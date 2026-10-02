"""Mistake memory: every answer, known words, the learner's own words, XP and streaks.

Pyodide's clock runs on UTC, so all dates go through ``Clock``, which knows the
browser's timezone offset. Nothing else in the app calls ``date.today()``.
"""
from __future__ import annotations

import datetime as _dt
import json
import time
from dataclasses import dataclass
from typing import ClassVar

from .vocab import Word


@dataclass
class Attempt:
    """One answered question."""

    ts: float
    qkey: str
    skill: str
    pattern: str
    theme: str
    correct: bool
    chosen: str = ""
    answer: str = ""
    big: str = ""

    def to_row(self) -> list:
        return [int(self.ts), self.qkey, self.skill, self.pattern, self.theme,
                1 if self.correct else 0, self.chosen, self.answer, self.big]

    @classmethod
    def from_row(cls, row) -> "Attempt | None":
        try:
            ts, qkey, skill, pattern, theme, ok = row[:6]
            extra = [str(x) for x in row[6:9]] + [""] * (3 - len(row[6:9]))
            if not all(isinstance(x, str) for x in (qkey, skill, pattern, theme)):
                return None
            return cls(float(ts), qkey, skill, pattern, theme, bool(ok), *extra)
        except (TypeError, ValueError):
            return None


class Clock:
    """Turns timestamps into the learner's *local* dates.

    ``tz_offset_minutes`` is exactly what JavaScript's ``Date.getTimezoneOffset()``
    returns: the minutes to add to local time to get UTC (Spain in winter = -60).
    """

    def __init__(self, tz_offset_minutes: int = 0, fixed_now: float | None = None):
        self.tz_offset_minutes = int(tz_offset_minutes or 0)
        self._fixed_now = fixed_now

    def now(self) -> float:
        return self._fixed_now if self._fixed_now is not None else time.time()

    def local(self, ts: float) -> _dt.datetime:
        utc = _dt.datetime(1970, 1, 1) + _dt.timedelta(seconds=ts)
        return utc - _dt.timedelta(minutes=self.tz_offset_minutes)

    def date_of(self, ts: float) -> _dt.date:
        return self.local(ts).date()

    def today(self) -> _dt.date:
        return self.date_of(self.now())

    @staticmethod
    def key(day: _dt.date) -> str:
        return day.isoformat()


class Labels:
    """Friendly names for skills, patterns and themes."""

    SKILLS = {
        "vocab": "Vocabulary",
        "gender": "Gender & articles",
        "serestar": "Ser or estar",
        "verbs": "Present-tense verbs",
        "falsefriends": "False friends",
    }
    SKILL_EMOJI = {"vocab": "📚", "gender": "⚖️", "serestar": "🔀", "verbs": "🏃", "falsefriends": "🎭"}
    SKILL_BLURB = {
        "vocab": "Spanish ↔ English across all five themes",
        "gender": "el, la, los or las, with the rule behind it",
        "serestar": "Origin, location, feelings, events…",
        "verbs": "-ar, -er and -ir endings in the present",
        "falsefriends": "embarazada, éxito, librería and friends",
    }
    PATTERNS = {
        "gender:plural": "plural-only nouns",
        "gender:stressed-a": "el agua words (stressed a-)",
        "gender:greek-ma": "-ma words from Greek",
        "gender:masc-a": "masculine words ending in -a",
        "gender:fem-o": "feminine words ending in -o",
        "gender:short": "shortened words (la foto, la moto)",
        "gender:dad": "-dad / -tad / -tud endings",
        "gender:cion": "-ción / -sión endings",
        "gender:umbre": "-umbre endings",
        "gender:aje": "-aje endings",
        "gender:or": "-or endings",
        "gender:o": "nouns ending in -o",
        "gender:a": "nouns ending in -a",
        "gender:memorise": "nouns to learn with their article",
        "serestar:origin": "ser for origin",
        "serestar:profession": "ser for jobs",
        "serestar:characteristic": "ser for characteristics",
        "serestar:time": "ser for days and times",
        "serestar:event": "ser for where events happen",
        "serestar:identity": "ser for identity",
        "serestar:location": "estar for location",
        "serestar:emotion": "estar for feelings",
        "serestar:condition": "estar for conditions",
        "serestar:progressive": "estar + -ando / -iendo",
        "verbs:ar": "-ar verb endings",
        "verbs:er": "-er verb endings",
        "verbs:ir": "-ir verb endings",
        "falsefriends": "false friends",
    }
    THEMES = {"identities": "Identities", "experiences": "Experiences", "ingenuity": "Human Ingenuity",
              "social": "Social Organization", "planet": "Sharing the Planet", "mine": "My words",
              "grammar": "Grammar"}

    @classmethod
    def skill(cls, skill: str) -> str:
        return cls.SKILLS.get(skill, skill.title())

    @classmethod
    def pattern(cls, pattern: str) -> str:
        if pattern.startswith("topic:"):
            topic = pattern[6:]
            return "your own words" if topic == "My words" else f"{topic} vocabulary"
        return cls.PATTERNS.get(pattern, pattern)

    @classmethod
    def theme(cls, slug: str) -> str:
        return cls.THEMES.get(slug, slug.title())


@dataclass(frozen=True)
class Level:
    """A level on a quadratic XP curve: level n starts at 60·(n−1)² XP."""

    number: int
    name: str
    progress: float   # 0..1 through the current level
    to_next: int      # XP still needed for the next level
    xp: int

    NAMES: ClassVar[tuple[str, ...]] = ("Principiante", "Explorador", "Viajero",
                                         "Conversador", "Hablante", "Maestro")
    STEP: ClassVar[int] = 60

    @classmethod
    def threshold(cls, number: int) -> int:
        return cls.STEP * (number - 1) ** 2

    @classmethod
    def from_xp(cls, xp: int) -> "Level":
        xp = max(0, int(xp))
        n = 1
        while cls.threshold(n + 1) <= xp:
            n += 1
        lo, hi = cls.threshold(n), cls.threshold(n + 1)
        name = cls.NAMES[min(n, len(cls.NAMES)) - 1]
        return cls(n, name, (xp - lo) / (hi - lo), hi - xp, xp)

    def as_dict(self) -> dict:
        return {"number": self.number, "name": self.name, "progress": round(self.progress, 3),
                "to_next": self.to_next, "xp": self.xp}


class MistakeMemory:
    """Stores attempts, known words and the learner's own words; derives everything else."""

    MAX_ATTEMPTS = 1200
    MAX_DAYS = 400
    HALF_LIFE_DAYS = 3.0
    PRIOR_MISS = 1.0      # a gentle prior: 1 miss in 4 answers
    PRIOR_TOTAL = 4.0
    XP_RIGHT, XP_WRONG, XP_KNOWN = 10, 2, 1

    def __init__(self, clock: Clock):
        self.clock = clock
        self._attempts: list[Attempt] = []
        self._known: set[str] = set()
        self._own: list[Word] = []
        self._days: dict[str, int] = {}

    # -- state -------------------------------------------------------------
    @property
    def attempts(self) -> list[Attempt]:
        return list(self._attempts)

    @property
    def own_words(self) -> list[Word]:
        return list(self._own)

    def set_own_words(self, words: list[Word]) -> None:
        self._own = list(words)

    def record(self, attempt: Attempt) -> None:
        self._attempts.append(attempt)
        if len(self._attempts) > self.MAX_ATTEMPTS:
            self._attempts = self._attempts[-self.MAX_ATTEMPTS:]
        self.touch(ts=attempt.ts)

    def set_known(self, key: str, on: bool) -> bool:
        """Mark or unmark a word as known. Returns True if anything changed."""
        if on and key not in self._known:
            self._known.add(key)
            self.touch()
            return True
        if not on and key in self._known:
            self._known.discard(key)
            return True
        return False

    def known_words(self) -> set[str]:
        return set(self._known)

    def reset(self) -> None:
        """Forget answers, known words and activity. The learner's own words stay."""
        self._attempts.clear()
        self._known.clear()
        self._days.clear()

    def touch(self, n: int = 1, ts: float | None = None) -> None:
        """Count some activity for today (or for the day of ``ts``)."""
        day = Clock.key(self.clock.date_of(self.clock.now() if ts is None else ts))
        self._days[day] = self._days.get(day, 0) + n
        if len(self._days) > self.MAX_DAYS:
            for old in sorted(self._days)[:-self.MAX_DAYS]:
                del self._days[old]

    # -- analysis ----------------------------------------------------------
    def weakness_scores(self) -> dict[str, float]:
        """Recency-weighted miss rate per pattern (3-day half-life, Bayesian prior).
        Only patterns with at least one miss are included."""
        now = self.clock.now()
        stats: dict[str, list[float]] = {}
        missed: set[str] = set()
        for a in self._attempts:
            age_days = max(0.0, now - a.ts) / 86400
            weight = 0.5 ** (age_days / self.HALF_LIFE_DAYS)
            s = stats.setdefault(a.pattern, [0.0, 0.0])
            s[1] += weight
            if not a.correct:
                s[0] += weight
                missed.add(a.pattern)
        return {p: (m + self.PRIOR_MISS) / (t + self.PRIOR_TOTAL)
                for p, (m, t) in stats.items() if p in missed}

    def misses(self, pattern: str, days: float | None = None) -> int:
        since = self.clock.now() - days * 86400 if days else float("-inf")
        return sum(1 for a in self._attempts if a.pattern == pattern and not a.correct and a.ts >= since)

    def due_mistakes(self) -> list[Attempt]:
        """Questions whose latest answer was wrong (missed, not since got right). Newest first."""
        latest: dict[str, Attempt] = {}
        for a in self._attempts:
            latest[a.qkey] = a
        due = [a for a in latest.values() if not a.correct]
        return sorted(due, key=lambda a: a.ts, reverse=True)

    def streak(self) -> int:
        day = self.clock.today()
        if not self._days.get(Clock.key(day)):
            day -= _dt.timedelta(days=1)  # today not done yet: the streak is still alive
        count = 0
        while self._days.get(Clock.key(day)):
            count += 1
            day -= _dt.timedelta(days=1)
        return count

    def xp(self) -> int:
        right = sum(1 for a in self._attempts if a.correct)
        wrong = len(self._attempts) - right
        return right * self.XP_RIGHT + wrong * self.XP_WRONG + len(self._known) * self.XP_KNOWN

    def level(self) -> Level:
        return Level.from_xp(self.xp())

    def accuracy(self) -> float | None:
        if not self._attempts:
            return None
        return sum(1 for a in self._attempts if a.correct) / len(self._attempts)

    def breakdown(self, attr: str) -> dict[str, tuple[int, int]]:
        """(right, total) grouped by an Attempt attribute: 'skill', 'theme' or 'pattern'."""
        out: dict[str, list[int]] = {}
        for a in self._attempts:
            s = out.setdefault(getattr(a, attr), [0, 0])
            s[0] += 1 if a.correct else 0
            s[1] += 1
        return {k: (v[0], v[1]) for k, v in out.items()}

    def recent_mistakes(self, n: int = 8) -> list[Attempt]:
        seen, out = set(), []
        for a in reversed(self._attempts):
            if not a.correct and a.qkey not in seen:
                seen.add(a.qkey)
                out.append(a)
                if len(out) >= n:
                    break
        return out

    def activity(self, weeks: int = 12) -> list[list[dict]]:
        """A GitHub-style calendar: ``weeks`` columns of Monday→Sunday cells."""
        today = self.clock.today()
        start = today - _dt.timedelta(days=today.weekday() + 7 * (weeks - 1))
        grid = []
        for w in range(weeks):
            column = []
            for d in range(7):
                day = start + _dt.timedelta(days=7 * w + d)
                count = self._days.get(Clock.key(day), 0)
                level = 0 if count == 0 else 1 if count < 5 else 2 if count < 10 else 3 if count < 20 else 4
                column.append({"date": Clock.key(day), "count": count, "level": level,
                               "future": day > today, "today": day == today})
            grid.append(column)
        return grid

    def active_days(self) -> int:
        return sum(1 for v in self._days.values() if v)

    def insights(self) -> list[str]:
        if not self._attempts:
            return ["Answer a few questions and your mistake memory will start spotting patterns."]
        out = []
        skills = {k: v for k, v in self.breakdown("skill").items() if v[1] >= 5}
        if skills:
            best = max(skills, key=lambda k: skills[k][0] / skills[k][1])
            r, t = skills[best]
            out.append(f"Strongest skill: {Labels.skill(best)} ({round(100 * r / t)}%).")
        weak = self.weakness_scores()
        if weak:
            worst = max(weak, key=weak.get)
            out.append(f"Most missed lately: {Labels.pattern(worst)}.")
        due = len(self.due_mistakes())
        if due:
            out.append(f"{due} question{'s' if due != 1 else ''} waiting in review.")
        streak = self.streak()
        if streak >= 2:
            out.append(f"You've practised {streak} days in a row. ¡Sigue así!")
        return out

    # -- persistence -----------------------------------------------------------
    def export_json(self) -> str:
        data = {
            "v": 1,
            "a": [a.to_row() for a in self._attempts[-self.MAX_ATTEMPTS:]],
            "k": sorted(self._known),
            "m": [[w.es, w.en, w.gender or "", w.example_es, 1 if w.is_plural else 0] for w in self._own],
            "d": self._days,
        }
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    def import_json(self, raw: str) -> bool:
        """Replace the state with a saved one. Returns False (and changes nothing) if it's unreadable."""
        try:
            data = json.loads(raw) if isinstance(raw, str) else None
        except ValueError:
            return False
        if not isinstance(data, dict):
            return False
        attempts = [a for a in (Attempt.from_row(r) for r in data.get("a", []) if isinstance(r, list)) if a]
        known = {k for k in data.get("k", []) if isinstance(k, str)}
        own = []
        for row in data.get("m", []):
            if isinstance(row, list) and len(row) >= 2 and all(isinstance(x, str) for x in row[:2]):
                gender = row[2] if len(row) > 2 and row[2] in ("m", "f") else None
                example = row[3] if len(row) > 3 and isinstance(row[3], str) else ""
                plural = bool(row[4]) if len(row) > 4 else False
                own.append(Word(row[0], row[1], gender, "My words", example, "", "",
                                "noun" if gender else "", plural, True))
        days = {k: int(v) for k, v in (data.get("d") or {}).items()
                if isinstance(k, str) and isinstance(v, (int, float))}
        self._attempts = attempts[-self.MAX_ATTEMPTS:]
        self._known = known
        self._own = own
        self._days = days
        return True
