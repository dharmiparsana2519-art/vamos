"""Play the ¡Vamos! quiz in the IDLE shell: open this file in IDLE and press F5.

It uses exactly the same Python classes as the website (QuizEngine, MistakeMemory…),
so explanations, review mode and levels all work the same way.
Progress from the shell is saved in shell_progress.json next to this file.
"""
from __future__ import annotations

import html
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "python"))

from core.memory import Clock, Labels, MistakeMemory  # noqa: E402
from core.quiz import QuizEngine  # noqa: E402
from core.vocab import BANK  # noqa: E402


class ShellQuiz:
    """A text version of the quiz with a mode menu, numbered answers and full explanations."""

    SAVE_FILE = os.path.join(HERE, "shell_progress.json")
    LINE = "─" * 60

    def __init__(self):
        offset = -time.localtime().tm_gmtoff // 60   # same convention as JavaScript's getTimezoneOffset()
        self.memory = MistakeMemory(Clock(offset))
        self.load()
        self.engine = QuizEngine(BANK, self.memory)

    # -- saving --------------------------------------------------------------
    def load(self) -> None:
        try:
            with open(self.SAVE_FILE, encoding="utf-8") as f:
                self.memory.import_json(f.read())
        except OSError:
            pass

    def save(self) -> None:
        try:
            with open(self.SAVE_FILE, "w", encoding="utf-8") as f:
                f.write(self.memory.export_json())
        except OSError:
            print("(Couldn't save your progress to a file.)")

    # -- text helpers --------------------------------------------------------------
    @staticmethod
    def plain(text: str) -> str:
        """Explanations contain light HTML (<b>, <i>, <br>); strip it for the shell."""
        text = re.sub(r"<br\s*/?>", "\n", text or "")
        return html.unescape(re.sub(r"<[^>]+>", "", text))

    @staticmethod
    def ask(prompt: str, valid: list[str]) -> str:
        while True:
            try:
                answer = input(prompt).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return "q"
            if answer in valid:
                return answer
            print(f"  Please type one of: {', '.join(valid)}")

    # -- menu ------------------------------------------------------------------------
    def menu(self) -> str | None:
        due = len(self.memory.due_mistakes())
        level = self.memory.level()
        print(f"\n{self.LINE}\n¡Vamos! · Level {level.number} {level.name} · {level.xp} XP · {due} to review\n{self.LINE}")
        print("  1  Mixed practice")
        print(f"  2  Review my mistakes ({due} due)")
        print("  3  By theme")
        print("  4  By skill")
        print("  q  Quit")
        choice = self.ask("Choose: ", ["1", "2", "3", "4", "q"])
        if choice == "1":
            return "mix"
        if choice == "2":
            return "review"
        if choice == "3":
            themes = list(BANK.themes.values())
            for i, t in enumerate(themes, 1):
                print(f"  {i}  {t.name} ({t.name_es})")
            pick = self.ask("Theme: ", [str(i) for i in range(1, len(themes) + 1)] + ["q"])
            return None if pick == "q" else f"theme:{themes[int(pick) - 1].slug}"
        if choice == "4":
            skills = list(Labels.SKILLS)
            for i, s in enumerate(skills, 1):
                print(f"  {i}  {Labels.skill(s)}")
            pick = self.ask("Skill: ", [str(i) for i in range(1, len(skills) + 1)] + ["q"])
            return None if pick == "q" else f"skill:{skills[int(pick) - 1]}"
        return None

    # -- one round ------------------------------------------------------------------------
    def play(self, mode: str) -> None:
        session = self.engine.start(mode)
        print(f"\n{session.title}")
        if session.note:
            print(f"({session.note})")
        result = {}
        for i, q in enumerate(session.questions):
            print(f"\n{self.LINE}\nQuestion {i + 1} of {session.total} · {Labels.skill(q.skill)}")
            print(q.prompt)
            print(f"\n    {q.big.replace('___', '_____')}")
            if q.sub:
                print(f"    ({q.sub})")
            print()
            for n, option in enumerate(q.options, 1):
                print(f"  {n}  {option}")
            pick = self.ask("Your answer: ", [str(n) for n in range(1, len(q.options) + 1)] + ["q"])
            if pick == "q":
                print("Round stopped.")
                self.save()
                return
            choice = q.options[int(pick) - 1]
            result = self.engine.check(session.sid, i, choice)
            if result["correct"]:
                print("\n  ✓ ¡Correcto!")
            else:
                print(f"\n  ✗ Not quite. Why '{choice}' is wrong:")
                print(f"    {self.plain(result['why_wrong'])}")
            print(f"  Why '{result['answer']}' is right:")
            print(f"    {self.plain(result['why_right'])}")
            if result.get("example") and result["example"].get("es"):
                ex = result["example"]
                print(f"  Example: {ex['es']}" + (f"  ({ex['en']})" if ex.get("en") else ""))
            if result.get("alert"):
                print(f"  🧩 {result['alert']}")
            if result.get("combo", 0) >= 2:
                print(f"  🔥 Combo ×{result['combo']}")
            self.save()
        summary = result.get("summary", {})
        lvl = summary.get("level", {})
        print(f"\n{self.LINE}\nScore: {summary.get('score')}/{summary.get('total')} ({summary.get('pct')}%)  ·  "
              f"+{summary.get('xp')} XP  ·  Level {lvl.get('number')} {lvl.get('name')}")
        if summary.get("level_up"):
            print("⭐ Level up!")
        for m in summary.get("mistakes", []):
            print(f"  ✗ {m['big']}: you said '{m['chosen']}', answer '{m['answer']}'")

    def run(self) -> None:
        print("¡Hola! Welcome to the ¡Vamos! shell quiz. Type the number of your answer and press Enter.")
        while True:
            mode = self.menu()
            if mode is None:
                print("¡Hasta luego!")
                return
            self.play(mode)
            again = self.ask("\nPlay again? (y/n): ", ["y", "n", "yes", "no", "q"])
            if again not in ("y", "yes"):
                print("¡Hasta luego! Your progress is saved.")
                return


if __name__ == "__main__":
    ShellQuiz().run()
