#!/usr/bin/env python3
# Mimar Onaylı - .env Dedektifi (Güvenlik ve DevOps)

import os
import sys
from pathlib import Path

# --- 1. KRİTİK DEĞİŞKENLER (Security) ---
CRITICAL_VARS = [
    "SECRET_KEY",
    "API_KEY",
    "DATABASE_URL",
    "REDIS_URL",
    "JWT_SECRET",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "STRIPE_SECRET_KEY",
    "GITHUB_TOKEN",
    "SLACK_WEBHOOK_URL"
]

# --- 2. .env DOSYASINI BUL ve OKU ---
def find_env_file():
    """Proje kökünde .env dosyasını ara."""
    env_path = Path(".env")
    if env_path.exists():
        return env_path
    else:
        return None

def parse_env_file(env_path):
    """.env dosyasını oku, yorum satırlarını ve boşlukları temizle."""
    env_vars = {}
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        print(f"❌ .env dosyası okunamadı: {e}")
        return None
    return env_vars

# --- 3. RAPORLAMA (UI/UX + QA) ---
def display_report(env_vars):
    """Eksik ve boş değişkenleri raporla."""
    print("\n" + "=" * 60)
    print("🏛️  MİMAR .ENV DEDEKTİFİ | Güvenlik ve Konfigürasyon Kontrolü")
    print("=" * 60)

    if not env_vars:
        print("⚠️ .env dosyası boş veya geçersiz!")
        return 1

    # Kritik değişkenleri kontrol et
    missing = [var for var in CRITICAL_VARS if var not in env_vars]
    empty = [var for var in CRITICAL_VARS if var in env_vars and not env_vars[var]]

    # Tüm değişkenleri listele (gizleme yapmadan)
    print(f"📦 Toplam Değişken: {len(env_vars)}")
    print(f"🔑 Kritik Değişkenler: {len(CRITICAL_VARS)}")
    
    if missing:
        print("\n🔴 EKSİK KRİTİK DEĞİŞKENLER (Hemen ekleyin!):")
        for var in missing:
            print(f"   ✗ {var}")
    else:
        print("\n✅ Tüm kritik değişkenler mevcut.")

    if empty:
        print("\n⚠️ BOŞ KRİTİK DEĞİŞKENLER (Değer atayın!):")
        for var in empty:
            print(f"   ⚠️ {var} = (boş)")
    else:
        print("✅ Hiçbir kritik değişken boş değil.")

    # Öneri: Eksik veya boş varsa hata kodu döndür
    if missing or empty:
        print("\n💡 Öneri: .env dosyasını düzenleyin ve eksik/boş değişkenleri tamamlayın.")
        return 1
    else:
        print("\n🎉 .env dosyanız mükemmel! Her şey yerli yerinde.")
        return 0

# --- 4. ANA KONTROLÖR ---
def main():
    env_path = find_env_file()
    if not env_path:
        print("❌ .env dosyası bulunamadı! Proje kökünde '.env' dosyası oluşturun.")
        sys.exit(1)
    
    env_vars = parse_env_file(env_path)
    if env_vars is None:
        sys.exit(1)
    
    exit_code = display_report(env_vars)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
