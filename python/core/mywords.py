"""The learner's own words: add one, paste a whole list, remove, quiz.

Own words live in MistakeMemory (so they're saved with everything else) and are
mirrored into ``BANK.mine`` so the flip cards and the quiz can use them.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .memory import MistakeMemory
from .vocab import Spelling, VocabularyBank, Word


@dataclass
class BulkResult:
    """What came out of a pasted list."""

    words: list[dict] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)   # (line, reason)


class BulkWordParser:
    """Parses pasted lists, one word per line, e.g.::

        el perro = dog
        la casa - house
        gato: cat (m)
        las gafas, glasses
        (f) nube	cloud
    """

    # Tried in order; the first one present splits the line once.
    SEPARATORS = ("\t", "=", "–", "—", " - ", ":", "-", ",")
    ARTICLES = {"el": ("m", False), "la": ("f", False), "los": ("m", True), "las": ("f", True),
                "un": ("m", False), "una": ("f", False), "unos": ("m", True), "unas": ("f", True)}
    TAGS = {"m": ("m", False), "f": ("f", False), "mpl": ("m", True), "fpl": ("f", True)}
    TAG_RE = re.compile(r"\(\s*(m|f|mpl|fpl)\s*\)", re.IGNORECASE)
    MAX_ES, MAX_EN = 60, 80

    @classmethod
    def split_article(cls, es: str) -> tuple[str, str | None, bool]:
        """'el agua' -> ('agua', 'f', False): stressed a- words are feminine despite 'el'."""
        parts = es.split(None, 1)
        if len(parts) == 2 and parts[0].lower() in cls.ARTICLES:
            gender, plural = cls.ARTICLES[parts[0].lower()]
            rest = parts[1].strip()
            if parts[0].lower() in ("el", "un") and rest.split()[0].lower() in Spelling.STRESSED_A:
                gender = "f"
            return rest, gender, plural
        return es, None, False

    @classmethod
    def clean(cls, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip(" \t.;")

    @classmethod
    def parse_line(cls, line: str) -> tuple[dict | None, str]:
        """Returns (word, '') or (None, reason)."""
        tag = None
        found = cls.TAG_RE.search(line)
        if found:
            tag = cls.TAGS[found.group(1).lower()]
            line = cls.TAG_RE.sub(" ", line)
        sep = next((s for s in cls.SEPARATORS if s in line), None)
        if sep is None:
            return None, "no separator"
        es, en = (cls.clean(x) for x in line.split(sep, 1))
        if not es or not en:
            return None, "missing a side"
        es, gender, plural = cls.split_article(es)
        if tag:
            gender, plural = tag
        if len(es) > cls.MAX_ES or len(en) > cls.MAX_EN:
            return None, "too long"
        if not re.search(r"[a-záéíóúüñ]", es, re.IGNORECASE):
            return None, "no Spanish word"
        return {"es": es, "en": en, "gender": gender, "plural": plural}, ""

    @classmethod
    def parse(cls, text: str) -> BulkResult:
        result = BulkResult()
        for raw in (text or "").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            word, reason = cls.parse_line(line)
            if word:
                result.words.append(word)
            else:
                result.skipped.append((line, reason))
        return result


class MyWords:
    """The learner's personal word list (no practical limit)."""

    LIMIT = 5000
    MAX_EXAMPLE = 200

    def __init__(self, memory: MistakeMemory, bank: VocabularyBank):
        self.memory = memory
        self.bank = bank

    def words(self) -> list[Word]:
        return self.memory.own_words

    def count(self) -> int:
        return len(self.memory.own_words)

    def refresh(self) -> None:
        """Mirror the list into BANK.mine for flip cards and quizzes."""
        self.bank.set_mine(self.memory.own_words)

    def _exists(self, es: str) -> bool:
        low = es.lower()
        return any(w.es.lower() == low for w in self.memory.own_words)

    @staticmethod
    def make(es: str, en: str, gender: str | None, plural: bool, example: str = "") -> Word:
        return Word(es, en, gender, "My words", example, "", "", "noun" if gender else "", plural, True)

    def add(self, es: str, en: str, gender: str = "auto", example: str = "") -> tuple[bool, str, Word | None]:
        es = BulkWordParser.clean(es or "")
        en = BulkWordParser.clean(en or "")
        example = (example or "").strip()
        if not es or not en:
            return False, "Please fill in both the Spanish and the English.", None
        plural = False
        if gender == "auto":
            es, gender, plural = BulkWordParser.split_article(es)
        elif gender in ("m", "f", "mpl", "fpl"):
            es, _, had_plural_article = BulkWordParser.split_article(es)
            plural = gender.endswith("pl") or had_plural_article
            gender = gender[0]
        else:  # "none": not a noun, keep exactly what was typed ("la verdad es que…")
            gender = None
        if len(es) > BulkWordParser.MAX_ES or len(en) > BulkWordParser.MAX_EN:
            return False, "That's a bit long. Keep words under 60 characters.", None
        if len(example) > self.MAX_EXAMPLE:
            return False, "Keep the example under 200 characters.", None
        if self._exists(es):
            return False, f"'{es}' is already in your list.", None
        if self.count() >= self.LIMIT:
            return False, f"Your list is full ({self.LIMIT} words).", None
        word = self.make(es, en, gender, plural, example)
        self.memory.set_own_words(self.memory.own_words + [word])
        self.refresh()
        return True, f"Added {word.display}.", word

    def add_bulk(self, text: str) -> dict:
        parsed = BulkWordParser.parse(text)
        added, skipped = [], list(parsed.skipped)
        words = self.memory.own_words
        existing = {w.es.lower() for w in words}
        for item in parsed.words:
            if item["es"].lower() in existing:
                skipped.append((item["es"], "already in your list"))
                continue
            if len(words) >= self.LIMIT:
                skipped.append((item["es"], "list full"))
                continue
            word = self.make(item["es"], item["en"], item["gender"], item["plural"])
            words.append(word)
            existing.add(word.es.lower())
            added.append(word)
        self.memory.set_own_words(words)
        self.refresh()
        return {"added": len(added), "skipped": skipped, "message": self.bulk_message(len(added), skipped)}

    @staticmethod
    def bulk_message(added: int, skipped: list[tuple[str, str]]) -> str:
        if not added and not skipped:
            return "Paste one word per line, like: el perro = dog"
        msg = f"Added {added} word{'s' if added != 1 else ''}."
        if skipped:
            line, reason = skipped[0]
            short = line if len(line) <= 40 else line[:39] + "…"
            n = len(skipped)
            msg += f" {n} line{'s' if n != 1 else ''} skipped ({reason}): '{short}'"
            if n > 1:
                msg += f" and {n - 1} more"
            msg += "."
        return msg

    def remove(self, key: str) -> bool:
        words = self.memory.own_words
        kept = [w for w in words if w.key != key]
        if len(kept) == len(words):
            return False
        self.memory.set_own_words(kept)
        self.memory.set_known(key, False)
        self.refresh()
        return True
