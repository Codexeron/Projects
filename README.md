# 🏛️ Projects · Zero-Compromise Monorepo

[![Python Version](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![CI Status](https://github.com/Codexeron/Projects/actions/workflows/ci.yml/badge.svg)](https://github.com/Codexeron/Projects/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **Motto:** If it's not secure, fast, and clean, it doesn't belong here.  
> Bu repo; Güvenlik, Performans ve Temiz Kod prensiplerini bir arada sunduğum mühendislik laboratuvarımdır.

---

## 📂 Proje Yapısı (Şema)

```text
Projects/
├── .github/
│   └── workflows/
│       └── ci.yml          # Otomatik test pipeline'ı
├── packages/
│   └── link-checker/
│       └── main.py         # Ana modül (asenkron link denetleyici)
├── tests/
│   └── test_main.py        # QA test iskeleti
├── .gitignore
├── Makefile                # Tek komutla çalıştır (make check)
├── pyproject.toml          # Modern Python paket bilgisi
├── requirements.txt        # Bağımlılıklar
└── README.md               # Bu dosya (açıklama ve rehber)
