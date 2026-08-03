#!/usr/bin/env python3
import sys, re, asyncio, aiohttp
from urllib.parse import urlparse

async def check(session, url):
    try:
        async with session.get(url, timeout=5) as resp:
            return url, resp.status
    except:
        return url, 0

async def main():
    dosya_adi = "README.md"
    with open(dosya_adi, encoding="utf-8") as f:
        metin = f.read()
    
    bulunan_linkler = re.findall(r'https?://[^\s\)]+', metin)
    print(f"🔍 {len(bulunan_linkler)} link bulundu, kontrol ediliyor...")
    
    async with aiohttp.ClientSession() as session:
        gorevler = [check(session, link) for link in set(bulunan_linkler)]
        sonuclar = await asyncio.gather(*gorevler)
    
    calisan = [s for s in sonuclar if s[1] == 200]
    kirik = [s for s in sonuclar if s[1] != 200]
    
    print(f"\n✅ Çalışan: {len(calisan)} | ❌ Kırık: {len(kirik)}")
    for url, durum in kirik:
        print(f"   ✗ {durum} - {url}")

if __name__ == "__main__":
    asyncio.run(main())
