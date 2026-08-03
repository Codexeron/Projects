#!/usr/bin/env python3
# Mimar Onaylı v3.0 - CLI Desteği + Otomatik Yeniden Deneme (Retry)

import sys
import re
import asyncio
import aiohttp
import os
import glob
from urllib.parse import urlparse

# --- 1. YARDIMCI: Linkleri Bul ---
def extract_links(text: str) -> list:
    """Verilen metindeki tüm http/https linklerini döndür."""
    return re.findall(r'https?://[^\s\)]+', text)

# --- 2. GÜVENLİK: Hassas Linkleri Gizle ---
def is_sensitive_url(url: str) -> bool:
    """Token, şifre veya iç ağ IP'si içeren linkleri gizle."""
    parsed = urlparse(url)
    if parsed.hostname in ['localhost', '127.0.0.1', '192.168.']:
        return True
    if any(x in url.lower() for x in ['token=', 'key=', 'secret=', 'password=']):
        return True
    return False

# --- 3. PERFORMANS & DAYANIKLILIK: Tek linki dene (3 kez tekrarla) ---
async def check_link_with_retry(session: aiohttp.ClientSession, url: str, retries: int = 3) -> dict:
    """Linki kontrol eder, başarısız olursa 3 kez yeniden dener (Retry)."""
    if is_sensitive_url(url):
        return {"url": url, "status": 403, "error": "Gizli (Güvenlik)"}
    
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            async with session.get(url, timeout=5, allow_redirects=True) as resp:
                # Eğer başarılıysa (200-299) veya geçerli bir hata koduyse (404, 403 vs.) direk dön.
                if resp.status < 500 or resp.status == 404:
                    return {"url": url, "status": resp.status, "error": None}
                # 500 hatası (Sunucu hatası) ise tekrar dene.
                else:
                    last_error = f"HTTP {resp.status}"
                    if attempt < retries:
                        await asyncio.sleep(0.5 * attempt)  # Bekle ve tekrar dene
        except asyncio.TimeoutError:
            last_error = "Zaman aşımı (Timeout)"
            if attempt < retries:
                await asyncio.sleep(0.5 * attempt)
        except Exception as e:
            last_error = str(e)[:30]
            if attempt < retries:
                await asyncio.sleep(0.5 * attempt)
    
    # Tüm denemeler başarısız olduysa son hatayı döndür
    return {"url": url, "status": 0, "error": last_error}

# --- 4. DOSYA BULUCU: Klasör veya dosya yolunu işle (CLI) ---
def find_md_files(path: str) -> list:
    """Verilen path dosya ise onu, klasör ise içindeki tüm .md dosyalarını bulur."""
    if os.path.isfile(path):
        return [path]
    elif os.path.isdir(path):
        # recursive (alt klasörler dahil) tüm .md dosyalarını bul
        return glob.glob(os.path.join(path, "**/*.md"), recursive=True)
    else:
        print(f"⚠️ HATA: '{path}' geçerli bir dosya veya klasör değil!")
        return []

# --- 5. RAPORLAMA (UI/UX) ---
def display_report(results: list, file_count: int, scanned_path: str):
    """Renkli ve detaylı rapor."""
    total = len(results)
    ok = [r for r in results if r["status"] == 200]
    broken = [r for r in results if r["status"] not in [200, 403]]
    hidden = [r for r in results if r["status"] == 403]
    
    print("\n" + "=" * 60)
    print(f"🏛️  MİMAR LİNK DENETİMİ (CLI) | {file_count} dosya tarandı")
    print(f"📍 Hedef: {scanned_path}")
    print("=" * 60)
    
    if total == 0:
        print("⚠️ Hiç link bulunamadı.")
        return 0

    ok_pct = int((len(ok) / total) * 30) if total else 0
    bar = "█" * ok_pct + "░" * (30 - ok_pct)
    print(f"🟢 {bar}  %{int((len(ok)/total)*100) if total else 0}")
    print(f"✅ Çalışan: {len(ok)} | ❌ Kırık: {len(broken)} | 🔒 Gizli: {len(hidden)} | 📦 Toplam: {total}")
    
    if broken:
        print("\n🔴 ACİL MÜDAHALE GEREKENLER (Retry başarısız oldu):")
        for item in broken[:10]:
            print(f"   ✗ [{item['status']}] {item['url'][:65]}... {item.get('error','')}")
        if len(broken) > 10:
            print(f"   ... ve {len(broken)-10} tane daha.")
    else:
        print("\n🎉 Tüm linkler sapasağlam! Bravo Mimar.")
    
    return len(broken)

# --- 6. ANA KONTROLÖR ---
async def main():
    # CLI Argümanını oku (Örnek: python main.py docs/ veya python main.py README.md)
    target_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    print(f"📂 Hedef taranıyor: {target_path}")
    
    # Dosyaları bul
    md_files = find_md_files(target_path)
    if not md_files:
        print("⚠️ Hiç .md dosyası bulunamadı.")
        return
    
    print(f"📁 {len(md_files)} Markdown dosyası bulundu, taranıyor...")
    
    # Tüm dosyalardaki linkleri topla
    all_links = []
    for f in md_files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                all_links.extend(extract_links(file.read()))
        except Exception as e:
            print(f"   ⚠️ Dosya okunamadı: {f} ({e})")
    
    if not all_links:
        print("⚠️ Hiç link bulunamadı.")
        return
    
    # Benzersiz linkleri al (aynı linki defalarca kontrol etme)
    unique_links = list(set(all_links))
    print(f"🔗 {len(unique_links)} benzersiz link bulundu, kontrol ediliyor (Her biri için 3 deneme)...")
    
    # Eşzamanlı kontrol (Performans + Retry)
    sem = asyncio.Semaphore(30)  # 50'den 30'a düşürdüm ki retry'ler sistemi yormasın
    async with aiohttp.ClientSession() as session:
        async def bounded_check(url):
            async with sem:
                return await check_link_with_retry(session, url, retries=3)
        
        tasks = [bounded_check(url) for url in unique_links]
        results = await asyncio.gather(*tasks)
    
    # Raporla
    broken_count = display_report(results, len(md_files), target_path)
    
    # CI/CD'de başarısız olması için hata kodu döndür
    sys.exit(1 if broken_count > 0 else 0)

if __name__ == "__main__":
    asyncio.run(main())
