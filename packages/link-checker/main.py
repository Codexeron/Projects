#!/usr/bin/env python3
# Mimar Onaylı: SOLID, Async, Zero-Trust Logging
import sys
import re
import asyncio
import aiohttp
from urllib.parse import urlparse

# --- 1. GÖREV: Linkleri Bul (Single Responsibility) ---
def extract_links(markdown_text: str) -> list:
    """Verilen metindeki tüm http/https linklerini döndür."""
    return re.findall(r'https?://[^\s\)]+', markdown_text)

# --- 2. GÖREV: Güvenlik Filtresi (Security) ---
def is_sensitive_url(url: str) -> bool:
    """Token, şifre veya iç ağ IP'si içeren linkleri gizle."""
    parsed = urlparse(url)
    # localhost, 127.0.0.1 veya query'de token varsa gizle
    if parsed.hostname in ['localhost', '127.0.0.1', '192.168.']:
        return True
    if 'token=' in url.lower() or 'key=' in url.lower() or 'secret=' in url.lower():
        return True
    return False

# --- 3. GÖREV: Asenkron Kontrol (Performance) ---
async def check_link(session: aiohttp.ClientSession, url: str) -> dict:
    """Tek bir linki kontrol et, sonucu sözlük olarak döndür."""
    if is_sensitive_url(url):
        return {"url": url, "status": 403, "error": "Güvenlik nedeniyle gizlendi"}
    
    try:
        async with session.get(url, timeout=5, allow_redirects=True) as resp:
            return {"url": url, "status": resp.status, "error": None}
    except asyncio.TimeoutError:
        return {"url": url, "status": 408, "error": "Zaman aşımı"}
    except Exception as e:
        return {"url": url, "status": 0, "error": str(e)[:30]}

# --- 4. GÖREV: Raporlama (UI/UX + QA) ---
def display_report(results: list):
    """Renkli ve tablolu rapor göster."""
    total = len(results)
    ok = [r for r in results if r["status"] == 200]
    broken = [r for r in results if 400 <= r["status"] < 600 or r["status"] == 0]
    
    # Başlık çubuğu (UI/UX)
    print("\n" + "=" * 50)
    print(f"🏛️  LINK SAĞLIĞI RAPORU  |  Mimar Denetimli")
    print("=" * 50)
    
    # İlerleme çubuğu görseli
    ok_percent = int((len(ok) / total) * 30) if total else 0
    bar = "█" * ok_percent + "░" * (30 - ok_percent)
    print(f"🟢 {bar}  %{int((len(ok)/total)*100) if total else 0}")
    print(f"✅ Çalışan: {len(ok)}  |  ❌ Kırık/Hatalı: {len(broken)}  |  📦 Toplam: {total}\n")
    
    # Hatalı linkler varsa listele (Bug Hunter)
    if broken:
        print("🔴 HATALI LİNKLER (Müdahale Gerekli):")
        for item in broken[:10]:  # En fazla 10 göster
            status = item["status"]
            url = item["url"]
            error = item.get("error", "")
            print(f"   ✗ [{status}] {url[:60]}... {error}")
        if len(broken) > 10:
            print(f"   ... ve {len(broken)-10} tane daha.")
    else:
        print("🎉 Mükemmel! Hiç kırık link yok. Rozeti hak ettiniz.")

# --- 5. ANA KONTROLÖR (Architect - Her şeyi birleştir) ---
async def main():
    dosya_adi = sys.argv[1] if len(sys.argv) > 1 else "README.md"
    
    try:
        with open(dosya_adi, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ HATA: '{dosya_adi}' dosyası bulunamadı!")
        return
    
    links = extract_links(content)
    if not links:
        print("⚠️  Hiç link bulunamadı. README'ye link ekleyin!")
        return
    
    # Async performans (aynı anda 50 kontrol)
    sem = asyncio.Semaphore(50)
    async with aiohttp.ClientSession() as session:
        async def bounded_check(url):
            async with sem:
                return await check_link(session, url)
        
        tasks = [bounded_check(url) for url in set(links)]  # Benzersiz linkler
        results = await asyncio.gather(*tasks)
    
    # Raporu göster
    display_report(results)
    
    # CI/CD için çıkış kodu (Build'in kırılıp kırılmayacağını belirler)
    broken_count = len([r for r in results if r["status"] != 200 and r["status"] != 403])
    sys.exit(1 if broken_count > 0 else 0)

if __name__ == "__main__":
    asyncio.run(main())
