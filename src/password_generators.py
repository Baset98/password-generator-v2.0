"""
password_generators.py
──────────────────────
Core password generation classes for PassGen.

Classes:
    PasswordGenerator         – Abstract base class
    RandomPasswordGenerator   – Cryptographically-random string passwords
    MemorablePasswordGenerator– XKCD-style word-phrase passwords
    PinCodeGenerator          – Numeric PIN codes
"""

from __future__ import annotations

import random
import secrets
import string
from abc import ABC, abstractmethod
from typing import List, Optional

import nltk


# ─────────────────────────────────────────────────────────────────────────────
# NLTK bootstrap
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_nltk_words() -> None:
    """Download the NLTK 'words' corpus if it is not already present."""
    try:
        nltk.data.find("corpora/words")
    except LookupError:
        nltk.download("words", quiet=True)


_ensure_nltk_words()


# ─────────────────────────────────────────────────────────────────────────────
# Abstract base
# ─────────────────────────────────────────────────────────────────────────────

class PasswordGenerator(ABC):
    """Abstract base class that every generator must implement."""

    @abstractmethod
    def generate(self) -> str:
        """Return a freshly generated password string."""
        ...

    # ------------------------------------------------------------------
    # Shared utility: strength scoring
    # ------------------------------------------------------------------

    @staticmethod
    def compute_strength(password: str) -> tuple[int, str]:
        """
        Score a password on a 0–100 scale and return (score, label).

        Scoring breakdown
        -----------------
        Length score   : up to 40 points  – scales from 4 → 28+ characters
        Diversity score: up to 40 points  – how many of {upper, lower, digit, symbol} appear
        Complexity bonus: 0 / 10 / 20    – extra credit for mixing digits and/or symbols

        Labels
        ------
        0–39   Weak
        40–59  Medium
        60–79  Strong
        80–100 Very Strong
        """
        if not password:
            return 0, "Weak"

        length    = len(password)
        has_upper  = any(c.isupper()  for c in password)
        has_lower  = any(c.islower()  for c in password)
        has_digit  = any(c.isdigit()  for c in password)
        has_symbol = any(not c.isalnum() for c in password)

        # Length contribution (capped at 40 pts)
        length_score = min(max(length - 4, 0) / 24 * 40, 40)

        # Diversity contribution (each class = 10 pts, max 40)
        diversity_score = sum([has_upper, has_lower, has_digit, has_symbol]) / 4 * 40

        # Complexity bonus
        if has_digit and has_symbol:
            bonus = 20
        elif has_digit or has_symbol:
            bonus = 10
        else:
            bonus = 0

        score = int(min(100, round(length_score + diversity_score + bonus)))

        if score < 40:
            label = "Weak"
        elif score < 60:
            label = "Medium"
        elif score < 80:
            label = "Strong"
        else:
            label = "Very Strong"

        return score, label

    @staticmethod
    def charset_size(password: str) -> int:
        """Estimate the alphabet size used in *password*."""
        size = 0
        if any(c.isupper()  for c in password): size += 26
        if any(c.islower()  for c in password): size += 26
        if any(c.isdigit()  for c in password): size += 10
        if any(not c.isalnum() for c in password): size += 32
        return size or 10

    @staticmethod
    def entropy_bits(password: str) -> int:
        """Shannon entropy: H = length × log₂(charset_size)."""
        import math
        cs = PasswordGenerator.charset_size(password)
        return int(len(password) * math.log2(max(cs, 2)))

    @staticmethod
    def crack_time_label(password: str) -> str:
        """
        Estimate brute-force crack time at 10¹⁰ guesses/second.
        Returns a human-readable string.
        """
        import math
        cs   = PasswordGenerator.charset_size(password)
        secs = (cs ** len(password)) / 1e10
        if secs < 1:       return "< 1 second"
        if secs < 60:      return f"{int(secs)} seconds"
        if secs < 3_600:   return f"{int(secs/60)} minutes"
        if secs < 86_400:  return f"{int(secs/3_600)} hours"
        if secs < 3e7:     return f"{int(secs/86_400)} days"
        if secs < 3e9:     return f"{int(secs/3e7)} years"
        if secs < 3e12:    return f"{int(secs/3e9):,} thousand years"
        return "∞ (practically uncrackable)"


# ─────────────────────────────────────────────────────────────────────────────
# Random password
# ─────────────────────────────────────────────────────────────────────────────

class RandomPasswordGenerator(PasswordGenerator):
    """
    Generate a random password from a configurable character pool.

    Parameters
    ----------
    length : int
        Desired password length (default 16).
    include_uppercase : bool
        Include A–Z (default True).
    include_lowercase : bool
        Include a–z (default True).
    include_digits : bool
        Include 0–9 (default True).
    include_symbols : bool
        Include !@#$… (default False).
    exclude_similar : bool
        Strip look-alike chars O, 0, l, I, 1 (default False).
    no_repeated_characters : bool
        Each character may appear at most once (default False).
    use_secrets : bool
        Use the ``secrets`` module instead of ``random`` (default True).
        The ``secrets`` module uses the OS entropy pool and is
        cryptographically secure.
    """

    _SIMILAR: str = "O0lI1"

    def __init__(
        self,
        length: int = 16,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_digits: bool = True,
        include_symbols: bool = False,
        exclude_similar: bool = False,
        no_repeated_characters: bool = False,
        use_secrets: bool = True,
    ) -> None:
        self.length = length
        self.no_repeated_characters = no_repeated_characters
        self.use_secrets = use_secrets

        # Build character pool
        pool = ""
        if include_uppercase: pool += string.ascii_uppercase
        if include_lowercase: pool += string.ascii_lowercase
        if include_digits:    pool += string.digits
        if include_symbols:   pool += string.punctuation

        if exclude_similar:
            pool = "".join(ch for ch in pool if ch not in self._SIMILAR)

        self.pool: str = pool

    # ------------------------------------------------------------------

    def generate(self) -> str:
        if not self.pool:
            raise ValueError(
                "Character pool is empty. Please enable at least one character type."
            )

        if self.no_repeated_characters:
            if self.length > len(self.pool):
                raise ValueError(
                    f"Cannot generate {self.length} unique characters "
                    f"from a pool of only {len(self.pool)}. "
                    "Reduce length or enable more character types."
                )
            # Fisher-Yates shuffle on a copy, then slice
            pool_list = list(self.pool)
            if self.use_secrets:
                # secrets.SystemRandom for shuffle
                rng = secrets.SystemRandom()
                rng.shuffle(pool_list)
            else:
                random.shuffle(pool_list)
            return "".join(pool_list[: self.length])

        if self.use_secrets:
            return "".join(secrets.choice(self.pool) for _ in range(self.length))
        return "".join(random.choice(self.pool) for _ in range(self.length))


# ─────────────────────────────────────────────────────────────────────────────
# Memorable (XKCD) password
# ─────────────────────────────────────────────────────────────────────────────

class MemorablePasswordGenerator(PasswordGenerator):
    """
    Generate a passphrase by concatenating random English words
    (the XKCD #936 method).

    Parameters
    ----------
    no_of_words : int
        Number of words to combine (default 4).
    separator : str
        String placed between words (default ``"-"``).
    capitalization : bool
        Capitalise the first letter of each word (default True).
    vocabulary : list[str] | None
        Custom word list; falls back to NLTK 'words' corpus.
    suffix_length : int
        Number of random digits appended after the phrase (default 0).
    """

    _WORD_MIN_LEN: int = 4
    _WORD_MAX_LEN: int = 8

    def __init__(
        self,
        no_of_words: int = 4,
        separator: str = "-",
        capitalization: bool = True,
        vocabulary: Optional[List[str]] = None,
        suffix_length: int = 0,
    ) -> None:
        self.no_of_words   = no_of_words
        self.separator     = separator
        self.capitalization = capitalization
        self.suffix_length = max(0, int(suffix_length))

        if vocabulary is not None:
            self.vocabulary = vocabulary
        else:
            _ensure_nltk_words()
            raw = nltk.corpus.words.words()
            # Keep only simple, common-looking words in the target length range
            self.vocabulary = [
                w for w in raw
                if self._WORD_MIN_LEN <= len(w) <= self._WORD_MAX_LEN
                and w.isalpha()
                and w.islower()
            ]

        if len(self.vocabulary) < self.no_of_words:
            raise ValueError(
                f"Vocabulary too small ({len(self.vocabulary)} words) "
                f"to pick {self.no_of_words} unique words."
            )

    # ------------------------------------------------------------------

    def generate(self) -> str:
        chosen = secrets.SystemRandom().sample(self.vocabulary, self.no_of_words)

        if self.capitalization:
            chosen = [w.capitalize() for w in chosen]

        phrase = self.separator.join(chosen)

        if self.suffix_length > 0:
            suffix = "".join(str(secrets.randbelow(10)) for _ in range(self.suffix_length))
            phrase += suffix

        return phrase


# ─────────────────────────────────────────────────────────────────────────────
# PIN code
# ─────────────────────────────────────────────────────────────────────────────

class PinCodeGenerator(PasswordGenerator):
    """
    Generate a numeric PIN code.

    Parameters
    ----------
    length : int
        Number of digits (default 6).
    avoid_sequential : bool
        Reject pins where every consecutive pair is sequential
        (e.g. 1234, 9876) or all digits are identical (e.g. 0000).
        (default False)
    """

    def __init__(self, length: int = 6, avoid_sequential: bool = False) -> None:
        if length < 1:
            raise ValueError("PIN length must be at least 1.")
        self.length = length
        self.avoid_sequential = avoid_sequential

    # ------------------------------------------------------------------

    def generate(self) -> str:
        for _ in range(1_000):   # safety cap on retries
            pin = "".join(str(secrets.randbelow(10)) for _ in range(self.length))
            if not self.avoid_sequential or not self._is_weak(pin):
                return pin
        # Fallback – return whatever was last generated
        return pin  # type: ignore[return-value]

    # ------------------------------------------------------------------

    @staticmethod
    def _is_weak(pin: str) -> bool:
        """Return True if the PIN is obviously weak (sequential or all-same)."""
        digits = [int(d) for d in pin]
        # All identical
        if len(set(digits)) == 1:
            return True
        # Strictly ascending sequential
        if all(digits[i + 1] - digits[i] == 1 for i in range(len(digits) - 1)):
            return True
        # Strictly descending sequential
        if all(digits[i] - digits[i + 1] == 1 for i in range(len(digits) - 1)):
            return True
        return False
