# 🏛️ Projects · Zero-Compromise Monorepo

[![Python Version](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![CI Status](https://github.com/Codexeron/Projects/actions/workflows/ci.yml/badge.svg)](https://github.com/Codexeron/Projects/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Motto:** If it's not secure, fast, and clean, it doesn't belong here.  
> Bu repo; Güvenlik, Performans ve Temiz Kod prensiplerini bir arada sunduğum mühendislik laboratuvarımdır.

---

## 📂 Proje Yapısı

```text
Projects/
├── .github/workflows/ci.yml       # Otomatik test (CI/CD)
├── packages/
│   ├── link-checker/main.py       # Modül 1: Link Denetleyici
│   ├── env-checker/main.py        # Modül 2: .env Güvenlik Dedektifi
│   └── api-health-checker/main.py # Modül 3: API Canlılık Dedektifi
├── tests/test_main.py             # Test iskeleti
├── Makefile                       # Tek komutla çalıştır
├── requirements.txt               # Bağımlılıklar
└── README.md
