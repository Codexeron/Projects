#!/usr/bin/env python3
# Mimar Onaylı v2.0 - Tüm repo tarar
import sys, re, asyncio, aiohttp, glob
from urllib.parse import urlparse

def extract_links(text):
    """Tüm http/https linklerini bul."""
    return re.findall(r'https?://[^\s\)]+', text)

def is_sensitive_url(url):
    """Güvenlik: Token, localhost, özel IP'leri gizle."""
    parsed = urlparse(url)
    if parsed.hostname in ['localhost', '127.0.0.1', '192.168.']:
        return True
    if any(x in url.lower() for x in ['token=', 'key=', 'secret=', 'password=']):
        return True
    return False

async def check_link(session, url):
    """Tek bir linki kontrol et."""
    if is_sensitive_url(url):
        return {"url": url, "status": 403, "error": "Gizli (Güvenlik)"}
    try:
        async with session.get(url, timeout=5, allow_redirects=True) as resp:
            return {"url": url, "status": resp.status, "error": None}
    except asyncio.TimeoutError:
        return {"url": url, "status": 408, "error": "Zaman aşımı"}
    except Exception as e:
        return {"url": url, "status": 0, "error": str(e)[:30]}

def display_report(results, file_count):
    """Renkli ve detaylı rapor."""
    total = len(results)
    ok = [r for r in results if r["status"] == 200]
    broken = [r for r in results if r["status"] not in [200, 403]]
    hidden = [r for r in results if r["status"] == 403]
    
    print("\n" + "=" * 55)
    print(f"🏛️  MİMAR LİNK DENETİMİ | {file_count} dosya tarandı")
    print("=" * 55)
    
    ok_pct = int((len(ok)/total)*30) if total else 0
    bar = "█" * ok_pct + "░" * (30 - ok_pct)
    print(f"🟢 {bar}  %{int((len(ok)/total)*100) if total else 0}")
    print(f"✅ Çalışan: {len(ok)} | ❌ Kırık: {len(broken)} | 🔒 Gizli: {len(hidden)}")
    
    if broken:
        print("\n🔴 ACİL MÜDAHALE GEREKENLER:")
        for item in broken[:10]:
            print(f"   ✗ [{item['status']}] {item['url'][:65]}... {item.get('error','')}")
    else:
        print("\n🎉 Tüm linkler sapasağlam! Bravo Mimar.")
    return len(broken)

async def main():
    # Tüm .md dosyalarını tara (alt klasörler dahil)
    md_files = glob.glob("**/*.md", recursive=True)
    if not md_files:
        print("⚠️ Hiç .md dosyası bulunamadı.")
        return
    
    print(f"📁 {len(md_files)} Markdown dosyası taranıyor...")
    
    all_links = []
    for f in md_files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                all_links.extend(extract_links(file.read()))
        except:
            pass
    
    if not all_links:
        print("⚠️ Hiç link bulunamadı.")
        return
    
    # Eş zamanlı kontrol (Performans)
    sem = asyncio.Semaphore(50)
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(check_link(session, url)) for url in set(all_links)]
        results = await asyncio.gather(*tasks)
    
    broken_count = display_report(results, len(md_files))
    # CI/CD'de başarısız olması için hata kodu döndür
    sys.exit(1 if broken_count > 0 else 0)

if __name__ == "__main__":
    asyncio.run(main())
