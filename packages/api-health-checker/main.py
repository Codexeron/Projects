#!/usr/bin/env python3
# Mimar Onaylı - API Health Checker (Canlılık Dedektifi)

import sys
import asyncio
import aiohttp
import time
from urllib.parse import urlparse

# --- 1. RENKLİ TERMINAL (UI/UX) ---
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# --- 2. GÜVENLİK: API Key gizleme (Security) ---
def mask_sensitive_url(url: str) -> str:
    """URL içindeki api_key, token gibi bilgileri gizler."""
    from urllib.parse import urlparse, parse_qs, urlunparse
    parsed = urlparse(url)
    if parsed.query:
        query_params = parse_qs(parsed.query)
        masked_params = {}
        for key, value in query_params.items():
            if key.lower() in ['apikey', 'api_key', 'key', 'token', 'secret', 'password']:
                masked_params[key] = ['***GIZLI***']
            else:
                masked_params[key] = value
        # Sorguyu yeniden oluştur
        new_query = '&'.join([f"{k}={v[0]}" for k, v in masked_params.items()])
        parsed = parsed._replace(query=new_query)
        return urlunparse(parsed)
    return url

# --- 3. PERFORMANS & DAYANIKLILIK: Tek API'yi kontrol et (Retry) ---
async def check_api(session: aiohttp.ClientSession, url: str, retries: int = 2) -> dict:
    """Bir API adresine GET isteği atar, süreyi ve durumu ölçer."""
    masked_url = mask_sensitive_url(url)
    start_time = time.time()
    
    for attempt in range(1, retries + 2):  # retries + ilk deneme
        try:
            async with session.get(url, timeout=5) as resp:
                elapsed = round((time.time() - start_time) * 1000, 2)  # ms cinsinden
                status = resp.status
                if 200 <= status < 400:
                    return {"url": masked_url, "status": status, "time": elapsed, "error": None}
                else:
                    # 5xx sunucu hatası ise tekrar dene
                    if status >= 500 and attempt <= retries:
                        await asyncio.sleep(0.5 * attempt)
                        continue
                    return {"url": masked_url, "status": status, "time": elapsed, "error": f"HTTP {status}"}
        except asyncio.TimeoutError:
            if attempt <= retries:
                await asyncio.sleep(0.5 * attempt)
                continue
            return {"url": masked_url, "status": 408, "time": 5000, "error": "Timeout"}
        except Exception as e:
            if attempt <= retries:
                await asyncio.sleep(0.5 * attempt)
                continue
            return {"url": masked_url, "status": 0, "time": 0, "error": str(e)[:30]}

# --- 4. KAYNAK BULUCU: URL mi, Dosya mı? (CLI) ---
def load_targets(arg: str) -> list:
    """Argümanı kontrol eder: URL ise direkt listeye ekler, dosya ise okur."""
    if arg.startswith(('http://', 'https://')):
        return [arg]
    else:
        # Dosya olarak dene
        try:
            with open(arg, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
                # Boş satırları ve yorumları (# ile başlayan) filtrele
                urls = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
                return urls
        except FileNotFoundError:
            print(f"{Colors.RED}❌ Dosya bulunamadı: {arg}{Colors.RESET}")
            return []
        except Exception as e:
            print(f"{Colors.RED}❌ Dosya okunamadı: {e}{Colors.RESET}")
            return []

# --- 5. RAPORLAMA (UI/UX + QA) ---
def display_report(results: list, source: str):
    """Güzel, renkli ve tablolu rapor."""
    total = len(results)
    if total == 0:
        print("⚠️ Hiçbir API adresi kontrol edilemedi.")
        return 0

    success = [r for r in results if 200 <= r["status"] < 400]
    failed = [r for r in results if r["status"] not in range(200, 400)]
    avg_time = round(sum(r["time"] for r in results) / total, 2) if total else 0

    print("\n" + "=" * 60)
    print(f"{Colors.BOLD}🏛️  MİMAR API HEALTH CHECKER{Colors.RESET}")
    print(f"📡 Kaynak: {source}")
    print("=" * 60)

    # Özet Çubuğu
    pct = int((len(success) / total) * 30) if total else 0
    bar = "█" * pct + "░" * (30 - pct)
    print(f"{Colors.GREEN}🟢 {bar}  %{int((len(success)/total)*100) if total else 0}{Colors.RESET}")
    print(f"{Colors.GREEN}✅ Canlı: {len(success)}{Colors.RESET} | {Colors.RED}❌ Hatalı: {len(failed)}{Colors.RESET} | 📦 Toplam: {total}")
    print(f"⏱️  Ortalama Yanıt Süresi: {avg_time} ms")

    if failed:
        print("\n" + f"{Colors.RED}🔴 HATALI API'LER (Müdahale Gerekli):{Colors.RESET}")
        for item in failed[:10]:
            status_icon = f"[{item['status']}]"
            time_str = f"{item['time']}ms" if item['time'] > 0 else "N/A"
            error = item.get('error', 'Bilinmeyen Hata')
            print(f"   {Colors.RED}✗{Colors.RESET} {status_icon} {item['url']} ({time_str}) - {error}")
        if len(failed) > 10:
            print(f"   ... ve {len(failed)-10} tane daha.")
    else:
        print(f"\n{Colors.GREEN}🎉 Tüm API'ler sapasağlam! Bravo Mimar.{Colors.RESET}")

    return len(failed)

# --- 6. ANA KONTROLÖR ---
async def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not arg:
        print(f"{Colors.YELLOW}⚠️ Kullanım: python main.py <api_url> veya <dosya.txt>{Colors.RESET}")
        print("   Örnek: python main.py https://api.github.com/zen")
        print("   Örnek: python main.py urls.txt")
        return

    print(f"{Colors.BLUE}🔍 Hedef taranıyor: {arg}{Colors.RESET}")
    
    targets = load_targets(arg)
    if not targets:
        return

    print(f"📡 {len(targets)} API adresi tespit edildi, kontrol ediliyor...")

    # Eşzamanlı kontrol (30 paralel)
    sem = asyncio.Semaphore(30)
    async with aiohttp.ClientSession() as session:
        async def bounded_check(url):
            async with sem:
                return await check_api(session, url)
        tasks = [bounded_check(url) for url in targets]
        results = await asyncio.gather(*tasks)

    # Raporu göster
    failed_count = display_report(results, arg)
    sys.exit(1 if failed_count > 0 else 0)

if __name__ == "__main__":
    asyncio.run(main())
