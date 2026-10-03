# ¡Vamos! 2.0 · IB Spanish ab initio study site

A free, static study website for **IB Diploma Spanish ab initio (SL)** students sitting their exams in **May 2027**.

- **Vocabulary:** 693 words across the five IB themes and their 20 prescribed topics, as 3D flip cards. About 85 of them come with an example, a translation and a tip. There's also a table of 15 false friends.
- **Quiz with a mistake memory:** every option of every question has its own explanation. After a wrong answer you see why your choice is wrong *and* why the right answer is right. Patterns you keep missing (e.g. "-ma words from Greek") are spotted, and **Review mode** drills them.
- **My words:** add your own class vocabulary, one word at a time or by pasting a whole list. There's no practical limit (5,000 words). Your words become flip cards and quiz questions.
- **Individual oral:** a new procedurally drawn picture every time, useful words you can tap to hear, sentence starters, examiner questions read aloud, and a real exam timer (15 min prepare · 2 present · 5 follow-up · 5 conversation).
- **Paper 1 writing coach:** marks Spanglish, missing accents and missing ¿ ¡ in your text, and checks connectors, tenses, register, repeated words and the conventions of eight text types. **It never rewrites your text: it only points.**
- **Progress:** level and XP, streak, a 12-week activity calendar, a heatmap per theme, skill bars, the patterns you keep missing and your recent mistakes.

Almost everything is **Python** (object-oriented, standard library only), running in your browser through **Pyodide**. JavaScript is a thin shell. Progress is saved in your browser (`localStorage`), so there's no account, server or database.

---

## Folder

```
vamos-site/
├── index.html          the whole page: <head>, inline CSS, page shell, inline JS
├── .nojekyll           tells GitHub Pages not to drop python/core/__init__.py
├── py/                 self-hosted Pyodide 0.26.4 (pyodide.js, .asm.js, .asm.wasm, stdlib, lock file)
├── python/
│   ├── api.py          VamosApp: the only object JavaScript talks to
│   ├── views.py        one Page class per screen (renders HTML)
│   └── core/
│       ├── vocab.py      Word, Theme, FalseFriend, VocabularyBank, WordListParser (+ the rich words)
│       ├── wordlists.py  compact word lists (about 100 per theme)
│       ├── mywords.py    MyWords, BulkWordParser (the learner's own words)
│       ├── grammar.py    GenderRules, Person, SerEstar, Conjugator, Verb, ChoiceSet
│       ├── memory.py     Attempt, Clock, Labels, Level, MistakeMemory
│       ├── quiz.py       Question, the QuestionType hierarchy, QuizSession, QuizEngine
│       ├── oral.py       Scene, Palette, SceneArtist, OralCoach
│       └── writing.py    Issue, the Rule hierarchy, TenseDetector, WritingCoach
├── serve.py            run the site locally from IDLE (F5)
├── play_in_shell.py    the quiz as a text game in the IDLE shell (F5)
└── README.md
```

The development sources live next to this folder on your computer, in `../dev/`. They aren't needed online, so they aren't part of the deployed site:

- `src/style.css`, `src/app.js` and `src/shell.html` are the CSS, JavaScript and HTML template.
- `build.py` inlines those sources into `index.html`.
- `tests/` holds the unit and browser tests.

---

## Run it on your computer (IDLE)

1. Open **`serve.py`** in IDLE and press **F5**.
2. Your browser opens `http://localhost:8000/`. If port 8000 is busy, the next free port is used.
3. Leave the IDLE shell open while you study. Press **Ctrl+C** in the shell (or close it) to stop.

> Double-clicking `index.html` won't work: browsers block Python files from loading over `file://`.
> The page detects this and tells you to use `serve.py`. You can also run
> `python -m http.server` inside `vamos-site/` and open `http://localhost:8000`.

**Quiz in the shell:** open **`play_in_shell.py`** in IDLE and press **F5**. Choose a mode (Mixed, Review my mistakes, By theme or By skill), type the number of your answer, and read both explanations. Score, XP and level are shown at the end. Shell progress is saved in `shell_progress.json` next to the script. Both scripts need Python 3.9 or newer and only use the standard library.

---

## Put it online for free

The site is just files, so any static host works. Upload the **`vamos-site`** folder as it is.

### Netlify (easiest)
1. Go to <https://app.netlify.com/drop>.
2. Drag the `vamos-site` folder onto the page. You get a URL in a few seconds. Sign in if you want to keep the site and choose its name.

### GitHub Pages
1. Create a new public repository on GitHub, e.g. `vamos`.
2. Upload the **contents** of `vamos-site/` (including `.nojekyll`, `py/` and `python/`) to the root of the repository, using **Add file → Upload files** or `git push`.
3. In the repository, open **Settings → Pages**. Under *Build and deployment*, choose **Deploy from a branch**, then branch **main** and folder **/ (root)**. Save.
4. After a minute the site is live at `https://<your-username>.github.io/vamos/`.

`.nojekyll` matters: without it, GitHub's Jekyll step drops files whose names start with `_`, such as `__init__.py`.

### Cloudflare Pages
1. In the Cloudflare dashboard, open **Workers & Pages → Create → Pages → Upload assets**.
2. Name the project and drag in the `vamos-site` folder. Deploy.

The first visit downloads about 6 MB (compressed) of Python runtime, which the browser then caches. `pyodide.asm.wasm` must be served as `application/wasm`; all three hosts do this automatically.

---

## Add or change words

### Compact lists: `python/core/wordlists.py`

Each theme has a block of lines in the form `spanish | english | kind`. A `## Topic` heading sets the topic for the lines below it.

```
## Climate
lluvia | rain | f
huracán | hurricane | m
derechos humanos | human rights | mpl
nevar | to snow | v
soleado | sunny | adj
a menudo | often | adv
hace frío | it's cold (weather) | phr
```

Kind codes:

| Code | Meaning |
|---|---|
| `m` / `f` | masculine / feminine noun |
| `mpl` / `fpl` | plural-only noun (los deberes, las vacaciones) |
| `v` | verb |
| `adj` | adjective |
| `adv` | adverb |
| `phr` | fixed phrase |

- Write nouns **without** the article: the gender code supplies it. The article is worked out for you (el agua, el aula and el hambre take *el* because of the stressed a-).
- Topics must be one of that theme's four IB topics.
- A Spanish word already in the bank is skipped. A malformed line raises a clear `ValueError` telling you the line number.

### Rich words with an example and a tip: `python/core/vocab.py`

Add a `W(...)` line to `BankBuilder.RICH[theme]`:

```python
W("sequía", "drought", "f", "Climate",
  "La sequía es un problema grave en el sur de España.", "Drought is a serious problem in the south of Spain.",
  "Say it in three syllables: se-quí-a."),
```

Add false friends to `BankBuilder.FALSE_FRIENDS`. Then run the unit tests (`python3 ../dev/tests/test_core.py`). They check for duplicates, topics, gender rules and every quiz mode.

### Your own words (inside the site)

Use **Vocab → My words**, or **＋ Add words**. When you paste a list, each line can use `=`, `-`, `–`, `:`, `,` or a tab as the separator:

```
el perro = dog
la casa - house
gato: cat (m)
las gafas, glasses
nube	cloud (f)
```

`el / la / los / las / un / una` sets the gender (and plural). You can also add `(m)`, `(f)`, `(mpl)` or `(fpl)` on either side. Lines it can't read are reported, e.g. *"Added 6 words. 1 line skipped (no separator): '…'"*.

---

## How it works

1. `index.html` shows a loading screen and loads `py/pyodide.js`.
2. JavaScript calls `loadPyodide({indexURL: "py/"})`. No CDN is used at runtime.
3. It fetches every file in `python/`, writes it into Pyodide's virtual filesystem under `/app`, adds `/app` to `sys.path`, and runs `from api import create_app`.
4. `create_app(tz_offset_minutes, saved_state)` builds **one** `VamosApp`. JavaScript passes `Date.getTimezoneOffset()`, because Pyodide's clock is UTC, and the JSON saved in `localStorage` under `vamos-progress-v1`.
5. From then on, JavaScript only:
   - calls `VamosApp` methods, which all return HTML or JSON text, and swaps the HTML into the page;
   - binds events and runs animations, timers and confetti;
   - speaks Spanish (`speechSynthesis`, es-ES, rate 0.9, only after a click);
   - saves `export_state()` after every answer, word toggle, word add or remove, and reset.

   All storage calls are wrapped in `try/catch`, so private browsing still works. There is no quiz logic, scoring or explanation text in JavaScript.

Routing uses hash tokens: `#home`, `#vocab`, `#theme-planet`, `#mywords`, `#quiz`, `#play-review`, `#play-mix`, `#play-theme.planet`, `#play-skill.gender`, `#oral`, `#write`, `#progress`.

The quiz session, including the answers, stays in Python. The page only ever receives `Question.public()`, which has no answer and no explanations.

---

## Developing

```bash
python3 dev/build.py                 # after editing dev/src/*: rebuild vamos-site/index.html
python3 dev/tests/test_core.py       # 46 unit checks, plain Python, no browser
pip install playwright && python -m playwright install chromium webkit firefox
python3 dev/tests/test_browser.py    # 13 end-to-end tests in Chromium
VAMOS_BROWSERS=chromium,webkit,firefox python3 dev/tests/test_browser.py
```

`build.py` also writes the list of `.py` files the browser must fetch and a build id that busts caches after each deploy. The Python files in `vamos-site/python/` are edited in place; no build step is needed for them except re-running `build.py` to refresh the cache id.

---

## Class and method reference

### `python/core/vocab.py`
| Class / function | Members |
|---|---|
| **`Spelling`**: Spanish spelling knowledge | `strip_accents(text)` removes accents but keeps ñ · `slug(text)` makes a stable readable id · `syllables(word)` gives a rough syllable count · `_last_vowel(word)` finds the index of the last vowel · `plural_of(word)` pluralises one word (canción → canciones, examen → exámenes, país → países) · `_drop_accent_unless_hiatus(word, i)` handles plural accent changes · `plural_phrase(phrase)` pluralises up to the first function word (fin de semana → fines de semana) |
| **`Word`** (frozen dataclass): one vocabulary item | `head` is the first word, lower-cased, and decides the article · `is_noun` · `plural` · `article` is el/la/los/las, including el agua · `display` is the article plus the word · `key` is a stable id, `u-` for custom words · `label` is the article or the word type, shown on the flip card · `has_example` |
| **`Theme`** (dataclass): an IB theme or "My words" | `known_count(known)` counts the words marked known · `gradient()` returns the CSS gradient from the two theme colours |
| **`FalseFriend`** (frozen dataclass) | `es`, `meaning`, `trap`, `note` |
| **`WordListParser`**: parses the compact lists | `parse(text)` reads `spanish \| english \| kind` lines with `## Topic` headings and raises `ValueError` on bad lines · `make(es, en, code, topic, …)` builds a Word from a kind code |
| `W(...)` | Tiny constructor used for the hand-written rich words |
| **`VocabularyBank`**: themes, false friends and `mine` | `themes` · `add_theme(theme)` · `theme(slug)` (also resolves `"mine"`) · `extend_theme(slug, words)` (skips Spanish words already in the bank) · `set_mine(words)` · `false_friends` · `add_false_friend(ff)` (ignores duplicates) · `all_words(include_mine=True)` · `find(key)` · `theme_of(word)` · `nouns()` · `word_of_the_day(date)` (built-in words only, prefers rich words) · `total()` |
| **`BankBuilder`**: theme metadata, rich words and false friends | `build()` returns the populated bank; the module-level `BANK = BankBuilder.build()` runs at import |

### `python/core/wordlists.py`
| | |
|---|---|
| `LISTS` | Dict of theme slug → compact word list (about 100 words per theme) |

### `python/core/grammar.py`
| Class | Members |
|---|---|
| **`ChoiceSet`** (dataclass) | `answer`, `options`, `explanations` (option → why it's wrong), `correct_expl`, `pattern` |
| **`GenderRules`**: why a noun has its article | `RULES` (tag → explanation) · `_candidate(word)` applies the rules in order: plural, stressed a-, Greek -ma, masculine -a, feminine -o, shortened words, -dad/-tad/-tud, -ción/-sión, -umbre, -aje, -or, -o, -a, memorise · `rule_for(word)` returns the tag, falling back to *memorise* if a rule would mislead (la flor) · `explain(word)` · `gender_name(word)` |
| **`Person`** (frozen dataclass): yo / tú / él / nosotros / ellos | `all()` · `get(code)` · `neighbour(code)` gives a plausible wrong person for distractors · `subject(code, rng)` gives a sample subject (Mis padres, Mi amigo y yo…) |
| **`SerEstarItem`** (dataclass) | A gap-fill sentence with its verb, person, reason and an optional note · `filled` is the sentence with the answer filled in |
| **`SerEstar`** | `FORMS`, `REASONS` (origin, profession, characteristic, time, event, identity, location, emotion, condition, progressive), `ITEMS` (31 sentences) · `other(verb)` · `choices(item)` gives four options (right; other verb; wrong person; both wrong), each explained |
| **`Verb`** (dataclass) | `infinitive`, `en`, `frame` · `group` (ar/er/ir) · `stem` |
| **`Conjugator`**: regular present tense | `ending(group, person)` · `conjugate(verb, person)` · `find(infinitive)` · `verbs_in_group(group)` · `wrong_groups(group, person)` puts the most tempting slip first (vivemos) · `rule(verb, person)` returns "viv + es = vives" · `choices(verb, person, rng)` gives four explained options |

### `python/core/memory.py`
| Class | Members |
|---|---|
| **`Attempt`** (dataclass): one answer | `to_row()` / `from_row(row)` for compact storage |
| **`Clock`**: local dates (Pyodide is UTC) | `now()` · `local(ts)` · `date_of(ts)` · `today()` · `key(date)` |
| **`Labels`**: friendly names | `skill(s)` · `pattern(p)` turns "gender:greek-ma" into "-ma words from Greek" · `theme(slug)` |
| **`Level`** (frozen dataclass) | `number`, `name`, `progress`, `to_next`, `xp` · `threshold(n)` = 60·(n−1)² · `from_xp(xp)` (Principiante → Explorador → Viajero → Conversador → Hablante → Maestro) · `as_dict()` |
| **`MistakeMemory`**: attempts, known words, own words | `attempts` · `own_words` / `set_own_words()` · `record(attempt)` · `set_known(key, on)` · `known_words()` · `reset()` (keeps own words) · `touch()` counts today's activity · `weakness_scores()` (3-day half-life, Bayesian prior) · `misses(pattern, days)` · `due_mistakes()` (missed and not since got right) · `streak()` · `xp()` · `level()` · `accuracy()` · `breakdown(attr)` · `recent_mistakes(n)` · `activity(weeks=12)` (GitHub-style grid) · `active_days()` · `insights()` · `export_json()` / `import_json(raw)` (compact, capped at 1200 attempts) |

### `python/core/quiz.py`
| Class | Members |
|---|---|
| **`Question`** (dataclass) | `qkey`, `skill`, `pattern`, `theme`, `kind`, `prompt`, `big`, `answer`, `explanations`, `correct_expl`, `options`, `sub`, `example`, `speak` · `shuffle(rng, keep_order=False)` · `public()` (no answer, no explanations) · `is_correct(choice)` · `target` · `stem` |
| **`QuestionType`** (ABC) | abstract `build(rng, target=None)`, `target_from_key(rest)`, `targets(theme)`, `pattern_of(target)` · concrete `key()`, `random(rng, theme)`, `from_key(qkey, rng)`, `handles(pattern)`, `for_pattern(pattern, rng)` |
| **`WordQuestion`**(QuestionType): shared word logic | `usable(word)` · `pool(theme)` · `targets()` · `target_from_key()` · `pattern_of()` (topic) · `pick(rng, theme)` (falls back to all words) · `random()` · `senses(english)` (avoids two right answers) · `distractors(word, rng)` (same theme and kind first, all words if the theme has fewer than 4) · `tip(word)` · `example(word)` · `theme_slug(word)` · `kind_note(word)` |
| **`MeaningQuestion`**(WordQuestion) | `build()`: Spanish → English |
| **`TranslateQuestion`**(WordQuestion) | `build()`: English → Spanish |
| **`GenderQuestion`**(WordQuestion) | `usable()` (nouns only) · `pattern_of()` (gender rule) · `build()`: el/la or los/las, explained by the rule |
| **`ChoiceSetQuestion`**(QuestionType, abstract) | abstract `choice_set(target, rng)` and `frame(target, rng)` · shared `build()` |
| **`SerEstarQuestion`**(ChoiceSetQuestion) | `targets()`, `target_from_key()`, `pattern_of()`, `choice_set()`, `frame()` |
| **`VerbQuestion`**(ChoiceSetQuestion) | `targets()`, `target_from_key()`, `pattern_of()`, `choice_set()`, `frame()` |
| **`FalseFriendQuestion`**(QuestionType) | `targets()`, `target_from_key()`, `pattern_of()`, `build()` (the trap option has its own explanation) |
| **`QuizSession`** (dataclass) | `total` · `score` · `done` · `record(index, choice, correct)` · `xp_gained()` · `public()` |
| **`QuizEngine`** | `start(mode)` (`mix`, `theme:<slug>` incl. `theme:mine`, `skill:<skill>`, `review`) · `check(sid, index, choice)` records the answer and returns both explanations plus a "Pattern spotted…" alert after 2+ misses · `summary(session)` · `question_from_key(qkey)` · internal `_weighted`, `_fill`, `_mix_picker`, `_pattern_picker` (weakness score²) |

### `python/core/mywords.py`
| Class | Members |
|---|---|
| **`BulkResult`** (dataclass) | `words`, `skipped` ((line, reason) pairs) |
| **`BulkWordParser`** | `split_article(es)` ("el agua" → feminine) · `clean(text)` · `parse_line(line)` (separators `= - – : ,` and tab; `(m) (f) (mpl) (fpl)` tags) · `parse(text)` |
| **`MyWords`** | `words()` · `count()` · `refresh()` (syncs into `BANK.mine`) · `make()` · `add(es, en, gender="auto", example="")` (validates, rejects duplicates) · `add_bulk(text)` · `bulk_message()` · `remove(key)` · limit 5000 |

### `python/core/oral.py`
| Class | Members |
|---|---|
| **`Scene`** (frozen dataclass) | `id`, `theme`, `title`, `sky`, `night`, `land`, `objects`, `hints`, `questions` (5 follow-ups), `water` |
| **`Palette`**: colour mixing | `rgb()` · `hex()` · `mix(a, b, t)` · `darken()` · `lighten()` |
| **`SceneArtist`**: draws an 800×500 SVG from a seed | `_wave()` · `_hill_path()` · `_defs()` · `_sun()` (sun with glow, or moon) · `_clouds()` (drifting) · `_stars()` (twinkling) · `_hills()` (three sine-wave layers, darker towards the front; sea and sand in water scenes) · `_objects()` (emoji with shadows, bobbing) · `draw(scene)` |
| **`OralCoach`** | `SCENES` (2 per theme), `CONVERSATION`, `STARTERS` (Describe / Guess / Connect / Opinion), `TIMINGS` (exam and quick) · `scenes(theme)` · `stimulus(theme=None, exclude=None)` |

### `python/core/writing.py`
| Class | Members |
|---|---|
| **`Issue`** (frozen dataclass) | `start`, `end`, `kind`, `title`, `message` · `as_dict()` |
| **`Sentences`** | `spans(text)` · `question_start(text, start, end, mark)` |
| **`Rule`** (ABC) | abstract `find(text, low)` · `_issue(match, title, message)` |
| **`SpanglishRule`**(Rule) | 29 patterns with explanations: soy 17 años, estoy caliente, hacer sentido, aplicar para, tener un buen tiempo, jugar la guitarra, me gusto, más mejor, en sábado, muy mucho, la gente son, mi amigo y yo soy, para dos semanas, depende en, soñar sobre, pensar sobre, estás tu, and the false friends (realizar que, embarazada, soportar, librería, actualmente)… |
| **`AccentRule`**(Rule) | dictionary of words missing an accent or tilde, singular -cion/-sion, and context checks (esta bien → está, para mi → para mí) |
| **`QuestionWordRule`**(Rule) | qué / cómo / dónde… at the start of questions and exclamations |
| **`OpeningMarkRule`**(Rule) | missing ¿ or ¡; marks only the first word |
| **`TenseDetector`** | `classify(word)` · `detect(text)` (present, preterite, imperfect, future incl. ir a + infinitive, conditional) · `tip(found, words)` |
| **`Convention`** (frozen dataclass) | one checklist item for a text type |
| **`WritingCoach`** | `resolve(issues)` (earliest, then longest; identical spans merged) · `segments(text, issues)` · `count_words()` · `connectors()` (8 functions, overuse of y / pero…) · `register()` (tú vs usted) · `repeated()` · `conventions()` (email, informal letter, formal letter, blog, diary, article, leaflet, speech) · `analyse(text, type)` · `score()` (out of 100) · `EXAMPLE` |

### `python/views.py`
| Class | Members |
|---|---|
| **`Page`** | `render(arg)` raises `NotImplementedError` · `countdown()` (days to 3 May 2027) · `word_of_the_day()` · `summary()` · `plural()` · `mode_link()` · `grad()` · `delay()` · `speak_btn()` · `ring()` · `label_class()` · `head()` · `theme_card()` |
| **`HomePage`**, **`VocabPage`**, **`ProgressPage`** | `render()` |
| **`ThemePage`** | `card(word, i, known)` · `render(slug)` |
| **`MyWordsPage`** | `list_html()` · `actions_html()` · `render()` |
| **`QuizPage`** | `mode_card()` · `render()` (mode picker) · `big_html()` · `question_html()` · `play_html()` · `feedback_html()` · `results_html()` |
| **`OralPage`** | `words_html()` · `parts(stimulus)` · `render(theme)` |
| **`WritePage`** | `render()` · `meter_html(words)` · `preview_html(analysis)` · `panel_html(analysis)` |
| **`Router`** | `PAGES` · `page(name)` · `render(name, arg)` |

### `python/api.py`
| Class / function | Members |
|---|---|
| **`VamosApp`**: the facade | `render(page, arg)` · `quiz_start(mode)` · `quiz_answer(sid, index, choice)` · `oral_stimulus(theme, exclude)` · `write_check(text, type)` · `write_example()` · `set_known(key, on)` · `add_word(es, en, gender, example)` · `add_words_bulk(text)` · `remove_word(key)` · `reset()` · `export_state()` · `import_state(raw)` · `state_info()` |
| `create_app(tz_offset_minutes, saved_state)` | Builds the app |

### `serve.py` and `play_in_shell.py`
| Class | Members |
|---|---|
| **`SiteHandler`**(SimpleHTTPRequestHandler) | `.wasm` → `application/wasm`; `end_headers()` adds no-cache; `log_message()` keeps IDLE quiet |
| **`SiteServer`** | `_bind()` (port 8000 or the next free one, `ThreadingTCPServer`) · `start()` (instructions, opens the browser after 1 s, stops cleanly on Ctrl+C) |
| **`ShellQuiz`** | `load()` / `save()` · `plain(html)` strips the HTML · `ask(prompt, valid)` validates input · `menu()` · `play(mode)` · `run()` |

---

## OOP concepts and where they're used

- **Classes and encapsulation:**
  - `MistakeMemory` keeps its attempts, known words and activity private (`_attempts`, `_known`…). Other code goes through `record`, `set_known` and `export_json`, and the derived numbers (XP, streak, weakness) are computed, never stored.
  - `VocabularyBank` hides its index and themes behind `find`, `theme` and `all_words`.
  - The quiz answers stay inside `QuizSession` in Python; the page only sees `public()`.
- **Dataclasses:**
  - Frozen, for immutable data: `Word`, `FalseFriend`, `Person`, `Level`, `Scene`, `Issue`, `Convention`.
  - Mutable: `Theme`, `Question`, `QuizSession`, `Attempt`, `ChoiceSet`, `SerEstarItem`, `Verb`, `BulkResult`.
- **Inheritance:**
  - `QuestionType → WordQuestion → Meaning/Translate/GenderQuestion`
  - `QuestionType → ChoiceSetQuestion → SerEstar/VerbQuestion`
  - `QuestionType → FalseFriendQuestion`
  - `Rule → Spanglish/Accent/QuestionWord/OpeningMarkRule`
  - `Page → HomePage, VocabPage…`
  - `SiteHandler → SimpleHTTPRequestHandler`
- **Abstraction:**
  - `QuestionType(ABC)` declares `build`, `target_from_key`, `targets` and `pattern_of` with `@abstractmethod`.
  - `ChoiceSetQuestion` adds abstract `choice_set` and `frame`.
  - `Rule(ABC)` declares `find`.
  - `Page.render` raises `NotImplementedError`.
  - None of these can be instantiated; the unit tests check this.
- **Polymorphism:**
  - `QuizEngine` calls `random()`, `from_key()` and `for_pattern()` on any question type without knowing which one it has.
  - `WritingCoach` loops over `self.rules` and calls `find()` on each.
  - `Router` calls `render()` on whichever `Page` subclass matches the route.
- **Composition:** `VamosApp` owns a `Clock`, `MistakeMemory`, `MyWords`, `QuizEngine`, `OralCoach`, `WritingCoach` and `Router`. `QuizEngine` owns the six question types.
- **Facade pattern:** `VamosApp` is the single object JavaScript talks to. Every method takes plain values and returns HTML or JSON text, so the JavaScript shell stays tiny.
- **Class methods and static methods** for knowledge tables that don't need instances: `GenderRules`, `Conjugator`, `SerEstar`, `Person`, `Spelling`, `Palette`, `Labels`.

---

## Accessibility and browsers

- Tested in Chromium, WebKit (Safari's engine) and Firefox, on desktop and at 390 × 844, in both light and dark mode.
- Visible focus rings; `aria-label`s on icon buttons; `role="status"` on toasts and form messages; labels on every field; quiz keys 1–4 and Enter.
- Writing marks open on hover, tap or keyboard focus.
- Everything still works with `prefers-reduced-motion`; it just doesn't move.

## Credits

- [Pyodide](https://pyodide.org) 0.26.4 (Mozilla Public License 2.0), self-hosted in `py/`.
- Fonts: Fraunces and Plus Jakarta Sans (SIL Open Font License), via Google Fonts.

¡Mucha suerte en el examen! 🍀
