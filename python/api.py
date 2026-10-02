"""VamosApp: the single facade the JavaScript shell talks to.

Every public method returns a string, either HTML or JSON text, so the
JavaScript side never has to understand Python objects. All of the logic
(questions, answers, scoring, explanations, analysis) stays here in Python.
"""
from __future__ import annotations

import json

from core.memory import Clock, MistakeMemory
from core.mywords import MyWords
from core.oral import OralCoach
from core.quiz import QuizEngine
from core.vocab import BANK
from core.writing import WritingCoach
from views import MyWordsPage, OralPage, QuizPage, Router, WritePage


class VamosApp:
    """Facade over the vocabulary bank, memory, quiz engine, oral and writing coaches."""

    def __init__(self, tz_offset_minutes: int = 0, saved_state: str | None = None):
        self.clock = Clock(tz_offset_minutes)
        self.bank = BANK
        self.memory = MistakeMemory(self.clock)
        self.restored = bool(saved_state) and self.memory.import_json(saved_state)
        self.mywords = MyWords(self.memory, self.bank)
        self.mywords.refresh()
        self.engine = QuizEngine(self.bank, self.memory)
        self.oral = OralCoach()
        self.writer = WritingCoach()
        self.router = Router(self)

    @staticmethod
    def _json(data) -> str:
        return json.dumps(data, ensure_ascii=False)

    # -- pages ----------------------------------------------------------------
    def render(self, page: str, arg: str = "") -> str:
        return self.router.render(page or "home", arg or "")

    # -- quiz -----------------------------------------------------------------
    def quiz_start(self, mode: str) -> str:
        session = self.engine.start(mode)
        public = session.public()
        return self._json({"sid": session.sid, "total": session.total, "mode": session.mode,
                           "html": QuizPage(self).play_html(public)})

    def quiz_answer(self, sid: str, index: int, choice: str) -> str:
        result = self.engine.check(str(sid), int(index), str(choice))
        page = QuizPage(self)
        out = {k: result.get(k) for k in ("correct", "answer", "combo", "score", "answered", "total", "done", "error")}
        out["feedback_html"] = page.feedback_html(result)
        if result.get("done"):
            summary = result["summary"]
            out["pct"] = summary["pct"]
            out["results_html"] = page.results_html(summary)
        return self._json(out)

    # -- oral -----------------------------------------------------------------
    def oral_stimulus(self, theme: str = "", exclude: str = "") -> str:
        theme = theme if theme in self.bank.themes else None
        stim = self.oral.stimulus(theme, exclude or None)
        return self._json(OralPage(self).parts(stim))

    # -- writing --------------------------------------------------------------
    def write_check(self, text: str, text_type: str = "email") -> str:
        analysis = self.writer.analyse(text or "", text_type or "email")
        page = WritePage(self)
        return self._json({"words": analysis["words"], "score": analysis["score"],
                           "meter_html": page.meter_html(analysis["words"]),
                           "preview_html": page.preview_html(analysis),
                           "panel_html": page.panel_html(analysis)})

    def write_example(self) -> str:
        return WritingCoach.EXAMPLE

    # -- words ------------------------------------------------------------------
    def set_known(self, key: str, on: bool) -> str:
        word = self.bank.find(key)
        if word is None:
            return self._json({"ok": False})
        self.memory.set_known(key, bool(on))
        theme = self.bank.theme_of(word)
        known = self.memory.known_words()
        count = theme.known_count(known) if theme else 0
        total = len(theme.words) if theme else 0
        return self._json({"ok": True, "known": key in known, "count": count, "total": total,
                           "complete": bool(on) and total > 0 and count == total})

    def _words_payload(self, ok: bool, message: str) -> str:
        page = MyWordsPage(self)
        return self._json({"ok": ok, "message": message, "count": self.mywords.count(),
                           "list_html": page.list_html(), "actions_html": page.actions_html()})

    def add_word(self, es: str, en: str, gender: str = "auto", example: str = "") -> str:
        ok, message, _ = self.mywords.add(es, en, gender or "auto", example or "")
        return self._words_payload(ok, message)

    def add_words_bulk(self, text: str) -> str:
        result = self.mywords.add_bulk(text or "")
        return self._words_payload(result["added"] > 0, result["message"])

    def remove_word(self, key: str) -> str:
        ok = self.mywords.remove(key)
        return self._words_payload(ok, "Removed." if ok else "That word was already gone.")

    # -- state --------------------------------------------------------------------
    def reset(self) -> str:
        self.memory.reset()
        return self._json({"ok": True})

    def export_state(self) -> str:
        return self.memory.export_json()

    def import_state(self, raw: str) -> str:
        ok = self.memory.import_json(raw)
        if ok:
            self.mywords.refresh()
        return self._json({"ok": ok, "message": "Backup restored." if ok else
                           "That file isn't a ¡Vamos! backup, so nothing was changed."})

    def state_info(self) -> str:
        level = self.memory.level()
        return self._json({"attempts": len(self.memory.attempts), "known": len(self.memory.known_words()),
                           "mine": self.mywords.count(), "xp": self.memory.xp(), "level": level.as_dict(),
                           "streak": self.memory.streak(), "due": len(self.memory.due_mistakes()),
                           "restored": self.restored})


def create_app(tz_offset_minutes: int = 0, saved_state: str | None = None) -> VamosApp:
    """Build the app. JavaScript passes Date.getTimezoneOffset() and the saved JSON (or null)."""
    return VamosApp(tz_offset_minutes, saved_state)
