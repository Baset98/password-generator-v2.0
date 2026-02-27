"""
dashboard.py
────────────
PassGen – Streamlit Password Generator Dashboard

Run with:
    streamlit run dashboard.py
"""

from __future__ import annotations

import json
from datetime import datetime

import streamlit as st
from nltk.corpus import words as nltk_words

from password_generators import (
    MemorablePasswordGenerator,
    PasswordGenerator,
    PinCodeGenerator,
    RandomPasswordGenerator,
    _ensure_nltk_words,
)

# ─────────────────────────────────────────────────────────────────────────────
# Page configuration  (must be the very first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="PassGen – Password Generator",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS – dark, modern, minimal
# ─────────────────────────────────────────────────────────────────────────────

def _inject_css() -> None:
    st.markdown(
        """
        <style>
        /* ── Global ── */
        [data-testid="stAppViewContainer"],
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        section.main { background-color: #060d1a !important; }

        /* ── Text ── */
        h1, h2, h3, h4, p, label, span, div, li, .stMarkdown {
            color: #e8f0fe !important;
        }

        /* ── Code blocks (password display) ── */
        code, .stCode pre {
            background-color: #0d1f3c !important;
            color: #67e8f9 !important;
            border: 1px solid rgba(103,232,249,0.25) !important;
            border-radius: 10px !important;
            font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
            font-size: 1.05rem !important;
            letter-spacing: 0.04em !important;
        }

        /* ── Buttons ── */
        .stButton > button {
            background: linear-gradient(135deg, #0ea5e9, #6366f1) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            letter-spacing: 0.04em !important;
            padding: 0.6rem 1.4rem !important;
            transition: transform 0.15s, box-shadow 0.15s !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 24px rgba(14,165,233,0.35) !important;
        }

        /* ── Sliders ── */
        .stSlider > div > div > div > div {
            background: linear-gradient(135deg, #0ea5e9, #6366f1) !important;
        }

        /* ── Progress bar (strength) ── */
        .stProgress > div > div > div > div {
            border-radius: 100px !important;
        }

        /* ── Expanders ── */
        .streamlit-expanderHeader {
            background-color: #0d1f3c !important;
            border-radius: 10px !important;
            border: 1px solid rgba(103,232,249,0.15) !important;
            font-weight: 600 !important;
        }
        .streamlit-expanderContent {
            background-color: #07121f !important;
            border: 1px solid rgba(103,232,249,0.1) !important;
            border-top: none !important;
            border-radius: 0 0 10px 10px !important;
        }

        /* ── Radio buttons ── */
        .stRadio > div { gap: 0.75rem !important; }
        .stRadio label { font-weight: 500 !important; }

        /* ── Checkboxes ── */
        .stCheckbox label { font-weight: 500 !important; }

        /* ── Metric cards ── */
        [data-testid="metric-container"] {
            background-color: #0d1f3c !important;
            border: 1px solid rgba(103,232,249,0.18) !important;
            border-radius: 12px !important;
            padding: 0.75rem 1rem !important;
        }
        [data-testid="metric-container"] label {
            font-size: 0.72rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.1em !important;
            color: #64748b !important;
        }
        [data-testid="stMetricValue"] {
            color: #67e8f9 !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-weight: 800 !important;
        }

        /* ── Download buttons ── */
        .stDownloadButton > button {
            background: #0d1f3c !important;
            color: #67e8f9 !important;
            border: 1px solid rgba(103,232,249,0.3) !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
        }
        .stDownloadButton > button:hover {
            border-color: #67e8f9 !important;
            transform: translateY(-1px) !important;
        }

        /* ── Divider ── */
        hr { border-color: rgba(103,232,249,0.12) !important; }

        /* ── Info / Success / Warning boxes ── */
        .stAlert { border-radius: 10px !important; }

        /* ── Scrollbar ── */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 3px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


_inject_css()

# ─────────────────────────────────────────────────────────────────────────────
# Session state initialisation
# ─────────────────────────────────────────────────────────────────────────────

DEFAULTS = {
    "generator":      None,
    "password":       None,
    "history":        [],
    "last_type":      None,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ─────────────────────────────────────────────────────────────────────────────
# NLTK word corpus (cached)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading word corpus…")
def load_word_list() -> list[str]:
    """Return a filtered list of clean English words for memorable passwords."""
    _ensure_nltk_words()
    return [
        w for w in nltk_words.words()
        if 4 <= len(w) <= 8 and w.isalpha() and w.islower()
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Strength helpers
# ─────────────────────────────────────────────────────────────────────────────

_STRENGTH_COLORS = {
    "Weak":        "#ef4444",
    "Medium":      "#f97316",
    "Strong":      "#facc15",
    "Very Strong": "#4ade80",
}

_STRENGTH_EMOJI = {
    "Weak":        "🔴",
    "Medium":      "🟠",
    "Strong":      "🟡",
    "Very Strong": "🟢",
}


def _render_strength(password: str) -> None:
    """Render animated strength bar + metrics below the password."""
    score, label = PasswordGenerator.compute_strength(password)
    color        = _STRENGTH_COLORS[label]
    emoji        = _STRENGTH_EMOJI[label]

    # Strength bar row
    col_label, col_bar = st.columns([1, 3])
    with col_label:
        st.markdown(
            f"<h4 style='color:{color};margin:0'>{emoji} {label}</h4>",
            unsafe_allow_html=True,
        )
    with col_bar:
        st.progress(score / 100)

    # Metric cards row
    cs  = PasswordGenerator.charset_size(password)
    ent = PasswordGenerator.entropy_bits(password)
    ct  = PasswordGenerator.crack_time_label(password)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Length",      len(password))
    m2.metric("Entropy",     f"{ent} bits")
    m3.metric("Charset",     cs)
    m4.metric("Crack Time",  ct)


# ─────────────────────────────────────────────────────────────────────────────
# Download helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_json_payload(password: str, pw_type: str) -> str:
    score, label = PasswordGenerator.compute_strength(password)
    cs           = PasswordGenerator.charset_size(password)
    ent          = PasswordGenerator.entropy_bits(password)
    ct           = PasswordGenerator.crack_time_label(password)
    return json.dumps(
        {
            "password":     password,
            "type":         pw_type,
            "strength":     {"score": score, "label": label},
            "length":       len(password),
            "charset_size": cs,
            "entropy_bits": ent,
            "crack_time":   ct,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "generator":    "PassGen v2.0 – github.com/Baset98/password-generator",
        },
        indent=2,
        ensure_ascii=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# ── Header ──
# ─────────────────────────────────────────────────────────────────────────────

try:
    st.image("./images/banner.jpeg", use_container_width=True)
except Exception:
    pass  # Banner image optional

st.title("🔐 PassGen — Password Generator")
st.caption(
    "Military-grade passwords, generated locally. "
    "Zero storage · Zero tracking · 100% private."
)
st.write("---")

# ─────────────────────────────────────────────────────────────────────────────
# ── Section 1 · Password Type Selector ──
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("① Select Password Type")

pw_type = st.radio(
    "Password Type",
    options=["🎲 Random Password", "🧠 Memorable Password", "🔢 PIN Code"],
    horizontal=True,
    label_visibility="collapsed",
)

# Reset password when type changes
if st.session_state.last_type != pw_type:
    st.session_state.password  = None
    st.session_state.generator = None
    st.session_state.last_type = pw_type

# ── Guide: type selector ──
with st.expander("📚 Guide: Which password type should I choose?"):
    st.markdown("""
### 🎯 Choosing the right type

Each password type is designed for a different use case:

---

#### 🎲 Random Password — Highest Security
- **Best for:** Email, banking, crypto wallets, social media — anywhere you use a **Password Manager**.
- **How it works:** Mixes uppercase, lowercase, digits, and symbols with zero pattern.
- **Security:** A 16-character random password with all types has ~10²⁸ combinations.
  Even a nation-state-level GPU cluster would need **billions of years** to crack it.

---

#### 🧠 Memorable Password — XKCD Method
- **Best for:** Passwords you **must memorise** — PC login, phone unlock, Wi-Fi.
- **Based on:** The famous [XKCD #936](https://xkcd.com/936/) comic.
- **Logic:** Four random words like `Correct-Horse-Battery-Staple` are far easier to remember
  than `x9#mP2qL` yet exponentially more secure because of their **combined length**.
- **Security:** Every additional word multiplies the search space by the vocabulary size (~170,000).

---

#### 🔢 PIN Code — Numbers Only
- **Best for:** Bank cards, phone lock screens, digital safes that **only accept digits**.
- **Best practice:** Use 6+ digits. Enable *Avoid Sequential Digits* to prevent patterns like `1234` or `0000`.

---

> ⚠️ **Never reuse passwords across accounts.** A single breach can compromise everything.
    """)

st.write("---")

# ─────────────────────────────────────────────────────────────────────────────
# ── Section 2 · Configuration ──
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("② Configure Options")

_type_key = pw_type.split()[1].lower()  # "random" | "memorable" | "pin"

if _type_key == "random":
    # ── Random ────────────────────────────────────────────────
    length = st.slider("Password Length", min_value=5, max_value=64, value=16)

    st.write("**Character Types**")
    c1, c2 = st.columns(2)
    with c1:
        inc_upper  = st.checkbox("Uppercase  (A–Z)", value=True,  key="r_upper")
        inc_digits = st.checkbox("Numbers   (0–9)", value=True,  key="r_digits")
    with c2:
        inc_lower  = st.checkbox("Lowercase  (a–z)", value=True,  key="r_lower")
        inc_symbols = st.checkbox("Symbols   (!@#$)", value=False, key="r_symbols")

    exc_similar = st.checkbox(
        "Exclude similar-looking characters  (O, 0, l, I, 1)",
        value=False, key="r_exc_sim",
    )
    no_repeat = st.toggle("No Repeated Characters", value=False, key="r_no_rep")
    use_crypto = st.toggle(
        "Cryptographically Secure  (crypto.secrets)",
        value=True, key="r_crypto",
        help="Uses Python's `secrets` module backed by the OS entropy pool.",
    )

    if not (inc_upper or inc_lower or inc_digits or inc_symbols):
        st.warning("⚠️ Please select at least one character type.")
        st.session_state.generator = None
    else:
        st.session_state.generator = RandomPasswordGenerator(
            length=length,
            include_uppercase=inc_upper,
            include_lowercase=inc_lower,
            include_digits=inc_digits,
            include_symbols=inc_symbols,
            exclude_similar=exc_similar,
            no_repeated_characters=no_repeat,
            use_secrets=use_crypto,
        )

elif _type_key == "memorable":
    # ── Memorable ─────────────────────────────────────────────
    no_of_words = st.slider("Number of Words", min_value=2, max_value=8, value=4)
    c1, c2 = st.columns(2)
    with c1:
        separator  = st.text_input("Separator", value="-", max_chars=3, key="m_sep")
        capitalize = st.checkbox("Capitalize Words", value=True, key="m_cap")
    with c2:
        suffix_len = st.number_input("Numeric Suffix Length", min_value=0, max_value=6, value=2, key="m_suf")

    word_list = load_word_list()
    st.session_state.generator = MemorablePasswordGenerator(
        no_of_words=no_of_words,
        separator=separator or "-",
        capitalization=capitalize,
        vocabulary=word_list,
        suffix_length=int(suffix_len),
    )

else:
    # ── PIN ───────────────────────────────────────────────────
    pin_length    = st.slider("PIN Length", min_value=4, max_value=12, value=6)
    avoid_seq     = st.checkbox("Avoid Sequential Digits  (e.g. 1234, 0000)", value=False, key="p_seq")
    st.session_state.generator = PinCodeGenerator(
        length=pin_length, avoid_sequential=avoid_seq
    )

# ── Guide: configuration ──
with st.expander("⚙️ Guide: Configuration options explained"):
    st.markdown("""
### 📏 Password Length

The single most impactful factor in password security.
Every additional character **multiplies** the combinations by the charset size.

| Length | Typical Use |
|--------|-------------|
| 8 chars | Minimum — avoid for sensitive accounts |
| 12–16 chars | Good balance for most accounts |
| 20+ chars | Recommended for high-value accounts |

---

### 🔤 Character Types

| Type | Pool Size | Notes |
|------|-----------|-------|
| Uppercase A–Z | +26 | Always enable unless the site rejects uppercase |
| Lowercase a–z | +26 | The baseline; always enable |
| Numbers 0–9 | +10 | Most sites require at least one digit |
| Symbols !@#$ | +32 | Biggest security boost; check site compatibility |

---

### 👁️ Exclude Similar Characters

Removes visually ambiguous chars: `O` vs `0`, `l` vs `I` vs `1`.  
Useful when you need to read or type the password manually.

---

### 🔁 No Repeated Characters

Guarantees character diversity (like drawing cards without replacement).  
Requires: **charset size ≥ password length**.

---

### 🔐 Cryptographically Secure (`secrets` module)

Python's `secrets` module reads from the OS entropy pool (`/dev/urandom` on Linux/macOS,
`CryptGenRandom` on Windows) — the same source used by TLS, SSH key generation, and
token minting. **Always keep this on** unless you have a specific reason not to.
    """)

st.write("---")

# ─────────────────────────────────────────────────────────────────────────────
# ── Section 3 · Generate ──
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("③ Generate Your Password")

# Auto-generate on first load
if st.session_state.password is None and st.session_state.generator is not None:
    try:
        st.session_state.password = st.session_state.generator.generate()
        st.session_state.history.append(st.session_state.password)
    except ValueError:
        pass

# Generate button
if st.button("⚡ Generate New Password", type="primary", use_container_width=True):
    if st.session_state.generator is None:
        st.error("❌ Please fix the configuration above before generating.")
    else:
        try:
            pw = st.session_state.generator.generate()
            st.session_state.password = pw
            st.session_state.history.append(pw)
            st.rerun()
        except ValueError as exc:
            st.error(f"❌ {exc}")

st.write("---")

# ─────────────────────────────────────────────────────────────────────────────
# ── Section 4 · Password Display & Strength ──
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.password:
    pw = st.session_state.password

    st.subheader("④ Your Password")
    st.code(pw, language=None)

    _render_strength(pw)

    # ── Guide: strength stats ──
    with st.expander("📊 Guide: How to read the security stats"):
        st.markdown("""
### 📏 Length
Total number of characters. Every extra character raises security **exponentially**.

---

### 🔬 Entropy (bits)
Measured as: **H = length × log₂(charset size)**

| Entropy | Assessment |
|---------|------------|
| < 40 bits | Easily crackable in minutes |
| 40–60 bits | Crackable with dedicated hardware |
| 60–80 bits | Very strong for most uses |
| **80+ bits** | **Practically uncrackable** ✅ |

---

### 🔤 Charset Size
How many unique characters are available in the pool your password draws from.
More character types → larger pool → stronger password.

---

### ⏱️ Crack Time
Estimated brute-force time at **10 billion guesses/second** (modern GPU cluster).
Real attacks are often slower; this is the worst case.

---

### 🎨 Strength Levels

| Level | Score | Colour |
|-------|-------|--------|
| Weak | 0–39 | 🔴 Red |
| Medium | 40–59 | 🟠 Orange |
| Strong | 60–79 | 🟡 Yellow |
| Very Strong | 80–100 | 🟢 Green |
        """)

    st.write("---")

# ─────────────────────────────────────────────────────────────────────────────
# ── Section 5 · Download ──
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("⑤ Download Your Password")

with st.expander("⬇️ Export Options", expanded=bool(st.session_state.password)):
    if st.session_state.password:
        pw       = st.session_state.password
        pw_label = pw_type.replace("🎲 ", "").replace("🧠 ", "").replace("🔢 ", "")
        json_str = _build_json_payload(pw, pw_label)

        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                label="📄 Download as TXT",
                data=pw,
                file_name="password.txt",
                mime="text/plain",
                use_container_width=True,
                key="dl_txt",
            )
        with d2:
            st.download_button(
                label="📦 Download as JSON",
                data=json_str,
                file_name="password.json",
                mime="application/json",
                use_container_width=True,
                key="dl_json",
            )

    else:
        st.info("Generate a password first to enable downloads.")

    # ── Guide: export formats ──
    with st.expander("💾 Guide: Export formats explained"):
        st.markdown("""
### 📄 TXT Format
A plain text file containing **only the password**.

**Best for:** Pasting into a Password Manager, secure import workflows.

---

### 📦 JSON Format
A structured file with **full metadata**:

```json
{
  "password": "your-password-here",
  "type": "Random Password",
  "strength": { "score": 92, "label": "Very Strong" },
  "length": 16,
  "charset_size": 94,
  "entropy_bits": 105,
  "crack_time": "∞ (practically uncrackable)",
  "generated_at": "2025-01-01T12:00:00Z"
}
```

**Best for:** Audit logs, developer tooling, batch credential management.

> ⚠️ Delete the file after importing it into your Password Manager.
        """)

st.write("---")

# ─────────────────────────────────────────────────────────────────────────────
# ── Section 6 · Session History ──
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("⑥ Session History")

with st.expander(
    f"🕑 History  ({len(st.session_state.history)} passwords this session)",
    expanded=False,
):
    if not st.session_state.history:
        st.info("No passwords generated yet in this session.")
    else:
        # Show in reverse chronological order; newest first
        for idx, item in enumerate(reversed(st.session_state.history[-30:]), start=1):
            sc, lbl = PasswordGenerator.compute_strength(item)
            emoji   = _STRENGTH_EMOJI.get(lbl, "⚪")
            col_pw, col_badge = st.columns([5, 1])
            with col_pw:
                st.code(item, language=None)
            with col_badge:
                st.markdown(
                    f"<span style='font-size:0.75rem;color:{_STRENGTH_COLORS[lbl]}'>"
                    f"{emoji} {lbl}</span>",
                    unsafe_allow_html=True,
                )

        if st.button("🗑️ Clear History", key="clear_hist"):
            st.session_state.history = []
            st.rerun()

    # ── Guide: history & privacy ──
    with st.expander("🔒 Guide: Session History & Your Privacy"):
        st.markdown("""
### 📝 Session History
Tracks up to **30 recently generated passwords** in Streamlit's session state.

- Visible **only to you** in your current browser tab
- **Never sent** to any server
- **Automatically wiped** when you close or refresh the tab
- Manually cleared with the "Clear History" button

---

### 🛡️ Zero-Storage Architecture

| Property | Status |
|----------|--------|
| Server storage | ❌ None |
| Database | ❌ None |
| Cookies | ❌ None |
| Analytics/Tracking | ❌ None |
| Network after load | ❌ None |
| Works offline | ✅ Yes |

---

### ✅ Best Practices

- Use a **Password Manager** (Bitwarden, 1Password, KeePass) to store passwords safely.
- Enable **2FA / MFA** on all important accounts.
- Use a **unique password** for every single account.
- Avoid entering passwords on public computers or unsecured networks.
        """)

st.write("---")

# ─────────────────────────────────────────────────────────────────────────────
# ── Section 7 · Full Security Guide ──
# ─────────────────────────────────────────────────────────────────────────────

with st.expander("📖 Full Security Guide: Password Types, Privacy & Best Practices"):
    st.markdown("""
### 🛡️ Why Does Password Security Matter?

Using weak or reused passwords (like `123456` or `password`) is the **#1 cause** of account
breaches. This app helps you create passwords that mathematics makes practically unbreakable.

---

### ⚙️ Password Types in Detail

#### 1. 🎲 Random Password — Maximum Security
The **gold standard** for account security.

- **Usage:** Any account where you store credentials in a Password Manager.
- **Strength:** A 16-char password with all 4 character types has a charset of 94 symbols:
  `94^16 ≈ 5.7 × 10³¹` possible combinations.
- **Crack time:** Even at 10 trillion guesses/second, this would take **~180 billion years**.

#### 2. 🧠 Memorable Password — Human-Friendly
Based on the **XKCD method** (see [xkcd.com/936](https://xkcd.com/936/)).

- **Usage:** Passwords you must type from memory — OS login, device PIN, Wi-Fi.
- **Logic:** Humans remember **stories and images** better than random strings.
  `Correct-Horse-Battery-Staple` tells a story; `x9#mP2qL` does not.
- **Security:** With a ~170,000-word vocabulary and 4 words:
  `170,000^4 ≈ 8.4 × 10²⁰` combinations — stronger than most random 12-char passwords.

#### 3. 🔢 PIN Code — Numeric-Only
- **Usage:** Bank cards, ATMs, phone lock screens, digital safes.
- **Caution:** A 4-digit PIN has only 10,000 combinations — fine for devices with lockout,
  but never use a short PIN as an account password.

---

### 🔒 Privacy Architecture

```
Your Browser / Python Runtime
        │
        ▼
  ┌──────────────────┐
  │  Password Logic  │   ← secrets.choice() / secrets.SystemRandom()
  │  (100% local)    │      OS entropy pool: /dev/urandom (Linux/macOS)
  └──────────────────┘      CryptGenRandom  (Windows)
        │
        ▼
  Your screen only — never touches a network
```

**No data ever leaves your machine.**

---

### 📋 Password Manager Recommendations

| Manager | Free Tier | Open Source | Notes |
|---------|-----------|-------------|-------|
| Bitwarden | ✅ Generous | ✅ Yes | Best free option |
| KeePassXC | ✅ Fully free | ✅ Yes | Offline, no cloud |
| 1Password | ❌ Paid | ❌ No | Polished UX |
| Dashlane | Limited | ❌ No | Good UI |

> 🔑 A password manager + unique passwords for every site is the single most
> impactful security improvement most people can make.
    """)

# ─────────────────────────────────────────────────────────────────────────────
# ── Footer ──
# ─────────────────────────────────────────────────────────────────────────────

st.write("---")
st.caption(
    "PassGen v2.0 — Built with Python & Streamlit · "
    "Open Source · MIT License · "
    "[GitHub](https://github.com/Baset98/password-generator)"
)
