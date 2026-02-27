<div align="center">

<img src="./images/banner.jpeg" width="800" alt="PassGen Banner"/>

# 🔐 PassGen — Password Generator

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.45-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![NLTK](https://img.shields.io/badge/NLTK-3.9-green?style=for-the-badge)](https://www.nltk.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-4ade80?style=for-the-badge)](LICENSE)
[![Code Style: PEP8](https://img.shields.io/badge/Code%20Style-PEP%208-0ea5e9?style=for-the-badge)](https://pep8.org/)

<p align="center">
  <b>A lightning-fast, privacy-first Streamlit app for generating military-grade passwords.</b><br/>
  Random · Memorable · PIN — all generated locally with zero storage, zero tracking.
</p>

<img src="./images/streamlit-dashboard.jpeg" width="800" alt="PassGen Dashboard Screenshot"/>

</div>

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎲 **Random Password** | Cryptographically secure via Python's `secrets` module — uppercase, lowercase, digits, symbols |
| 🧠 **Memorable Password** | XKCD-style word phrases using the full NLTK English corpus |
| 🔢 **PIN Code** | Secure numeric codes with optional sequential-pattern avoidance |
| 📊 **Strength Evaluation** | Real-time score (0–100) with entropy bits, charset size, and crack-time estimate |
| 💾 **Export** | Download as plain `.txt` or structured `.json` with full metadata |
| 🕑 **Session History** | Auto-tracks the last 30 passwords; cleared on refresh |
| 📚 **Inline Guides** | Every section has a collapsible explanation — no documentation needed |
| 🌑 **Dark UI** | Modern dark interface with gradient accents |
| 🔒 **100% Private** | All generation happens in Python — nothing ever leaves your machine |

---

## 🚀 Quick Start

### Prerequisites

- Python **3.9+** (3.12 recommended)
- `pip` package manager

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Baset98/password-generator.git
cd password-generator/src

# 2. (Recommended) Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download the NLTK word corpus (one-time setup)
python -c "import nltk; nltk.download('words')"

# 5. Launch the app
streamlit run dashboard.py
or
reamlit run src/dashboard.py
```

The app opens automatically at **http://localhost:8501**.

---

## 📁 Project Structure

```
src/
├── dashboard.py               # Main Streamlit application
├── password_generators.py     # Password generation classes (OOP, fully typed)
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── images/
    ├── banner.jpeg            # Application header banner
    └── streamlit-dashboard.jpeg # Dashboard screenshot
```

---

## 🔧 Core Components

### `password_generators.py` — Class Architecture

```
PasswordGenerator  (Abstract Base Class)
│
├── compute_strength(password)  → (score: int, label: str)
├── charset_size(password)      → int
├── entropy_bits(password)      → int
└── crack_time_label(password)  → str
     │
     ├── RandomPasswordGenerator
     │     length, include_uppercase/lowercase/digits/symbols
     │     exclude_similar, no_repeated_characters, use_secrets
     │
     ├── MemorablePasswordGenerator
     │     no_of_words, separator, capitalization
     │     vocabulary (NLTK), suffix_length
     │
     └── PinCodeGenerator
           length, avoid_sequential
```

| Class | Key Method | Randomness Source |
|-------|-----------|-------------------|
| `RandomPasswordGenerator` | `generate() → str` | `secrets.choice()` |
| `MemorablePasswordGenerator` | `generate() → str` | `secrets.SystemRandom().sample()` |
| `PinCodeGenerator` | `generate() → str` | `secrets.randbelow(10)` |

### `dashboard.py` — Section Map

| Section | Content |
|---------|---------|
| ① Select Type | Radio tabs + inline guide |
| ② Configure | Type-specific sliders, checkboxes, toggles + guide |
| ③ Generate | Primary action button |
| ④ Display | Password code block · strength bar · 4 metric cards |
| ⑤ Download | TXT and JSON export buttons + format guide |
| ⑥ History | Last 30 passwords with strength badges |
| Guide | Full security reference (always accessible) |

---

## 🛡️ Security & Privacy

### Strength Scoring Algorithm

```
score = length_score + diversity_score + complexity_bonus

length_score     = min( max(length - 4, 0) / 24 × 40,  40 )   # 0–40 pts
diversity_score  = (char_classes_used / 4) × 40                 # 0–40 pts
complexity_bonus = 20 if digits AND symbols                      # 0–20 pts
                   10 if digits OR symbols
                    0 otherwise

Thresholds:  0–39 Weak · 40–59 Medium · 60–79 Strong · 80–100 Very Strong
```

### Entropy Formula

```
H = length × log₂(charset_size)   (bits)

Examples:
  16 chars, all types  (charset=94)  →  16 × 6.55 ≈ 105 bits  ✅
  12 chars, lower+digit(charset=36)  →  12 × 5.17 ≈  62 bits
   4 words, ~170k vocab              →   4 × 17.4 ≈  70 bits  ✅
```

### Privacy Guarantee

```
Your Machine
    │
    ▼
┌───────────────────────────────────────────┐
│  Python Runtime (Streamlit)               │
│                                           │
│  secrets.choice()                         │
│   └── OS entropy pool                     │
│        ├── /dev/urandom   (Linux/macOS)   │
│        └── CryptGenRandom (Windows)       │
│                                           │
│  ❌ No network calls                      │
│  ❌ No database writes                    │
│  ❌ No cookies / analytics               │
│  ✅ Session memory only                   │
└───────────────────────────────────────────┘
```

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| [`streamlit`](https://streamlit.io/) | 1.45.x | Interactive web UI framework |
| [`nltk`](https://www.nltk.org/) | 3.9.x | English word corpus for memorable passwords |

**Standard library used:** `abc`, `json`, `math`, `random`, `secrets`, `string`, `datetime`

---

## 📖 How to Use

1. **Select Type** — Choose Random, Memorable, or PIN from the radio buttons.
2. **Configure** — Adjust length, character types, separators, or other options.
3. **Generate** — Click *⚡ Generate New Password*. The password appears instantly with its strength analysis.
4. **Evaluate** — Read the strength score, entropy in bits, charset size, and estimated crack time.
5. **Download** — Save as `.txt` (password only) or `.json` (with full metadata).
6. **Explore Guides** — Every section has a collapsible guide. Expand them to learn more.

---

## 🤝 Contributing

Contributions are welcome!

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/password-generator.git
cd password-generator

git checkout -b feature/your-feature-name
# ... make your changes ...
git commit -m "feat: describe your change"
git push origin feature/your-feature-name
# Open a Pull Request
```

**Guidelines:**
- Follow [PEP 8](https://pep8.org/) style.
- Add type hints to all new functions.
- Add docstrings to all new classes and methods.
- Test your changes locally before submitting.

**Ideas welcome:**
- 🌍 Additional language word lists (Arabic, Persian, French…)
- 🔑 Passphrase strength presets (NIST levels)
- 📊 Strength history chart
- 🌐 Deploy to Streamlit Cloud

---

## 📄 License

```
MIT License  ©  2025  Baset98

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, subject to the above copyright notice
appearing in all copies.
```

---

<div align="center">

**Built with ❤️ using Python & Streamlit**

[⭐ Star this repo](https://github.com/Baset98/password-generator) · 
[🐛 Report a bug](https://github.com/Baset98/password-generator/issues) · 
[💡 Request a feature](https://github.com/Baset98/password-generator/issues)

</div>
