"""Quiz: questions, the QuestionType hierarchy, sessions and the engine.

The core promise: every option of every question carries its own explanation,
so after a wrong answer the learner sees (1) why their choice is wrong and
(2) why the right answer is right.

    QuestionType (ABC)
    ├── WordQuestion
    │   ├── MeaningQuestion      Spanish → English
    │   ├── TranslateQuestion    English → Spanish
    │   └── GenderQuestion       el / la / los / las
    ├── ChoiceSetQuestion
    │   ├── SerEstarQuestion
    │   └── VerbQuestion
    └── FalseFriendQuestion
"""
from __future__ import annotations

import html
import random
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar

from .grammar import ChoiceSet, Conjugator, GenderRules, Person, SerEstar
from .memory import Attempt, Labels, MistakeMemory
from .vocab import FalseFriend, VocabularyBank, Word

E = html.escape


@dataclass
class Question:
    """One multiple-choice question. Only ``public()`` ever reaches the page."""

    qkey: str
    skill: str
    pattern: str
    theme: str
    kind: str
    prompt: str
    big: str
    answer: str
    explanations: dict[str, str | None]
    correct_expl: str
    options: list[str] = field(default_factory=list)
    sub: str = ""
    example: dict | None = None
    speak: str = ""

    def shuffle(self, rng: random.Random, keep_order: bool = False) -> "Question":
        if not self.options:
            self.options = list(self.explanations)
        if not keep_order:
            rng.shuffle(self.options)
        return self

    def public(self, index: int | None = None) -> dict:
        """What the page may see: no answer, no explanations."""
        return {"index": index, "skill": self.skill, "theme": self.theme, "kind": self.kind,
                "prompt": self.prompt, "big": self.big, "sub": self.sub,
                "options": list(self.options), "speak": self.speak}

    def is_correct(self, choice: str) -> bool:
        return choice == self.answer

    @property
    def target(self) -> str:
        return self.qkey.partition(":")[2]

    @property
    def stem(self) -> str:
        """What the question is *about* (a word, a verb, a sentence) — one per round."""
        return self.target.split(".")[0]


class QuestionType(ABC):
    """A family of questions that can be built at random, from a key, or for a pattern."""

    code: ClassVar[str] = ""            # qkey prefix
    skill: ClassVar[str] = ""
    pattern_prefix: ClassVar[str] = ""

    def __init__(self, bank: VocabularyBank):
        self.bank = bank

    # -- the contract every subclass fulfils ----------------------------------
    @abstractmethod
    def build(self, rng: random.Random, target=None) -> Question | None:
        """Build a question about ``target`` (or a random one)."""

    @abstractmethod
    def target_from_key(self, rest: str):
        """Turn the part of a qkey after 'code:' back into a target (or None)."""

    @abstractmethod
    def targets(self, theme: str | None = None) -> list:
        """Everything this type can ask about."""

    @abstractmethod
    def pattern_of(self, target) -> str:
        """The pattern (rule) a target belongs to, for mistake tracking."""

    # -- shared behaviour ------------------------------------------------------
    def key(self, target_id: str) -> str:
        return f"{self.code}:{target_id}"

    def random(self, rng: random.Random, theme: str | None = None) -> Question | None:
        return self.build(rng, None)

    def from_key(self, qkey: str, rng: random.Random) -> Question | None:
        prefix, _, rest = qkey.partition(":")
        if prefix != self.code:
            return None
        target = self.target_from_key(rest)
        return None if target is None else self.build(rng, target)

    def handles(self, pattern: str) -> bool:
        return bool(self.pattern_prefix) and pattern.startswith(self.pattern_prefix)

    def for_pattern(self, pattern: str, rng: random.Random) -> Question | None:
        if not self.handles(pattern):
            return None
        matches = [t for t in self.targets("*") if self.pattern_of(t) == pattern]
        return self.build(rng, rng.choice(matches)) if matches else None


class WordQuestion(QuestionType):
    """Shared logic for questions about one vocabulary word."""

    pattern_prefix = "topic:"
    skill = "vocab"

    def usable(self, word: Word) -> bool:
        return True

    def pool(self, theme: str | None) -> list[Word]:
        """None = built-in words, '*' = everything, otherwise one theme ('mine' included)."""
        if theme is None:
            return self.bank.all_words(include_mine=False)
        if theme == "*":
            return self.bank.all_words(include_mine=True)
        t = self.bank.theme(theme)
        return list(t.words) if t else []

    def targets(self, theme: str | None = None) -> list[Word]:
        return [w for w in self.pool(theme) if self.usable(w)]

    def target_from_key(self, rest: str) -> Word | None:
        word = self.bank.find(rest)
        return word if word and self.usable(word) else None

    def pattern_of(self, word: Word) -> str:
        return f"topic:{word.topic}"

    def pick(self, rng: random.Random, theme: str | None = None) -> Word:
        """A random usable word from the theme, falling back to all built-in words."""
        words = self.targets(theme) or self.targets(None)
        return rng.choice(words)

    def random(self, rng: random.Random, theme: str | None = None) -> Question | None:
        return self.build(rng, self.pick(rng, theme))

    @staticmethod
    def senses(english: str) -> set[str]:
        """'to try, to taste (food)' -> {'try', 'taste'}: used to avoid two right answers."""
        text = re.sub(r"\([^)]*\)", "", english.lower())
        out = set()
        for part in re.split(r"[,;/]", text):
            part = part.strip()
            for lead in ("to ", "the "):
                if part.startswith(lead):
                    part = part[len(lead):]
            if part:
                out.add(part)
        return out

    def distractors(self, word: Word, rng: random.Random, n: int = 3) -> list[Word]:
        """Plausible wrong words: same theme and kind first, then anywhere."""
        theme = self.bank.theme_of(word)
        local = list(theme.words) if theme else []
        if len(local) < 4:
            local = self.bank.all_words(include_mine=False)
        chosen: list[Word] = []
        banned = self.senses(word.en)
        shown = {word.en.lower(), word.display.lower()}

        def ok(w: Word) -> bool:
            if w.key == word.key or w.en.lower() in shown or w.display.lower() in shown:
                return False
            return not (self.senses(w.en) & banned)

        for group in (
            [w for w in local if w.kind == word.kind],
            local,
            self.bank.all_words(include_mine=False),
        ):
            candidates = [w for w in group if ok(w)]
            rng.shuffle(candidates)
            for w in candidates:
                if len(chosen) >= n:
                    return chosen
                chosen.append(w)
                banned |= self.senses(w.en)
                shown |= {w.en.lower(), w.display.lower()}
        return chosen

    def tip(self, word: Word) -> str:
        if word.tip:
            return word.tip
        return GenderRules.explain(word) if word.is_noun else ""

    @staticmethod
    def example(word: Word) -> dict | None:
        if not word.has_example:
            return None
        return {"es": word.example_es, "en": word.example_en}

    def theme_slug(self, word: Word) -> str:
        theme = self.bank.theme_of(word)
        return theme.slug if theme else "mine"

    @staticmethod
    def kind_note(word: Word) -> str:
        return "" if word.is_noun else (word.kind or ("my word" if word.custom else ""))


class MeaningQuestion(WordQuestion):
    """Spanish → English."""

    code = "meaning"

    def build(self, rng: random.Random, target: Word | None = None) -> Question | None:
        word = target or self.pick(rng)
        wrong = self.distractors(word, rng)
        expl: dict[str, str | None] = {word.en: None}
        for d in wrong:
            expl[d.en] = (f"<b>{E(d.en)}</b> is <b>{E(d.display)}</b> in Spanish — "
                          f"a different word from <b>{E(word.display)}</b>.")
        tip = self.tip(word)
        correct = f"<b>{E(word.display)}</b> means <b>{E(word.en)}</b>." + (f" {E(tip)}" if tip else "")
        return Question(self.key(word.key), self.skill, self.pattern_of(word), self.theme_slug(word),
                        "meaning", "What does this mean?", word.display, word.en, expl, correct,
                        sub=self.kind_note(word), example=self.example(word),
                        speak=word.display).shuffle(rng)


class TranslateQuestion(WordQuestion):
    """English → Spanish."""

    code = "translate"

    def build(self, rng: random.Random, target: Word | None = None) -> Question | None:
        word = target or self.pick(rng)
        wrong = self.distractors(word, rng)
        expl: dict[str, str | None] = {word.display: None}
        for d in wrong:
            expl[d.display] = f"<b>{E(d.display)}</b> means <b>{E(d.en)}</b>, not '{E(word.en)}'."
        tip = self.tip(word)
        correct = (f"'{E(word.en)}' is <b>{E(word.display)}</b>." + (f" {E(tip)}" if tip else ""))
        return Question(self.key(word.key), self.skill, self.pattern_of(word), self.theme_slug(word),
                        "translate", "How do you say this in Spanish?", word.en, word.display, expl,
                        correct, sub=self.kind_note(word), example=self.example(word),
                        speak="").shuffle(rng)


class GenderQuestion(WordQuestion):
    """el / la (or los / las), explained by the gender rule."""

    code = "gender"
    skill = "gender"
    pattern_prefix = "gender:"

    def usable(self, word: Word) -> bool:
        return word.is_noun

    def pattern_of(self, word: Word) -> str:
        return f"gender:{GenderRules.rule_for(word)}"

    def build(self, rng: random.Random, target: Word | None = None) -> Question | None:
        word = target or self.pick(rng)
        if not word.is_noun:
            return None
        options = ["los", "las"] if word.is_plural else ["el", "la"]
        answer = word.article
        wrong = next(o for o in options if o != answer)
        tag = GenderRules.rule_for(word)
        gender = GenderRules.gender_name(word)
        other = "feminine" if word.gender == "m" else "masculine"
        if tag == "stressed-a":
            why_wrong = (f"It <i>is</i> feminine, but <b>la {E(word.es)}</b> is avoided: a stressed a- sound "
                         f"at the start takes <b>el</b> in the singular. {E(GenderRules.RULES[tag])}")
        else:
            why_wrong = (f"<b>{wrong} {E(word.es)}</b> would make it {other}, but <b>{E(word.es)}</b> is "
                         f"{gender}. {E(GenderRules.RULES[tag])}")
        expl: dict[str, str | None] = {answer: None, wrong: why_wrong}
        correct = f"<b>{E(word.display)}</b> ({gender}). {E(GenderRules.explain(word))}"
        prompt = "los or las?" if word.is_plural else "el or la?"
        return Question(self.key(word.key), self.skill, self.pattern_of(word), self.theme_slug(word),
                        "gender", prompt, word.es, answer, expl, correct, options=options,
                        sub=word.en, example=self.example(word), speak="").shuffle(rng, keep_order=True)


class ChoiceSetQuestion(QuestionType):
    """Questions whose options come from a grammar ChoiceSet (four options, each explained)."""

    @abstractmethod
    def choice_set(self, target, rng: random.Random) -> ChoiceSet:
        """The answer, the options and their explanations."""

    @abstractmethod
    def frame(self, target, rng: random.Random) -> dict:
        """prompt / big / sub / example / speak / id for the question card."""

    def build(self, rng: random.Random, target=None) -> Question | None:
        if target is None:
            target = rng.choice(self.targets())
        cs = self.choice_set(target, rng)
        f = self.frame(target, rng)
        return Question(self.key(f["id"]), self.skill, cs.pattern, "grammar", self.code,
                        f["prompt"], f["big"], cs.answer, cs.explanations, cs.correct_expl,
                        options=list(cs.options), sub=f.get("sub", ""), example=f.get("example"),
                        speak=f.get("speak", "")).shuffle(rng)


class SerEstarQuestion(ChoiceSetQuestion):
    code = "serestar"
    skill = "serestar"
    pattern_prefix = "serestar:"

    def targets(self, theme: str | None = None) -> list[int]:
        return list(range(len(SerEstar.ITEMS)))

    def target_from_key(self, rest: str) -> int | None:
        return int(rest) if rest.isdigit() and int(rest) < len(SerEstar.ITEMS) else None

    def pattern_of(self, target: int) -> str:
        return f"serestar:{SerEstar.ITEMS[target].reason}"

    def choice_set(self, target: int, rng: random.Random) -> ChoiceSet:
        return SerEstar.choices(SerEstar.ITEMS[target])

    def frame(self, target: int, rng: random.Random) -> dict:
        item = SerEstar.ITEMS[target]
        return {"id": str(target), "prompt": "Ser or estar? Fill the gap.", "big": item.sentence,
                "sub": item.en, "example": {"es": item.filled, "en": item.en}, "speak": item.sentence}


class VerbQuestion(ChoiceSetQuestion):
    code = "verb"
    skill = "verbs"
    pattern_prefix = "verbs:"

    def targets(self, theme: str | None = None) -> list[tuple[str, str]]:
        return [(v.infinitive, p.code) for v in Conjugator.VERBS for p in Person.all()]

    def target_from_key(self, rest: str) -> tuple[str, str] | None:
        inf, _, person = rest.partition(".")
        if Conjugator.find(inf) is None or person not in Conjugator.ENDINGS["ar"]:
            return None
        return inf, person

    def pattern_of(self, target: tuple[str, str]) -> str:
        return f"verbs:{target[0][-2:]}"

    def choice_set(self, target: tuple[str, str], rng: random.Random) -> ChoiceSet:
        return Conjugator.choices(Conjugator.find(target[0]), target[1], rng)

    def frame(self, target: tuple[str, str], rng: random.Random) -> dict:
        verb = Conjugator.find(target[0])
        subject = Person.subject(target[1], rng)
        sentence = f"{subject} {verb.frame}"
        return {"id": f"{verb.infinitive}.{target[1]}", "prompt": "Pick the right present-tense form.",
                "big": sentence, "sub": f"{verb.infinitive} · {verb.en}",
                "example": {"es": sentence.replace("___", Conjugator.conjugate(verb, target[1])), "en": ""},
                "speak": sentence}


class FalseFriendQuestion(QuestionType):
    """Looks English, means something else. The trap option gets a special explanation."""

    code = "ff"
    skill = "falsefriends"
    pattern_prefix = "falsefriends"

    def targets(self, theme: str | None = None) -> list[FalseFriend]:
        return self.bank.false_friends

    def target_from_key(self, rest: str) -> FalseFriend | None:
        return next((f for f in self.bank.false_friends if f.es == rest), None)

    def pattern_of(self, target: FalseFriend) -> str:
        return "falsefriends"

    def build(self, rng: random.Random, target: FalseFriend | None = None) -> Question | None:
        ff = target or rng.choice(self.targets())
        is_verb = ff.meaning.startswith("to ")
        others = [f for f in self.targets() if f.es != ff.es]
        same = [f for f in others if f.meaning.startswith("to ") == is_verb]
        rng.shuffle(same)
        rest = [f for f in others if f not in same]
        rng.shuffle(rest)
        picks = (same + rest)[:2]
        expl: dict[str, str | None] = {
            ff.meaning: None,
            ff.trap: f"Trap! <b>{E(ff.trap)}</b> is the false friend — the English look-alike. {E(ff.note)}",
        }
        for f in picks:
            expl[f.meaning] = f"<b>{E(f.meaning)}</b> is what <b>{E(f.es)}</b> means."
        correct = f"<b>{E(ff.es)}</b> really means <b>{E(ff.meaning)}</b>. {E(ff.note)}"
        return Question(self.key(ff.es), self.skill, "falsefriends", "grammar", "falsefriend",
                        "False friend! What does it really mean?", ff.es, ff.meaning, expl, correct,
                        sub="It looks like an English word…", speak=ff.es).shuffle(rng)


@dataclass
class QuizSession:
    """One round of questions. Lives on the Python side, answers and all."""

    sid: str
    mode: str
    title: str
    questions: list[Question]
    note: str = ""
    level_start: int = 1
    answers: dict[int, str] = field(default_factory=dict)
    results: dict[int, bool] = field(default_factory=dict)
    feedback: dict[int, dict] = field(default_factory=dict)
    combo: int = 0
    best_combo: int = 0

    @property
    def total(self) -> int:
        return len(self.questions)

    @property
    def score(self) -> int:
        return sum(1 for ok in self.results.values() if ok)

    @property
    def done(self) -> bool:
        return len(self.results) >= self.total

    def record(self, index: int, choice: str, correct: bool) -> None:
        self.answers[index] = choice
        self.results[index] = correct
        self.combo = self.combo + 1 if correct else 0
        self.best_combo = max(self.best_combo, self.combo)

    def xp_gained(self) -> int:
        right = self.score
        return right * MistakeMemory.XP_RIGHT + (len(self.results) - right) * MistakeMemory.XP_WRONG

    def public(self) -> dict:
        return {"sid": self.sid, "mode": self.mode, "title": self.title, "note": self.note,
                "total": self.total, "questions": [q.public(i) for i, q in enumerate(self.questions)]}


class QuizEngine:
    """Owns the question types and builds/checks rounds for every mode."""

    LENGTH = 10
    MAX_SESSIONS = 20
    ALERT_AFTER = 2
    ALERT_WINDOW_DAYS = 14
    MIX_WEIGHTS = {"meaning": 30, "translate": 25, "gender": 15, "serestar": 10, "verb": 10, "ff": 10}
    THEME_WEIGHTS = {"meaning": 40, "translate": 35, "gender": 25}
    SKILL_TYPES = {"vocab": ["meaning", "translate"], "gender": ["gender"], "serestar": ["serestar"],
                   "verbs": ["verb"], "falsefriends": ["ff"]}

    def __init__(self, bank: VocabularyBank, memory: MistakeMemory, seed: int | None = None):
        self.bank = bank
        self.memory = memory
        self.rng = random.Random(seed)
        self.types: dict[str, QuestionType] = {
            t.code: t for t in (MeaningQuestion(bank), TranslateQuestion(bank), GenderQuestion(bank),
                                SerEstarQuestion(bank), VerbQuestion(bank), FalseFriendQuestion(bank))
        }
        self.sessions: dict[str, QuizSession] = {}
        self._counter = 0

    # -- building rounds ----------------------------------------------------
    def question_from_key(self, qkey: str) -> Question | None:
        qtype = self.types.get(qkey.partition(":")[0])
        return qtype.from_key(qkey, self.rng) if qtype else None

    def _weighted(self, weights: dict[str, int]) -> QuestionType:
        codes = list(weights)
        return self.types[self.rng.choices(codes, [weights[c] for c in codes])[0]]

    def _fill(self, questions: list[Question], picker, tries: int = 250) -> None:
        stems = {q.stem for q in questions}
        keys = {q.qkey for q in questions}
        for _ in range(tries):
            if len(questions) >= self.LENGTH:
                return
            q = picker()
            if q is None or q.qkey in keys or q.stem in stems:
                continue
            questions.append(q)
            keys.add(q.qkey)
            stems.add(q.stem)

    def _mix_picker(self):
        return lambda: self._weighted(self.MIX_WEIGHTS).random(self.rng)

    def _pattern_picker(self, weak: dict[str, float]):
        patterns = list(weak)
        weights = [weak[p] ** 2 for p in patterns]

        def pick():
            pattern = self.rng.choices(patterns, weights)[0]
            handlers = [t for t in self.types.values() if t.handles(pattern)]
            return self.rng.choice(handlers).for_pattern(pattern, self.rng) if handlers else None
        return pick

    def start(self, mode: str) -> QuizSession:
        mode = (mode or "mix").strip()
        kind, _, arg = mode.partition(":")
        questions: list[Question] = []
        note = ""
        if kind == "theme" and self.bank.theme(arg):
            theme = self.bank.theme(arg)
            title = f"{theme.emoji} {theme.name}"
            self._fill(questions, lambda: self._weighted(self.THEME_WEIGHTS).random(self.rng, arg))
            if len(questions) < self.LENGTH:
                note = ("You have only a few words here, so the round is topped up with general vocabulary."
                        if arg == "mine" else "")
        elif kind == "skill" and arg in self.SKILL_TYPES:
            title = f"{Labels.SKILL_EMOJI[arg]} {Labels.skill(arg)}"
            codes = self.SKILL_TYPES[arg]
            self._fill(questions, lambda: self.types[self.rng.choice(codes)].random(self.rng))
        elif kind == "review":
            title = "🧠 Review my mistakes"
            for attempt in self.memory.due_mistakes():
                if len(questions) >= self.LENGTH:
                    break
                q = self.question_from_key(attempt.qkey)
                if q and q.qkey not in {x.qkey for x in questions} and q.stem not in {x.stem for x in questions}:
                    questions.append(q)
            weak = self.memory.weakness_scores()
            if weak:
                self._fill(questions, self._pattern_picker(weak))
            if not questions:
                note = "Nothing to review yet, so here's a mixed warm-up. Anything you miss will come back here."
        else:
            mode, title = "mix", "🎲 Mixed practice"
        self._fill(questions, self._mix_picker(), tries=400)

        self._counter += 1
        sid = f"s{self._counter}-{self.rng.randrange(16 ** 6):06x}"
        session = QuizSession(sid, mode, title, questions[: self.LENGTH], note,
                              level_start=self.memory.level().number)
        self.sessions[sid] = session
        while len(self.sessions) > self.MAX_SESSIONS:
            del self.sessions[next(iter(self.sessions))]
        return session

    # -- checking answers -------------------------------------------------------
    def check(self, sid: str, index: int, choice: str) -> dict:
        session = self.sessions.get(sid)
        if session is None:
            return {"error": "This quiz has expired. Start a new round."}
        if not 0 <= index < session.total:
            return {"error": "That question doesn't exist."}
        if index in session.feedback:
            return session.feedback[index]
        q = session.questions[index]
        correct = q.is_correct(choice)
        self.memory.record(Attempt(self.memory.clock.now(), q.qkey, q.skill, q.pattern, q.theme,
                                   correct, choice, q.answer, q.big))
        session.record(index, choice, correct)
        alert = ""
        if not correct:
            n = self.memory.misses(q.pattern, days=self.ALERT_WINDOW_DAYS)
            if n >= self.ALERT_AFTER:
                alert = (f"Pattern spotted: that's {n} misses on {Labels.pattern(q.pattern)}. "
                         f"Review mode will drill this.")
        why_wrong = None
        if not correct:
            why_wrong = q.explanations.get(choice) or "That isn't one of the options for this question."
        result = {
            "index": index, "correct": correct, "choice": choice, "answer": q.answer,
            "why_wrong": why_wrong, "why_right": q.correct_expl, "example": q.example,
            "alert": alert, "score": session.score, "answered": len(session.results),
            "total": session.total, "combo": session.combo, "done": session.done,
        }
        if session.done:
            result["summary"] = self.summary(session)
        session.feedback[index] = result
        return result

    def summary(self, session: QuizSession) -> dict:
        level = self.memory.level()
        mistakes = [{"big": q.big, "chosen": session.answers.get(i, ""), "answer": q.answer}
                    for i, q in enumerate(session.questions) if session.results.get(i) is False]
        pct = round(100 * session.score / session.total) if session.total else 0
        return {"score": session.score, "total": session.total, "pct": pct,
                "xp": session.xp_gained(), "best_combo": session.best_combo,
                "level": level.as_dict(), "level_up": level.number > session.level_start,
                "mistakes": mistakes, "mode": session.mode}
