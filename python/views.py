"""Page classes: each one renders a screen of the site as an HTML string.

Every piece of text that reaches the page goes through ``html.escape``.
That matters most for the learner's own words, which are user input.
"""
from __future__ import annotations

import datetime as _dt
import html
import json
import math

from core.grammar import GenderRules
from core.memory import Labels, Level
from core.oral import OralCoach
from core.vocab import Spelling, Theme, Word
from core.writing import WritingCoach

E = html.escape


class Page:
    """Base page: shared helpers. Subclasses implement ``render``."""

    EXAM_DATE = _dt.date(2027, 5, 3)

    def __init__(self, app):
        self.app = app

    def render(self, arg: str = "") -> str:
        raise NotImplementedError(f"{type(self).__name__} must implement render()")

    # -- data helpers ---------------------------------------------------------
    def countdown(self) -> int:
        return max(0, (self.EXAM_DATE - self.app.clock.today()).days)

    def word_of_the_day(self) -> Word:
        return self.app.bank.word_of_the_day(self.app.clock.today())

    def summary(self) -> dict:
        memory = self.app.memory
        level = memory.level()
        acc = memory.accuracy()
        return {"streak": memory.streak(), "level": level, "xp": memory.xp(),
                "due": len(memory.due_mistakes()), "answers": len(memory.attempts),
                "accuracy": None if acc is None else round(100 * acc),
                "known": len(memory.known_words())}

    # -- formatting helpers ------------------------------------------------------
    @staticmethod
    def plural(n: int, one: str, many: str | None = None) -> str:
        return f"{n} {one if n == 1 else (many or one + 's')}"

    @staticmethod
    def mode_link(mode: str) -> str:
        """'theme:planet' -> '#play-theme.planet'"""
        return "#play-" + mode.replace(":", ".")

    @staticmethod
    def grad(theme: Theme) -> str:
        return theme.gradient(135)

    @staticmethod
    def delay(i: int, step: int = 70) -> str:
        return f"--d:{i * step}ms"

    @staticmethod
    def speak_btn(text: str, label: str = "", cls: str = "") -> str:
        say = E(text)
        return (f'<button type="button" class="icon-btn speak {cls}" data-say="{say}" '
                f'aria-label="Pronounce {E(label or text)}">🔊</button>')

    @staticmethod
    def ring(pct: float, size: int = 120, stroke: int = 12, cls: str = "ring", gid: str = "rg") -> str:
        r = (size - stroke) / 2
        c = 2 * math.pi * r
        pct = max(0.0, min(100.0, pct))
        mid = size / 2
        return (f'<svg class="{cls}" viewBox="0 0 {size} {size}" aria-hidden="true">'
                f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
                f'<stop offset="0" style="stop-color:var(--sun)"/><stop offset=".55" style="stop-color:var(--rose)"/>'
                f'<stop offset="1" style="stop-color:var(--plum)"/></linearGradient></defs>'
                f'<circle class="ring-track" cx="{mid}" cy="{mid}" r="{r:.1f}" stroke-width="{stroke}"/>'
                f'<circle class="ring-fill" cx="{mid}" cy="{mid}" r="{r:.1f}" stroke-width="{stroke}" '
                f'stroke="url(#{gid})" stroke-dasharray="{c:.1f}" stroke-dashoffset="{c:.1f}" '
                f'data-offset="{c * (1 - pct / 100):.1f}" transform="rotate(-90 {mid} {mid})"/></svg>')

    @staticmethod
    def label_class(word: Word) -> str:
        if word.gender == "m":
            return "g-m"
        if word.gender == "f":
            return "g-f"
        return "g-x"

    @staticmethod
    def head(eyebrow: str, title_html: str, lede: str = "", extra: str = "") -> str:
        lede_html = f'<p class="lede">{lede}</p>' if lede else ""
        return (f'<header class="page-head rise"><p class="eyebrow">{E(eyebrow)}</p>'
                f'<h1 class="display-sm">{title_html}</h1>{lede_html}{extra}</header>')

    def theme_card(self, theme: Theme, i: int, known: set[str]) -> str:
        total = len(theme.words)
        k = theme.known_count(known)
        pct = round(100 * k / total) if total else 0
        topics = " · ".join(E(t) for t in theme.topics)
        return (f'<a class="theme-card tilt rise" href="#theme-{theme.slug}" '
                f'style="--g:{self.grad(theme)};{self.delay(i)}">'
                f'<span class="shine" aria-hidden="true"></span>'
                f'<span class="tc-emoji" aria-hidden="true">{theme.emoji}</span>'
                f'<span class="tc-es">{E(theme.name_es)}</span>'
                f'<span class="tc-name">{E(theme.name)}</span>'
                f'<span class="tc-topics">{topics}</span>'
                f'<span class="tc-progress"><span class="bar"><i style="--w:{pct}%"></i></span>'
                f'<span>{k} / {total} known</span></span></a>')


class HomePage(Page):
    PHRASES = ["¿Qué tal estás?", "Me llamo Alex y tengo diecisiete años.", "Me encanta viajar.",
               "El fin de semana pasado fui a la playa.", "En mi opinión, es muy importante reciclar.",
               "Hace buen tiempo hoy.", "¡Mucha suerte en el examen!"]

    def render(self, arg: str = "") -> str:
        s = self.summary()
        lvl: Level = s["level"]
        w = self.word_of_the_day()
        known = self.app.memory.known_words()
        themes = "".join(self.theme_card(t, i, known) for i, t in enumerate(self.app.bank.themes.values()))
        days = self.countdown()
        exam = self.EXAM_DATE
        example = (f'<p class="wotd-ex">{E(w.example_es)}<i>{E(w.example_en)}</i></p>'
                   if w.has_example else "")
        tip = f'<p class="wotd-tip">💡 {E(w.tip)}</p>' if w.tip else ""
        label = (f'<span class="wc-label {self.label_class(w)}">{E(w.label)}</span>')
        insights = "".join(f"<li>{E(t)}</li>" for t in self.app.memory.insights()[:3])
        due = s["due"]
        due_line = (f'<b data-count="{due}">0</b> {"question" if due == 1 else "questions"} waiting'
                    if due else "Nothing waiting. Mistakes you make will appear here.")
        phrases = E(json.dumps(self.PHRASES, ensure_ascii=False))
        return f"""
<div class="page home">
  <section class="hero">
    <div class="hero-copy rise">
      <p class="eyebrow"><span class="pulse-dot" aria-hidden="true"></span>IB Spanish ab initio · May 2027</p>
      <h1 class="display"><span class="hola">¡Hola! <span class="wave" aria-hidden="true">👋</span></span>
        <span class="line2">Vamos <em class="grad-text">a aprender.</em></span></h1>
      <p class="typing" aria-hidden="true"><span class="typed" data-phrases="{phrases}"></span><span class="caret"></span></p>
      <p class="lede">Vocabulary for all five themes, a quiz that remembers your mistakes, oral practice with a
        real exam timer and a Paper 1 writing coach. All in your browser.</p>
      <div class="btn-row">
        <a class="btn btn-primary" href="#play-mix">Start a quiz <span aria-hidden="true">→</span></a>
        <a class="btn btn-ghost" href="#vocab">Browse vocabulary</a>
      </div>
    </div>
    <div class="hero-side rise" style="{self.delay(2)}">
      <div class="wotd flip" tabindex="0" role="button" aria-label="Word of the day: {E(w.display)}. Press to flip.">
        <div class="flip-inner">
          <div class="face front">
            <span class="wotd-tag">Palabra del día</span>
            <div class="wotd-main">{label}<span class="wotd-word">{E(w.es)}</span></div>
            <span class="wotd-hint">Tap to flip ↻</span>
          </div>
          <div class="face back">
            <span class="wotd-tag">{E(w.display)}</span>
            <span class="wotd-meaning">{E(w.en)}</span>
            {example}{tip}
            {self.speak_btn(w.example_es or w.display, w.display, "wotd-speak")}
          </div>
        </div>
      </div>
      <div class="mini mini-streak glass">
        <span class="mini-ico" aria-hidden="true">🔥</span>
        <div><b data-count="{s['streak']}">0</b><span>day streak</span></div>
      </div>
      <div class="mini mini-level glass">
        <span class="mini-ico" aria-hidden="true">⭐</span>
        <div><b>Lv {lvl.number} · {E(lvl.name)}</b>
          <span class="bar" title="{lvl.xp} XP"><i style="--w:{round(lvl.progress * 100)}%"></i></span></div>
      </div>
    </div>
  </section>

  <section class="band rise" style="{self.delay(3)}">
    <div class="band-num"><b data-count="{days}">0</b><span>{"day" if days == 1 else "days"}</span></div>
    <div class="band-copy">
      <h2>until your exams begin</h2>
      <p>{exam:%A} {exam.day} {exam:%B %Y}. Ten focused minutes a day adds up to hours of practice.</p>
    </div>
    <a class="btn btn-light" href="#play-review">Review mistakes</a>
  </section>

  <section class="section">
    <div class="section-head rise"><h2 class="h2">Five themes, <em>one goal.</em></h2>
      <a class="link" href="#vocab">All vocabulary →</a></div>
    <div class="theme-grid">{themes}</div>
  </section>

  <section class="home-bottom">
    <a class="memory-card glass rise" href="#play-review">
      <span class="memory-ico" aria-hidden="true">🧠</span>
      <div class="memory-copy">
        <p class="eyebrow">Mistake memory</p>
        <h3>{due_line}</h3>
        <ul class="insights">{insights}</ul>
      </div>
      <span class="btn btn-primary">Review now →</span>
    </a>
    <div class="features">
      <a class="feature glass rise" href="#oral" style="{self.delay(1)}"><span aria-hidden="true">🎙️</span>
        <b>Oral practice</b><small>A fresh picture every time, examiner questions read aloud and a 15-minute prep timer.</small></a>
      <a class="feature glass rise" href="#write" style="{self.delay(2)}"><span aria-hidden="true">✍️</span>
        <b>Paper 1 coach</b><small>Spanglish, accents and ¿¡ marked in your text, plus connectors, tenses and conventions.</small></a>
      <a class="feature glass rise" href="#mywords" style="{self.delay(3)}"><span aria-hidden="true">⭐</span>
        <b>My words</b><small>Paste your class vocab lists and turn them into flip cards and quizzes.</small></a>
    </div>
  </section>
</div>"""


class VocabPage(Page):
    def render(self, arg: str = "") -> str:
        bank = self.app.bank
        known = self.app.memory.known_words()
        cards = "".join(self.theme_card(t, i, known) for i, t in enumerate(bank.themes.values()))
        mine = bank.mine
        n = len(mine.words)
        mine_card = (f'<a class="theme-card mine-card tilt rise" href="{"#theme-mine" if n else "#mywords"}" '
                     f'style="--g:{self.grad(mine)};{self.delay(5)}"><span class="shine" aria-hidden="true"></span>'
                     f'<span class="tc-emoji" aria-hidden="true">⭐</span><span class="tc-es">Mis palabras</span>'
                     f'<span class="tc-name">My words</span>'
                     f'<span class="tc-topics">{"Your own list: " + self.plural(n, "word") if n else "Add your class lists, no limit"}</span>'
                     f'<span class="tc-progress"><span class="bar"><i style="--w:{round(100 * mine.known_count(known) / n) if n else 0}%"></i></span>'
                     f'<span>{mine.known_count(known)} / {n} known</span></span></a>')
        rows = "".join(
            f'<tr class="rise" style="{self.delay(i, 30)}"><td data-th="Spanish"><span class="ff-es">{E(f.es)}</span>'
            f'{self.speak_btn(f.es)}</td><td data-th="Really means"><b>{E(f.meaning)}</b></td>'
            f'<td data-th="Not…"><s>{E(f.trap)}</s></td><td data-th="Note">{E(f.note)}</td></tr>'
            for i, f in enumerate(bank.false_friends))
        lede = (f"{bank.total()} words across the five IB themes, from high-frequency nouns to the phrases that "
                f"lift a Paper 1 answer. Open a theme, flip the cards and mark the ones you know.")
        return f"""
<div class="page vocab">
  {self.head("Vocabulary", "Every word, <em>by theme.</em>", E(lede))}
  <div class="theme-grid six">{cards}{mine_card}</div>
  <section class="glass panel ff rise">
    <div class="section-head">
      <div><h2 class="h2">False friends</h2><p class="muted">They look English. They aren't.</p></div>
      <a class="btn btn-primary" href="#play-skill.falsefriends">Quiz me on these</a>
    </div>
    <div class="table-wrap"><table class="ff-table">
      <thead><tr><th>Spanish</th><th>Really means</th><th>Not…</th><th>Note</th></tr></thead>
      <tbody>{rows}</tbody></table></div>
  </section>
</div>"""


class ThemePage(Page):
    def card(self, w: Word, i: int, known: bool) -> str:
        search = Spelling.strip_accents(f"{w.display} {w.en}".lower())
        if w.has_example:
            ex_en = f"<i>{E(w.example_en)}</i>" if w.example_en else ""
            back_mid = f'<p class="wc-ex">{E(w.example_es)}{ex_en}</p>'
        else:
            back_mid = f'<p class="wc-ex muted">{E(w.topic)}</p>'
        tip = w.tip or (GenderRules.explain(w) if w.is_noun else "")
        tip_html = f'<p class="wc-tip">💡 {E(tip)}</p>' if tip else ""
        k = " known" if known else ""
        return f"""<article class="wcard flip{k}" data-key="{E(w.key)}" data-topic="{E(w.topic)}" data-search="{E(search)}" tabindex="0" role="button" aria-label="{E(w.display)}. Press to flip." style="{self.delay(min(i, 16), 25)}">
  <div class="flip-inner">
    <div class="face front">
      <div class="wc-top"><span class="wc-topic">{E(w.topic)}</span><span class="wc-badge" aria-hidden="true">✓ known</span></div>
      <div class="wc-main"><span class="wc-label {self.label_class(w)}">{E(w.label)}</span><span class="wc-word">{E(w.es)}</span></div>
      <div class="wc-actions">{self.speak_btn(w.display)}<button type="button" class="icon-btn known-btn" aria-pressed="{"true" if known else "false"}" aria-label="I know {E(w.display)}">✓</button></div>
    </div>
    <div class="face back">
      <span class="wc-meaning">{E(w.en)}</span>
      {back_mid}{tip_html}
    </div>
  </div>
</article>"""

    def render(self, arg: str = "") -> str:
        theme = self.app.bank.theme(arg)
        if theme is None:
            return VocabPage(self.app).render()
        known = self.app.memory.known_words()
        total = len(theme.words)
        k = theme.known_count(known)
        pct = round(100 * k / total) if total else 0
        is_mine = theme.slug == "mine"
        add_btn = '<a class="btn btn-glass" href="#mywords">＋ Add words</a>' if is_mine else ""
        quiz_btn = (f'<a class="btn btn-light" href="{self.mode_link("theme:" + theme.slug)}">Quiz this theme</a>'
                    if total else "")
        chips = "".join(f'<button type="button" class="chip" data-topic="{E(t)}">{E(t)}</button>'
                        for t in theme.topics if any(w.topic == t for w in theme.words))
        cards = "".join(self.card(w, i, w.key in known) for i, w in enumerate(theme.words))
        if not total:
            body = ('<div class="empty-state glass rise"><span aria-hidden="true">⭐</span>'
                    '<h2>No words yet</h2><p>Add your own vocabulary and it will appear here as flip cards.</p>'
                    '<a class="btn btn-primary" href="#mywords">＋ Add words</a></div>')
        else:
            body = f"""
  <section class="toolbar glass rise" style="{self.delay(1)}">
    <label class="search"><span aria-hidden="true">🔎</span>
      <input type="search" id="card-search" placeholder="Search in Spanish or English" aria-label="Search words" autocomplete="off"></label>
    <div class="chips" role="group" aria-label="Filter by topic">
      <button type="button" class="chip active" data-topic="">All</button>{chips if len(theme.topics) > 1 else ""}</div>
    <label class="toggle"><input type="checkbox" id="unknown-only"><span class="toggle-ui" aria-hidden="true"></span><span>Not known yet</span></label>
  </section>
  <p class="count-line" id="card-count" role="status">{self.plural(total, "word")}</p>
  <div class="card-grid" id="card-grid">{cards}</div>
  <p class="empty-line" id="card-empty" hidden>No words match. Try another search or filter.</p>"""
        return f"""
<div class="page theme-page" data-theme="{E(theme.slug)}" data-total="{total}">
  <section class="banner rise" style="--g:{self.grad(theme)}">
    <a class="back-link" href="#vocab">← All themes</a>
    <div class="banner-body">
      <div class="banner-copy">
        <span class="banner-emoji" aria-hidden="true">{theme.emoji}</span>
        <h1>{E(theme.name)}</h1>
        <p class="banner-es">{E(theme.name_es)}</p>
        <div class="btn-row">{quiz_btn}{add_btn}</div>
      </div>
      <div class="ring-wrap">{self.ring(pct, 132, 12, "ring ring-light", "rg-theme")}
        <div class="ring-label"><b id="known-count">{k}</b><span>/ {total} known</span></div></div>
    </div>
  </section>
  {body}
</div>"""


class MyWordsPage(Page):
    def list_html(self) -> str:
        words = self.app.mywords.words()
        if not words:
            return ('<div class="empty-state small"><span aria-hidden="true">📝</span>'
                    '<p>Your list is empty. Add a word above or paste a whole list.</p></div>')
        items = "".join(
            f'<li class="mw-item" data-key="{E(w.key)}">'
            f'<span class="wc-label {self.label_class(w)}">{E(w.label)}</span>'
            f'<span class="mw-es">{E(w.es)}</span><span class="mw-en">{E(w.en)}</span>'
            f'{self.speak_btn(w.display)}'
            f'<button type="button" class="icon-btn del-btn" data-key="{E(w.key)}" aria-label="Remove {E(w.es)}">✕</button></li>'
            for w in reversed(words))
        return f'<ul class="mw-list" id="mw-list">{items}</ul>'

    def actions_html(self) -> str:
        n = self.app.mywords.count()
        if not n:
            return ""
        return ('<a class="btn btn-ghost" href="#theme-mine">Flip cards</a>'
                f'<a class="btn btn-primary" href="{self.mode_link("theme:mine")}">Quiz my words</a>')

    def render(self, arg: str = "") -> str:
        n = self.app.mywords.count()
        return f"""
<div class="page mywords">
  {self.head("My words", "Your words, <em>no limit.</em>",
             "Add the vocabulary from your own lessons. Your words become flip cards and quiz questions, and they're saved in this browser.")}
  <div class="mw-grid">
    <section class="glass panel rise" style="{self.delay(1)}">
      <h2 class="h3">Add a word</h2>
      <form id="mw-form" class="form" autocomplete="off" novalidate>
        <div class="field"><label for="mw-es">Spanish</label><input id="mw-es" name="es" placeholder="el perro" maxlength="60" lang="es"></div>
        <div class="field"><label for="mw-en">English</label><input id="mw-en" name="en" placeholder="dog" maxlength="80"></div>
        <div class="field"><label for="mw-gender">Gender</label>
          <select id="mw-gender" name="gender">
            <option value="auto">Auto (from el / la)</option><option value="m">Masculine (el)</option>
            <option value="f">Feminine (la)</option><option value="none">Not a noun</option></select></div>
        <div class="field"><label for="mw-ex">Example <small>(optional)</small></label><input id="mw-ex" name="example" maxlength="200" placeholder="Mi perro se llama Toby." lang="es"></div>
        <div class="form-foot"><button class="btn btn-primary" type="submit">Add word</button>
          <p class="form-msg" id="mw-msg" role="status" aria-live="polite"></p></div>
      </form>
    </section>
    <section class="glass panel rise" style="{self.delay(2)}">
      <h2 class="h3">Paste a list</h2>
      <p class="muted small">One word per line. Put <code>=</code> <code>-</code> <code>:</code> <code>,</code> or a tab between
        the Spanish and the English. <code>el / la / los / las</code> sets the gender, or add <code>(m)</code> <code>(f)</code> <code>(mpl)</code> <code>(fpl)</code>.</p>
      <label for="mw-bulk" class="sr-only">Word list</label>
      <textarea id="mw-bulk" rows="6" lang="es" placeholder="el perro = dog&#10;la casa - house&#10;gato: cat (m)&#10;las gafas, glasses"></textarea>
      <div class="form-foot"><button class="btn btn-primary" id="mw-bulk-btn" type="button">Add list</button>
        <p class="form-msg" id="mw-bulk-msg" role="status" aria-live="polite"></p></div>
    </section>
  </div>
  <section class="glass panel rise" style="{self.delay(3)}">
    <div class="section-head">
      <h2 class="h3">Your list <span class="pill" id="mw-count">{n}</span></h2>
      <div class="btn-row" id="mw-actions">{self.actions_html()}</div>
    </div>
    <div id="mw-list-wrap">{self.list_html()}</div>
  </section>
</div>"""


class QuizPage(Page):
    BANDS = [(100, "¡Perfecto!", "A flawless round. Nothing gets past you."),
             (80, "¡Fantástico!", "Brilliant work. You really know this."),
             (60, "¡Muy bien!", "Solid. Your misses are saved for review."),
             (40, "¡Vas bien!", "Getting there. Every miss is now in your review list."),
             (0, "¡Ánimo!", "Tough round, but this is how it sticks. Try review mode next.")]

    def mode_card(self, href: str, emoji: str, title: str, sub: str, i: int, grad: str = "", cls: str = "") -> str:
        style = f"--g:{grad};" if grad else ""
        return (f'<a class="mode-card glass tilt rise {cls}" href="{href}" style="{style}{self.delay(i, 50)}">'
                f'<span class="shine" aria-hidden="true"></span><span class="mode-emoji" aria-hidden="true">{emoji}</span>'
                f'<span class="mode-copy"><b>{E(title)}</b><small>{E(sub)}</small></span>'
                f'<span class="mode-go" aria-hidden="true">→</span></a>')

    def render(self, arg: str = "") -> str:
        memory = self.app.memory
        due = len(memory.due_mistakes())
        weak = sorted(memory.weakness_scores().items(), key=lambda kv: -kv[1])[:4]
        focus = "".join(f'<span class="chip chip-light">{E(Labels.pattern(p))}</span>' for p, _ in weak)
        focus_html = (f'<div class="review-focus"><span>Focus:</span>{focus}</div>' if focus else
                      '<p class="review-sub">No mistakes yet. Play a round and anything you miss lands here.</p>')
        badge = f'<span class="due-badge">{due} due</span>' if due else ""
        bank = self.app.bank
        themes = "".join(self.mode_card(self.mode_link(f"theme:{t.slug}"), t.emoji, t.name,
                                        f"{len(t.words)} words · {t.name_es}", i, self.grad(t))
                         for i, t in enumerate(bank.themes.values()))
        if bank.mine.words:
            themes += self.mode_card(self.mode_link("theme:mine"), "⭐", "My words",
                                     self.plural(len(bank.mine.words), "word"), 5, self.grad(bank.mine))
        skills = "".join(self.mode_card(self.mode_link(f"skill:{s}"), Labels.SKILL_EMOJI[s], Labels.skill(s),
                                        Labels.SKILL_BLURB[s], i)
                         for i, s in enumerate(Labels.SKILLS))
        return f"""
<div class="page quiz">
  {self.head("Quiz", "Pick a mode. <em>Learn from every miss.</em>",
             "Ten questions a round. Every wrong answer explains why it's wrong and why the right one is right, and your mistake memory brings it back later.")}
  <div class="quiz-top">
    <a class="review-card rise" href="#play-review" style="{self.delay(1)}">
      <span class="review-ico" aria-hidden="true">🧠</span>
      <div class="review-copy"><p class="eyebrow light">Recommended</p><h2>Review my mistakes {badge}</h2>{focus_html}</div>
      <span class="btn btn-light">Start review →</span>
    </a>
    {self.mode_card("#play-mix", "🎲", "Mixed practice", "Mostly vocabulary, with grammar and false friends", 2, "", "big")}
  </div>
  <section class="mode-section">
    <h2 class="h3 rise">By theme</h2>
    <div class="mode-grid{" six" if bank.mine.words else ""}">{themes}</div>
  </section>
  <section class="mode-section">
    <h2 class="h3 rise">By skill</h2>
    <div class="mode-grid">{skills}</div>
  </section>
</div>"""

    # -- play screen -------------------------------------------------------------
    @staticmethod
    def big_html(text: str) -> str:
        return E(text).replace("___", '<span class="blank" aria-label="blank"></span>')

    def question_html(self, q: dict, total: int) -> str:
        i = q["index"]
        skill = Labels.skill(q["skill"])
        emoji = Labels.SKILL_EMOJI.get(q["skill"], "")
        theme = q["theme"]
        theme_chip = (f'<span class="chip chip-soft">{E(Labels.theme(theme))}</span>'
                      if theme not in ("grammar", "") else "")
        speak = self.speak_btn(q["speak"].replace("___", "…"), "the prompt") if q["speak"] else ""
        n = len(q["options"])
        opts = "".join(
            f'<button type="button" class="opt" data-choice="{E(o)}" data-n="{k + 1}">'
            f'<kbd aria-hidden="true">{k + 1}</kbd><span>{E(o)}</span></button>'
            for k, o in enumerate(q["options"]))
        sub = f'<p class="q-sub">{E(q["sub"])}</p>' if q["sub"] else ""
        hidden = "" if i == 0 else " hidden"
        return f"""<article class="q-card glass" data-i="{i}"{hidden}>
  <div class="q-meta"><span class="chip chip-soft">{emoji} {E(skill)}</span>{theme_chip}<span class="q-count">{i + 1} / {total}</span></div>
  <p class="q-prompt">{E(q["prompt"])}</p>
  <div class="q-big-row"><h2 class="q-big" lang="{"en" if q["kind"] == "translate" else "es"}">{self.big_html(q["big"])}</h2>{speak}</div>
  {sub}
  <div class="options n{n}" role="group" aria-label="Answers">{opts}</div>
  <div class="feedback" aria-live="polite"></div>
  <div class="q-next" hidden><button type="button" class="btn btn-primary next-btn">{"See results" if i == total - 1 else "Next"} →</button><span class="hint">or press Enter</span></div>
</article>"""

    def play_html(self, session: dict) -> str:
        total = session["total"]
        dots = "".join(f'<li class="dot{" current" if i == 0 else ""}"></li>' for i in range(total))
        cards = "".join(self.question_html(q, total) for q in session["questions"])
        note = f'<p class="play-note rise">{E(session["note"])}</p>' if session["note"] else ""
        return f"""
<div class="page play" data-sid="{E(session["sid"])}" data-total="{total}" data-mode="{E(session["mode"])}">
  <div class="play-top rise">
    <a class="btn btn-ghost btn-sm" href="#quiz">✕ Quit</a>
    <p class="play-title">{E(session["title"])}</p>
    <div class="combo" id="combo" hidden aria-live="polite">🔥 ×<b>2</b></div>
  </div>
  <ol class="dots rise" aria-label="Progress">{dots}</ol>
  {note}
  <div class="q-stage" id="q-stage">{cards}</div>
</div>"""

    def feedback_html(self, r: dict) -> str:
        parts = []
        if r.get("error"):
            return f'<div class="fb bad"><p class="fb-head">{E(r["error"])}</p></div>'
        if r["correct"]:
            parts.append('<p class="fb-head good">✓ ¡Correcto!</p>')
        else:
            parts.append('<p class="fb-head bad">✗ Not quite</p>')
            parts.append(f'<div class="fb-block bad"><h3>Why “{E(r["choice"])}” is wrong</h3>'
                         f'<p>{r["why_wrong"]}</p></div>')
        parts.append(f'<div class="fb-block good"><h3>Why “{E(r["answer"])}” is right</h3>'
                     f'<p>{r["why_right"]}</p></div>')
        ex = r.get("example")
        if ex and ex.get("es"):
            en = f'<p class="en">{E(ex["en"])}</p>' if ex.get("en") else ""
            parts.append(f'<div class="fb-example">{self.speak_btn(ex["es"], "the example")}'
                         f'<div><p class="es" lang="es">{E(ex["es"])}</p>{en}</div></div>')
        if r.get("alert"):
            parts.append(f'<div class="fb-alert" role="note"><span aria-hidden="true">🧩</span>'
                         f'<p>{E(r["alert"])}</p></div>')
        cls = "good" if r["correct"] else "bad"
        return f'<div class="fb {cls}">{"".join(parts)}</div>'

    def results_html(self, s: dict) -> str:
        pct = s["pct"]
        title, sub = next((t, d) for limit, t, d in self.BANDS if pct >= limit)
        lvl = s["level"]
        level_up = (f'<p class="level-up">⭐ Level up! You\'re now <b>Level {lvl["number"]} · {E(lvl["name"])}</b></p>'
                    if s["level_up"] else "")
        if s["mistakes"]:
            items = "".join(
                f'<li><span class="m-q" lang="es">{self.big_html(m["big"])}</span>'
                f'<span class="m-a"><s>{E(m["chosen"])}</s> → <b>{E(m["answer"])}</b></span></li>'
                for m in s["mistakes"])
            mistakes = f'<div class="mistakes"><h3>Your mistakes</h3><ul>{items}</ul></div>'
        else:
            mistakes = '<p class="no-mistakes">No mistakes at all. ¡Enhorabuena!</p>'
        again = self.mode_link(s["mode"])
        confetti = "1" if pct >= 80 else "0"
        return f"""
<section class="results glass rise" data-confetti="{confetti}">
  <div class="score-ring">{self.ring(pct, 168, 14, "ring", "rg-score")}
    <div class="ring-label big"><span class="rl-num"><b data-count="{pct}">0</b><i>%</i></span><small>{s["score"]} / {s["total"]} correct</small></div></div>
  <h2 class="results-title">{E(title)}</h2>
  <p class="results-sub">{E(sub)}</p>
  <div class="results-stats"><span>+{s["xp"]} XP</span><span>Best combo ×{s["best_combo"]}</span>
    <span>Lv {lvl["number"]} · {E(lvl["name"])}</span></div>
  {level_up}
  {mistakes}
  <div class="btn-row center">
    <a class="btn btn-primary" href="{again}">Play again</a>
    <a class="btn btn-ghost" href="#play-review">Review mistakes</a>
    <a class="btn btn-ghost" href="#progress">See progress</a>
  </div>
</section>"""


class OralPage(Page):
    def words_html(self, stim: dict) -> str:
        return "".join(f'<button type="button" class="wchip" data-say="{E(es)}" aria-label="Pronounce {E(es)}">'
                       f'<b lang="es">{E(es)}</b><span>{E(en)}</span></button>' for es, en in stim["hints"])

    def parts(self, stim: dict) -> dict:
        """The pieces the page swaps in when a new image is drawn."""
        return {"id": stim["id"], "theme": stim["theme"], "title": stim["title"],
                "theme_label": Labels.theme(stim["theme"]), "svg": stim["svg"],
                "words_html": self.words_html(stim), "followups": stim["followups"],
                "conversation": stim["conversation"]}

    def render(self, arg: str = "") -> str:
        theme = arg if arg in self.app.bank.themes else None
        stim = self.app.oral.stimulus(theme)
        data = {"timings": stim["timings"], **self.parts(stim)}
        data.pop("svg")
        data.pop("words_html")
        chips = '<button type="button" class="chip active" data-theme="">All themes</button>' + "".join(
            f'<button type="button" class="chip" data-theme="{t.slug}">{t.emoji} {E(t.name)}</button>'
            for t in self.app.bank.themes.values())
        tabs, panels = [], []
        for i, (group, items) in enumerate(stim["starters"].items()):
            sel = "true" if i == 0 else "false"
            tabs.append(f'<button type="button" class="tab" role="tab" id="tab-{i}" aria-controls="panel-{i}" '
                        f'aria-selected="{sel}" data-tab="{i}">{E(group)}</button>')
            lis = "".join(f'<li lang="es">{E(x)}</li>' for x in items)
            panels.append(f'<ul class="starter-list" role="tabpanel" id="panel-{i}" aria-labelledby="tab-{i}"'
                          f'{"" if i == 0 else " hidden"}>{lis}</ul>')
        phases = "".join(f'<li class="phase{" active" if i == 0 else ""}" data-phase="{i}"><b>{E(p["label"])}</b>'
                         f'<small>{p["secs"] // 60}:{p["secs"] % 60:02d}</small></li>'
                         for i, p in enumerate(stim["timings"]["exam"]))
        payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
        return f"""
<div class="page oral" data-scene="{E(stim["id"])}">
  {self.head("Individual oral", "Describe, guess, <em>connect.</em>",
             "Prepare with the picture, present for two minutes, then answer the examiner's questions. New pictures are drawn every time.")}
  <div class="chips rise" id="oral-themes" role="group" aria-label="Theme">{chips}</div>
  <div class="oral-grid">
    <div class="oral-main">
      <figure class="scene-frame glass rise">
        <div class="scene-stack" id="scene-stack"><div class="scene-layer">{stim["svg"]}</div></div>
        <figcaption>
          <span class="scene-title" id="scene-title" lang="es">{E(stim["title"])}</span>
          <span class="chip chip-soft" id="scene-theme">{E(Labels.theme(stim["theme"]))}</span>
          <button type="button" class="btn btn-sm btn-primary" id="new-image">↻ New image</button>
        </figcaption>
      </figure>
      <section class="glass panel rise" style="{self.delay(1)}">
        <h2 class="h3">Useful words <small class="muted">tap to hear</small></h2>
        <div class="word-chips" id="word-chips">{self.words_html(stim)}</div>
      </section>
      <section class="glass panel rise" style="{self.delay(2)}">
        <h2 class="h3">Sentence starters</h2>
        <div class="tabs" role="tablist" aria-label="Sentence starters">{"".join(tabs)}</div>
        {"".join(panels)}
      </section>
    </div>
    <aside class="oral-side">
      <section class="timer-card glass rise" aria-label="Oral timer">
        <div class="seg" role="group" aria-label="Timing">
          <button type="button" class="seg-btn active" data-timing="exam" aria-pressed="true">Exam timing</button>
          <button type="button" class="seg-btn" data-timing="quick" aria-pressed="false">Quick practice</button>
        </div>
        <ol class="phases" id="phases">{phases}</ol>
        <div class="timer">
          <svg class="timer-ring" viewBox="0 0 220 220" aria-hidden="true">
            <defs><linearGradient id="tg" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" style="stop-color:var(--sun)"/><stop offset=".5" style="stop-color:var(--rose)"/>
              <stop offset="1" style="stop-color:var(--plum)"/></linearGradient></defs>
            <circle class="ring-track" cx="110" cy="110" r="96" stroke-width="14"/>
            <circle class="timer-fill" id="timer-fill" cx="110" cy="110" r="96" stroke-width="14" stroke="url(#tg)"
              stroke-dasharray="603.2" stroke-dashoffset="0" transform="rotate(-90 110 110)"/>
          </svg>
          <div class="timer-center"><b id="timer-time" role="timer" aria-live="off">15:00</b><span id="timer-phase">Prepare</span></div>
        </div>
        <div class="timer-controls">
          <button type="button" class="btn btn-primary" id="t-start">▶ Start</button>
          <button type="button" class="btn btn-ghost" id="t-skip" aria-label="Skip to the next phase">⏭ Skip</button>
          <button type="button" class="btn btn-ghost" id="t-reset" aria-label="Reset the timer">↺ Reset</button>
        </div>
      </section>
      <section class="glass panel ask-card rise" style="{self.delay(1)}">
        <h2 class="h3">Examiner questions</h2>
        <p class="muted small" id="ask-stage">Follow-up questions about the picture come first, then general conversation.</p>
        <ol class="asked" id="asked" aria-live="polite"></ol>
        <button type="button" class="btn btn-primary" id="ask-btn">Ask me one →</button>
      </section>
    </aside>
  </div>
  <script type="application/json" id="oral-data">{payload}</script>
</div>"""


class WritePage(Page):
    KIND_LABEL = {"spanglish": "Spanglish", "accent": "Accent", "punctuation": "¿ ¡"}

    def render(self, arg: str = "") -> str:
        chips = "".join(f'<button type="button" class="chip{" active" if t == "email" else ""}" data-type="{t}" '
                        f'aria-pressed="{"true" if t == "email" else "false"}">{E(label)}</button>'
                        for t, label in WritingCoach.TEXT_TYPES.items())
        return f"""
<div class="page write">
  {self.head("Paper 1 coach", "Write it. <em>I'll point.</em>",
             "Choose a text type and write 70–150 words. I never rewrite your text: I mark what to check and explain the rule, so you make the fix.")}
  <div class="chips rise" id="type-chips" role="group" aria-label="Text type">{chips}</div>
  <div class="write-grid">
    <section class="glass panel editor-panel rise" style="{self.delay(1)}">
      <label for="editor" class="h3">Your text</label>
      <textarea id="editor" rows="12" lang="es" spellcheck="false" placeholder="Escribe aquí… (70–150 palabras)"></textarea>
      <div id="meter">{self.meter_html(0)}</div>
      <div class="btn-row"><button type="button" class="btn btn-ghost btn-sm" id="load-example">Load an example with mistakes</button>
        <button type="button" class="btn btn-ghost btn-sm" id="clear-text">Clear</button></div>
    </section>
    <section class="glass panel preview-panel rise" style="{self.delay(2)}">
      <h2 class="h3">Marked-up preview</h2>
      <div class="legend"><span class="lg spanglish">Spanglish</span><span class="lg accent">Accents</span><span class="lg punctuation">¿ ¡</span></div>
      <div class="preview" id="preview" lang="es"><p class="muted">Your text will appear here with the things to check underlined. Hover, tap or tab to a mark to see why.</p></div>
    </section>
  </div>
  <div id="analysis"></div>
</div>"""

    @staticmethod
    def meter_html(words: int) -> str:
        lo, hi = WritingCoach.TARGET
        scale = 200
        pos = min(100, words / scale * 100)
        state = "empty" if words == 0 else "short" if words < lo else "long" if words > hi else "ok"
        label = {"empty": "Start writing", "short": f"{lo - words} more to reach {lo}",
                 "ok": "In the target zone", "long": f"{words - hi} over {hi}"}[state]
        return (f'<div class="meter {state}"><div class="meter-head"><b>{words}</b> words <span>{E(label)}</span></div>'
                f'<div class="meter-track" role="meter" aria-valuemin="0" aria-valuemax="{scale}" aria-valuenow="{words}" '
                f'aria-label="Word count"><span class="zone" style="left:{lo / scale * 100}%;width:{(hi - lo) / scale * 100}%"></span>'
                f'<span class="needle" style="left:{pos}%"></span></div>'
                f'<div class="meter-scale"><span>0</span><span style="left:{lo / scale * 100}%">{lo}</span>'
                f'<span style="left:{hi / scale * 100}%">{hi}</span><span>{scale}</span></div></div>')

    def preview_html(self, a: dict) -> str:
        if not a["words"]:
            return '<p class="muted">Your text will appear here with the things to check underlined.</p>'
        out = []
        for seg in a["segments"]:
            text = E(seg["text"]).replace("\n", "<br>")
            if seg["issue"] is None:
                out.append(text)
                continue
            issue = a["issues"][seg["issue"]]
            out.append(f'<mark class="mk {issue["kind"]}" tabindex="0" aria-describedby="tip-{seg["issue"]}">{text}'
                       f'<span class="tip" role="tooltip" id="tip-{seg["issue"]}"><b>{E(issue["title"])}</b>'
                       f'{issue["message"]}</span></mark>')
        return "".join(out)

    def panel_html(self, a: dict) -> str:
        if not a["words"]:
            return ""
        counts = a["counts"]
        count_chips = "".join(
            f'<span class="count-chip {k}"><b>{counts.get(k, 0)}</b> {E(label)}</span>'
            for k, label in self.KIND_LABEL.items())
        conv = "".join(
            f'<li class="{"ok" if c["ok"] else "todo"}"><span class="tick" aria-hidden="true">{"✓" if c["ok"] else "○"}</span>'
            f'<div><b>{E(c["label"])}</b>{"" if c["ok"] else "<small>" + E(c["hint"]) + "</small>"}</div>'
            f'<span class="sr-only">{"done" if c["ok"] else "to do"}</span></li>'
            for c in a["conventions"])
        con = a["connectors"]
        found = "".join(
            f'<span class="cchip"><small>{E(con["labels"][f])}</small>{E(", ".join(words))}</span>'
            for f, words in con["found"].items()) or '<p class="muted small">No connectors yet.</p>'
        missing = "".join(f'<li><b>{E(con["labels"][f])}</b>: try <i lang="es">{E(con["suggest"][f])}</i></li>'
                          for f in con["missing"][:4])
        missing_html = f'<ul class="tips">{missing}</ul>' if missing else ""
        overuse = "".join(f'<li>You use <b lang="es">{E(o["word"])}</b> {o["count"]}×. Upgrade: '
                          f'<i lang="es">{E(o["try"])}</i></li>' for o in con["overuse"])
        overuse_html = f'<ul class="tips warn">{overuse}</ul>' if overuse else ""
        t = a["tenses"]
        tense_chips = "".join(f'<span class="tchip on"><b>{E(t["names"][k])}</b><small lang="es">'
                              f'{E(", ".join(v[:3]))}</small></span>' for k, v in t["found"].items())
        tense_chips += "".join(f'<span class="tchip off">{E(name)}</span>'
                               for k, name in t["names"].items() if k not in t["found"])
        reg = a["register"]
        reg_html = (f'<p class="reg {reg["status"]}"><b>{E(reg["label"])}</b></p>'
                    + (f'<p class="warn-line">{E(reg["warning"])}</p>' if reg["warning"] else ""))
        rep = "".join(f'<li><b lang="es">{E(r["word"])}</b> × {r["count"]}'
                      + (f' <i lang="es">→ {E(r["try"])}</i>' if r["try"] else "") + "</li>"
                      for r in a["repeated"])
        rep_html = f'<ul class="tips">{rep}</ul>' if rep else '<p class="muted small">No word repeated too often.</p>'
        score = a["score"]
        verdict = ("Exam-ready" if score >= 85 else "Nearly there" if score >= 70 else
                   "Getting there" if score >= 50 else "Keep fixing")
        return f"""
<div class="analysis-grid">
  <section class="glass panel score-panel rise">
    <div class="score-ring small">{self.ring(score, 120, 11, "ring", "rg-write")}
      <div class="ring-label"><b data-count="{score}">0</b><small>/ 100</small></div></div>
    <div><h3 class="h3">{E(verdict)}</h3><p class="muted small">A guide, not an IB mark. Fix the marks, then aim for range.</p>
      <div class="count-chips">{count_chips}</div></div>
  </section>
  <section class="glass panel rise" style="{self.delay(1)}">
    <h3 class="h3">Conventions: {E(a["type_label"])}</h3><ul class="checklist">{conv}</ul>
  </section>
  <section class="glass panel rise" style="{self.delay(2)}">
    <h3 class="h3">Connectors</h3><div class="cchips">{found}</div>{overuse_html}{missing_html}
  </section>
  <section class="glass panel rise" style="{self.delay(3)}">
    <h3 class="h3">Tenses</h3><div class="tchips">{tense_chips}</div><p class="small">{E(t["tip"])}</p>
    <h3 class="h3">Register</h3>{reg_html}
    <h3 class="h3">Repeated words</h3>{rep_html}
  </section>
</div>"""


class ProgressPage(Page):
    def render(self, arg: str = "") -> str:
        memory = self.app.memory
        s = self.summary()
        lvl: Level = s["level"]
        acc = "—" if s["accuracy"] is None else s["accuracy"]
        acc_attr = "" if s["accuracy"] is None else f' data-count="{s["accuracy"]}"'
        # calendar
        weeks = memory.activity(12)
        cols = "".join(
            '<div class="cal-col">' + "".join(
                f'<span class="cal-cell l{c["level"]}{" future" if c["future"] else ""}{" today" if c["today"] else ""}" '
                f'title="{c["date"]}: {self.plural(c["count"], "activity", "activities")}"></span>' for c in col) + "</div>"
            for col in weeks)
        # themes heatmap
        by_theme = memory.breakdown("theme")
        heat = []
        themes = list(self.app.bank.themes.values()) + ([self.app.bank.mine] if self.app.bank.mine.words else [])
        for i, t in enumerate(themes):
            right, total = by_theme.get(t.slug, (0, 0))
            pct = round(100 * right / total) if total else None
            label = "No answers yet" if pct is None else f"{right} / {total} correct"
            heat.append(f'<a class="heat glass rise" href="{self.mode_link("theme:" + t.slug)}" '
                        f'style="--g:{self.grad(t)};--a:{0 if pct is None else 0.18 + 0.6 * pct / 100:.2f};{self.delay(i, 50)}">'
                        f'<span class="heat-emoji" aria-hidden="true">{t.emoji}</span><b>{E(t.name)}</b>'
                        f'<span class="heat-pct">{"—" if pct is None else f"{pct}%"}</span><small>{label}</small></a>')
        grammar = by_theme.get("grammar")
        # skills
        by_skill = memory.breakdown("skill")
        bars = []
        for k in Labels.SKILLS:
            right, total = by_skill.get(k, (0, 0))
            pct = round(100 * right / total) if total else 0
            bars.append(f'<li><div class="sb-head"><span>{Labels.SKILL_EMOJI[k]} {E(Labels.skill(k))}</span>'
                        f'<b>{"—" if not total else f"{pct}%"}</b></div><span class="bar"><i style="--w:{pct}%"></i></span>'
                        f'<small>{self.plural(total, "answer")}</small></li>')
        # weak patterns
        weak = sorted(memory.weakness_scores().items(), key=lambda kv: -kv[1])[:6]
        if weak:
            pats = "".join(f'<li><span>{E(Labels.pattern(p))}</span><span class="meter-mini"><i style="--w:{round(sc * 100)}%">'
                           f'</i></span><small>{memory.misses(p)} missed</small></li>' for p, sc in weak)
            patterns = (f'<ul class="patterns">{pats}</ul>'
                        f'<a class="btn btn-primary" href="#play-review">Drill these now →</a>')
        else:
            patterns = '<p class="muted">No patterns yet. Keep playing and I\'ll spot what trips you up.</p>'
        # recent mistakes
        recent = memory.recent_mistakes(8)
        if recent:
            rec = "".join(f'<li><span class="m-q" lang="es">{QuizPage.big_html(a.big)}</span>'
                          f'<span class="m-a"><s>{E(a.chosen)}</s> → <b>{E(a.answer)}</b></span></li>' for a in recent)
            recent_html = f'<ul class="recent">{rec}</ul>'
        else:
            recent_html = '<p class="muted">No mistakes yet.</p>'
        insights = "".join(f"<li>{E(t)}</li>" for t in memory.insights())
        grammar_line = ""
        if grammar:
            grammar_line = (f'<p class="muted small">Grammar questions (ser/estar, verbs, false friends): '
                            f'{grammar[0]} / {grammar[1]} correct.</p>')
        return f"""
<div class="page progress">
  {self.head("Progress", "Look how far <em>you've come.</em>", "",
             '<p class="saved-note"><span aria-hidden="true">💾</span> Saved in this browser on this device.</p>')}
  <div class="stats-grid">
    <section class="level-card glass rise">
      <div class="level-badge" aria-hidden="true">{lvl.number}</div>
      <div class="level-copy"><p class="eyebrow">Level {lvl.number}</p><h2>{E(lvl.name)}</h2>
        <span class="bar big"><i style="--w:{round(lvl.progress * 100)}%"></i></span>
        <small><b data-count="{lvl.xp}">0</b> XP · {lvl.to_next} XP to level {lvl.number + 1}</small></div>
    </section>
    <div class="tile glass rise" style="{self.delay(1)}"><span aria-hidden="true">🔥</span><b data-count="{s['streak']}">0</b><small>day streak</small></div>
    <div class="tile glass rise" style="{self.delay(2)}"><span aria-hidden="true">✍️</span><b data-count="{s['answers']}">0</b><small>answers</small></div>
    <div class="tile glass rise" style="{self.delay(3)}"><span aria-hidden="true">🎯</span><b{acc_attr}>{"0" if acc_attr else acc}</b><small>% accuracy</small></div>
  </div>
  <section class="glass panel rise">
    <div class="section-head"><h2 class="h3">Activity <small class="muted">last 12 weeks</small></h2>
      <div class="cal-legend" aria-hidden="true">Less<span class="cal-cell l0"></span><span class="cal-cell l1"></span><span class="cal-cell l2"></span><span class="cal-cell l3"></span><span class="cal-cell l4"></span>More</div></div>
    <div class="cal-wrap"><div class="cal-days" aria-hidden="true"><span>Mon</span><span></span><span>Wed</span><span></span><span>Fri</span><span></span><span>Sun</span></div>
      <div class="cal" role="img" aria-label="Activity calendar: {self.plural(memory.active_days(), 'active day')}">{cols}</div></div>
    <ul class="insights">{insights}</ul>
  </section>
  <section class="section">
    <h2 class="h3 rise">Themes</h2>
    <div class="heat-grid">{"".join(heat)}</div>
    {grammar_line}
  </section>
  <div class="two-col">
    <section class="glass panel rise"><h2 class="h3">Skills</h2><ul class="skill-bars">{"".join(bars)}</ul></section>
    <section class="glass panel rise" style="{self.delay(1)}"><h2 class="h3">Patterns you keep missing</h2>{patterns}</section>
  </div>
  <section class="glass panel rise"><h2 class="h3">Recent mistakes</h2>{recent_html}</section>
  <section class="glass panel danger rise">
    <div><h2 class="h3">Your data</h2>
      <p class="muted small">Download a backup to move your progress to another browser, or start again from zero. Your own words are kept when you reset.</p></div>
    <div class="btn-row">
      <button type="button" class="btn btn-ghost" id="export-btn">⬇ Download backup</button>
      <label class="btn btn-ghost" for="import-file">⬆ Restore backup</label>
      <input type="file" id="import-file" accept=".json,application/json" class="sr-only">
      <button type="button" class="btn btn-danger" id="reset-btn">Reset all progress</button>
    </div>
    <p class="form-msg" id="data-msg" role="status" aria-live="polite"></p>
  </section>
</div>"""


class Router:
    """Maps page names to Page classes."""

    PAGES = {"home": HomePage, "vocab": VocabPage, "theme": ThemePage, "mywords": MyWordsPage,
             "quiz": QuizPage, "oral": OralPage, "write": WritePage, "progress": ProgressPage}

    def __init__(self, app):
        self.app = app

    def page(self, name: str) -> Page:
        return self.PAGES.get(name, HomePage)(self.app)

    def render(self, name: str, arg: str = "") -> str:
        return self.page(name).render(arg or "")
