"""Paper 1 writing coach.

It never rewrites the student's text. It only *points*: each Issue marks a span
and explains the rule, so the student makes the fix themselves.

    Rule (ABC)
    ├── SpanglishRule      word-for-word copies of English and false friends
    ├── AccentRule         missing accents and tildes
    ├── QuestionWordRule   qué / cómo / dónde… in questions and exclamations
    └── OpeningMarkRule    missing ¿ or ¡ (only the first word is marked)
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from typing import ClassVar

from .vocab import BANK


@dataclass(frozen=True)
class Issue:
    """A marked span of the student's text plus the teaching point."""

    start: int
    end: int
    kind: str      # spanglish / accent / punctuation
    title: str
    message: str   # trusted HTML (never contains the student's own text)

    def as_dict(self) -> dict:
        return {"start": self.start, "end": self.end, "kind": self.kind,
                "title": self.title, "message": self.message}


class Sentences:
    """Splits text into sentence spans and finds where a question/exclamation starts."""

    QWORDS = ("por que", "que", "como", "donde", "adonde", "cuando", "cual", "cuales",
              "quien", "quienes", "cuanto", "cuanta", "cuantos", "cuantas",
              "por qué", "qué", "cómo", "dónde", "adónde", "cuándo", "cuál", "cuáles",
              "quién", "quiénes", "cuánto", "cuánta", "cuántos", "cuántas")

    @staticmethod
    def spans(text: str) -> list[tuple[int, int, str]]:
        """(start, end, terminator) for each sentence; terminator is . ! ? newline or ''."""
        out, start, i, n = [], 0, 0, len(text)
        while i < n:
            ch = text[i]
            if ch in ".!?\n":
                j = i
                while j + 1 < n and text[j + 1] in ".!?":
                    j += 1
                term = "?" if "?" in text[i:j + 1] else "!" if "!" in text[i:j + 1] else ch
                out.append((start, i, term))
                start = i = j + 1
                continue
            i += 1
        if start < n:
            out.append((start, n, ""))
        return out

    @classmethod
    def question_start(cls, text: str, start: int, end: int, mark: str) -> int:
        """Where the question (or exclamation) begins inside a sentence span."""
        seg = text[start:end]
        opener = "¿" if mark == "?" else "¡"
        if opener in seg:
            return start + seg.rindex(opener) + 1
        low = seg.lower()
        cut = max(low.rfind(","), low.rfind(";"), low.rfind(":"))
        if cut >= 0:
            rest = low[cut + 1:].lstrip()
            if any(rest.startswith(w + " ") or rest == w for w in cls.QWORDS):
                return start + cut + 1 + (len(low[cut + 1:]) - len(rest))
        offset = len(seg) - len(seg.lstrip(" \t\"'«“"))
        return start + offset


class Rule(ABC):
    """A writing check that returns the Issues it finds."""

    kind: ClassVar[str] = ""

    @abstractmethod
    def find(self, text: str, low: str) -> list[Issue]:
        """``low`` is ``text.lower()`` (same length), handy for case-insensitive regexes."""

    def _issue(self, m: re.Match, title: str, message: str) -> Issue:
        if "w" in m.re.groupindex and m.group("w") is not None:
            return Issue(m.start("w"), m.end("w"), self.kind, title, message)
        return Issue(m.start(), m.end(), self.kind, title, message)


class SpanglishRule(Rule):
    """Word-for-word copies of English, plus the classic false friends."""

    kind = "spanglish"
    PATTERNS = [
        (r"\b(?:soy|eres|es|somos|son)\s+(?:\d+|[a-záéíóúñ]+)\s+años\b(?!\s+(?:mayor|menor|más))",
         "Age uses tener", "In Spanish you <i>have</i> years: <b>tengo 17 años</b>, not 'soy 17 años'."),
        (r"\b(?:estoy|estamos|estaba|estábamos)\s+(?:muy\s+)?calientes?\b",
         "Feeling hot = tener calor",
         "For feeling hot, say <b>tengo calor</b>. 'Estoy caliente' doesn't mean what you think!"),
        (r"\b(?:(?:el tiempo|el clima|el día)\s+(?:es|está|era|estaba|fue)|hace|hacía|hizo)\s+(?:muy\s+)?caliente\b",
         "Weather uses hacer", "Weather uses <b>hacer + noun</b>: <b>hace calor</b>, hace mucho calor."),
        (r"\b(?:hace|hacía|hizo|tengo|tienes|tiene|tenemos|tienen|tenía)\s+muy\s+(?:calor|frío|hambre|sed|sueño|miedo|prisa|suerte)\b",
         "Mucho, not muy",
         "Calor, frío, hambre and sed are nouns, so use <b>mucho / mucha</b>: hace mucho calor, tengo mucha hambre."),
        (r"\b(?:hace|hacen|hacer|hizo)\s+sentido\b", "Make sense = tener sentido",
         "Spanish says <b>tener sentido</b>: no tiene sentido. 'Hacer sentido' is a word-for-word copy of English."),
        (r"\baplic(?:ar|o|as|a|amos|an|é|ó|aste|aron)\s+(?:para|a)\b", "Apply for = solicitar",
         "To apply for a job is <b>solicitar</b> un trabajo or un puesto. Aplicar means to apply a rule or a cream."),
        (r"\b(?:tener|tengo|tienes|tiene|tenemos|tienen|tuve|tuviste|tuvo|tuvimos|tuvieron|tenía)\s+un\s+(?:buen|gran|mal)\s+tiempo\b",
         "Have a good time = pasarlo bien",
         "Say <b>pasarlo bien</b>: lo pasé muy bien, lo pasamos genial. 'Tener un buen tiempo' is copied from English."),
        (r"\b(?:jueg[a-záéíóú]*|jug[a-záéíóú]*)\s+(?:a\s+la\s+|al\s+|el\s+|la\s+)?(?:guitarra|piano|violín|batería|flauta|trompeta|saxofón|violonchelo)\b",
         "Instruments use tocar",
         "You <b>tocar</b> an instrument: toco la guitarra. Jugar is for games and sports: juego al fútbol."),
        (r"\bme\s+gusto\b", "Me gusta, not me gusto",
         "<b>Gustar</b> agrees with the thing you like: <b>me gusta</b> la música, <b>me gustan</b> los perros. "
         "'Me gusto' means 'I like myself'! (For the past, write me gustó, with the accent.)"),
        (r"\bm[aá]s\s+(?:mejor|peor|mayor|menor)(?:es)?\b", "Más mejor → mejor",
         "<b>Mejor</b> already means 'better' (and peor 'worse'), so drop the más."),
        (r"\ben\s+(?:el\s+)?(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)s?\b",
         "No 'en' with days",
         "Days take the article, not en: <b>el sábado</b> (on Saturday), <b>los sábados</b> (on Saturdays)."),
        (r"\bmuy\s+mucho\b", "Never 'muy mucho'", "Use <b>muchísimo</b>: me gusta muchísimo."),
        (r"\bla\s+gente\s+(?:no\s+)?(?:son|están|eran|estaban|tienen|piensan|creen|dicen|hacen|van|quieren|viven|pueden|necesitan|usan|comen|trabajan|hablan|prefieren|deben|saben)\b",
         "La gente is singular",
         "<b>La gente</b> is singular (and feminine): la gente <b>es</b> simpática, la gente <b>piensa</b>…"),
        (r"\b(?:mi|tu|su)\s+(?:mejor\s+)?[a-záéíóúñ]+\s+y\s+yo\s+(?:no\s+)?(?:soy|estoy|voy|fui|era|estaba|tengo|hago|(?!no\b)[a-záéíóúñ]+o)\b",
         "X y yo = nosotros",
         "<b>Mi amigo y yo</b> means 'we', so the verb is in the nosotros form: "
         "mi amigo y yo <b>fuimos / somos / jugamos</b>."),
        (r"\bpara\s+(?:dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|unos?|unas?|\d+)\s+(?:días|semanas|meses|años|horas|minutos)\b",
         "For + time = durante",
         "For how long something lasts, use <b>durante</b> (or nothing): estuve en Madrid <b>durante dos semanas</b>. "
         "Para + time is for deadlines and plans."),
        (r"\bdepend[a-záéíóú]*\s+en\b", "Depender de", "It's <b>depender de</b>: depende de ti, depende del tiempo."),
        (r"\b(?:soñ(?:ar|é|ó|amos|aron|aba|ando)|sueñ(?:o|as|a|an))\s+sobre\b", "Soñar con",
         "In Spanish you dream <i>with</i>: <b>sueño con</b> viajar por el mundo."),
        (r"\b(?:pens[a-záéíóú]*|piens[a-záéíóú]*)\s+sobre\b", "Pensar en",
         "To think about something or someone is <b>pensar en</b>: pienso en el futuro. "
         "To ask for an opinion: <b>¿Qué piensas de…?</b>"),
        (r"\b(?:estás|estas|eres|tienes|vas|quieres|puedes|vienes|sabes|y)\s+(?P<w>tu)(?=\s*(?:[?¿,.!]|$))",
         "Tú (you) needs its accent", "With an accent, <b>tú</b> means 'you'. Without it, tu means 'your' (tu casa)."),
        (r"(?:^|(?<=[\s¿¡]))(?P<w>tu)\s+(?:eres|estás|estas|tienes|vas|puedes|quieres|sabes|vives|haces|hablas)\b",
         "Tú (you) needs its accent", "With an accent, <b>tú</b> means 'you'. Without it, tu means 'your' (tu casa)."),
        (r"\breali[zc][a-záéíóú]*\s+que\b", "To realise = darse cuenta",
         "<b>Realizar</b> means to carry out (realizar un proyecto). To realise is <b>darse cuenta de</b>: "
         "me di cuenta de que…"),
        (r"\bembarazad[oa]s?\b", "Embarazada = pregnant!",
         "Check: <b>embarazada</b> means pregnant. If you meant embarrassed, use <b>avergonzado/a</b> "
         "or <b>me da vergüenza</b>."),
        (r"\bsoport(?:ar|o|as|a|amos|an|é|ó|aron|aba)\b", "Soportar = put up with",
         "<b>Soportar</b> means to stand or put up with (no soporto el ruido). To support someone is <b>apoyar</b>."),
        (r"\blibrer[ií]as?\b", "Librería = bookshop",
         "A <b>librería</b> is a bookshop. If you meant a library, that's a <b>biblioteca</b>."),
        (r"\bactualmente\b", "Actualmente = currently",
         "<b>Actualmente</b> means currently or nowadays. If you meant 'actually', say <b>en realidad</b>."),
        (r"\bbusc[a-záéíóú]*\s+para\b", "Buscar already means 'look for'",
         "No 'para' needed: <b>busco trabajo</b> = I'm looking for work."),
        (r"\b(?:un|una)\s+otr[oa]s?\b", "Otro without un",
         "<b>Otro</b> already means 'another': otro día, otra vez (never 'un otro')."),
        (r"\b(?:soy|eres|somos|son)\s+(?:muy\s+)?(?:cansad|enferm|preocupad|content)[oa]s?\b",
         "Temporary states use estar", "How you feel right now uses <b>estar</b>: estoy cansado, estamos contentos."),
        (r"\bsoy\s+(?:muy\s+)?aburrid[oa]\b", "Bored = estar aburrido",
         "<b>Soy aburrido</b> means 'I'm a boring person'! Bored is <b>estoy aburrido/a</b>."),
    ]

    def __init__(self):
        self._compiled = [(re.compile(p, re.IGNORECASE | re.MULTILINE), t, m) for p, t, m in self.PATTERNS]

    def find(self, text: str, low: str) -> list[Issue]:
        return [self._issue(m, title, msg) for rx, title, msg in self._compiled for m in rx.finditer(low)]


class AccentRule(Rule):
    """Common words missing their accent or tilde, plus singular -cion / -sion."""

    kind = "accent"
    WORDS = {
        "tambien": "también", "despues": "después", "facil": "fácil", "dificil": "difícil",
        "musica": "música", "telefono": "teléfono", "rapido": "rápido", "rapida": "rápida",
        "ingles": "inglés", "frances": "francés", "aleman": "alemán", "japones": "japonés",
        "portugues": "portugués", "autobus": "autobús", "arbol": "árbol", "lapiz": "lápiz",
        "pais": "país", "dia": "día", "dias": "días", "sabado": "sábado", "miercoles": "miércoles",
        "matematicas": "matemáticas", "fisica": "física", "quimica": "química", "pelicula": "película",
        "peliculas": "películas", "pagina": "página", "ultimo": "último", "ultima": "última",
        "proximo": "próximo", "proxima": "próxima", "numero": "número", "simpatico": "simpático",
        "simpatica": "simpática", "simpaticos": "simpáticos", "simpaticas": "simpáticas",
        "antipatico": "antipático", "antipatica": "antipática", "timido": "tímido", "timida": "tímida",
        "medico": "médico", "medica": "médica", "jamas": "jamás", "ademas": "además", "detras": "detrás",
        "asi": "así", "aqui": "aquí", "alli": "allí", "adios": "adiós", "lapices": "lápices",
        "examenes": "exámenes", "jovenes": "jóvenes", "util": "útil", "tecnologia": "tecnología",
        "energia": "energía", "biologia": "biología", "geografia": "geografía", "economia": "economía",
        "politica": "política", "publico": "público", "publica": "pública", "informatica": "informática",
        "platano": "plátano", "movil": "móvil", "futbol": "fútbol", "exito": "éxito", "tipico": "típico",
        "tipica": "típica", "fantastico": "fantástico", "fantastica": "fantástica", "increible": "increíble",
        "avion": "avión", "camion": "camión", "jamon": "jamón", "corazon": "corazón", "raton": "ratón",
        "jardin": "jardín", "interes": "interés", "estres": "estrés", "cafe": "café", "estan": "están",
        "podria": "podría", "gustaria": "gustaría", "encantaria": "encantaría", "habia": "había",
        "tenia": "tenía", "queria": "quería", "vivia": "vivía", "comia": "comía", "iria": "iría",
        "tendria": "tendría", "haria": "haría", "jugue": "jugué", "comi": "comí", "vivi": "viví",
        "sali": "salí", "comio": "comió", "salio": "salió", "vivio": "vivió", "mas": "más",
        "mama": "mamá", "papa": "papá",
        "ano": "año", "anos": "años", "espanol": "español", "espanola": "española", "espana": "España",
        "manana": "mañana", "nino": "niño", "nina": "niña", "ninos": "niños", "senor": "señor",
        "senora": "señora", "companero": "compañero", "companera": "compañera", "montana": "montaña",
        "pequeno": "pequeño", "pequena": "pequeña", "sueno": "sueño", "otono": "otoño",
        "cumpleanos": "cumpleaños", "bano": "baño",
    }
    NO_ACCENT = {"fué": "fue", "fuí": "fui", "dió": "dio", "vió": "vio"}
    CONTEXT = [
        (r"\b(?P<w>esta)\s+(?:bien|mal|en|muy|cerca|lejos|aquí|aqui|allí|alli|cansad[oa]|content[oa]|enferm[oa]|abiert[oa]|cerrad[oa]|lloviendo|nublado)\b",
         "está", "Is = <b>está</b> (with an accent). Esta without an accent means 'this'."),
        (r"\b(?P<w>estas)\s+(?:bien|mal|en|muy|cansad[oa]s?|content[oa]s?)\b", "estás",
         "You are = <b>estás</b> (with an accent). Estas without an accent means 'these'."),
        (r"\b(?:cómo|como|dónde|donde|qué|que)\s+(?P<w>estas)\b", "estás",
         "You are = <b>estás</b> (with an accent). Estas without an accent means 'these'."),
        (r"\bpara\s+(?P<w>mi)(?=\s*(?:[,.;:!?]|$))", "mí",
         "After a preposition, 'me' is <b>mí</b> with an accent: para mí. (Mi without an accent means 'my'.)"),
        (r"\ba\s+(?P<w>mi)\s+me\b", "mí",
         "In <b>a mí me gusta</b>, mí takes an accent. (Mi without an accent means 'my'.)"),
    ]
    TILDE = {"ano", "anos", "espanol", "espanola", "espana", "manana", "nino", "nina", "ninos", "senor",
             "senora", "companero", "companera", "montana", "pequeno", "pequena", "sueno", "otono",
             "cumpleanos", "bano"}
    WORD_RE = re.compile(r"[a-záéíóúüñ]+", re.IGNORECASE)
    CION_RE = re.compile(r"\b[a-zñ]+(?:cion|sion)\b")

    def __init__(self):
        self._context = [(re.compile(p, re.IGNORECASE | re.MULTILINE), fix, msg) for p, fix, msg in self.CONTEXT]

    def find(self, text: str, low: str) -> list[Issue]:
        issues = []
        for m in self.WORD_RE.finditer(low):
            word = m.group()
            if word in self.WORDS:
                fix = self.WORDS[word]
                if word == "ano" or word == "anos":
                    msg = (f"Write <b>{fix}</b> with the tilde: ñ. Without it, it's a very different "
                           f"(and embarrassing) word!")
                elif word in self.TILDE:
                    msg = f"Don't forget the tilde: <b>{fix}</b>."
                elif word == "mas":
                    msg = "Did you mean <b>más</b> (more)? Without the accent, mas is a rare old word for 'but'."
                elif word in ("mama", "papa"):
                    msg = f"Mum and dad are <b>{fix}</b>, with the accent on the last syllable."
                else:
                    msg = f"Missing accent: <b>{fix}</b>."
                issues.append(Issue(m.start(), m.end(), self.kind, "Accent missing", msg))
            elif word in self.NO_ACCENT:
                issues.append(Issue(m.start(), m.end(), self.kind, "No accent needed",
                                    f"One-syllable verb forms don't take an accent: <b>{self.NO_ACCENT[word]}</b>."))
        for m in self.CION_RE.finditer(low):
            issues.append(Issue(m.start(), m.end(), self.kind, "Accent missing",
                                "Singular -ción and -sión words need the accent: canción, televisión. "
                                "It disappears in the plural: canciones."))
        for rx, fix, msg in self._context:
            for m in rx.finditer(low):
                issues.append(self._issue(m, "Accent missing", msg))
        return issues


class QuestionWordRule(Rule):
    """qué / cómo / dónde… need their accent when they ask (or exclaim)."""

    kind = "accent"
    QUESTION = {"por que": "por qué", "que": "qué", "como": "cómo", "donde": "dónde", "adonde": "adónde",
                "cuando": "cuándo", "cual": "cuál", "cuales": "cuáles", "quien": "quién", "quienes": "quiénes",
                "cuanto": "cuánto", "cuanta": "cuánta", "cuantos": "cuántos", "cuantas": "cuántas"}
    EXCLAIM = ("que", "como", "cuanto", "cuanta", "cuantos", "cuantas")

    def find(self, text: str, low: str) -> list[Issue]:
        issues = []
        for start, end, term in Sentences.spans(text):
            if term not in "?!" or not term:
                continue
            q = Sentences.question_start(text, start, end, term)
            words = self.QUESTION if term == "?" else {k: self.QUESTION[k] for k in self.EXCLAIM}
            for plain in sorted(words, key=len, reverse=True):
                m = re.match(re.escape(plain) + r"\b", low[q:end])
                if m:
                    fix = words[plain]
                    issues.append(Issue(q, q + m.end(), self.kind, "Question word needs an accent",
                                        f"In questions and exclamations it's <b>{fix}</b>, with an accent: "
                                        f"¿Qué…? ¿Cómo…? ¡Qué bien!"))
                    break
        return issues


class OpeningMarkRule(Rule):
    """A ? or ! without its opening ¿ or ¡. Only the first word is marked,
    so other issues inside the sentence stay visible."""

    kind = "punctuation"

    def find(self, text: str, low: str) -> list[Issue]:
        issues = []
        for start, end, term in Sentences.spans(text):
            if term not in ("?", "!"):
                continue
            opener = "¿" if term == "?" else "¡"
            if opener in text[start:end]:
                continue
            q = Sentences.question_start(text, start, end, term)
            m = re.match(r"[\wáéíóúüñÁÉÍÓÚÜÑ]+", text[q:end])
            if not m:
                continue
            if term == "?":
                title, msg = "Missing ¿", "Spanish questions open with <b>¿</b> as well as closing with ?: <b>¿Cómo estás?</b>"
            else:
                title, msg = "Missing ¡", "Exclamations open with <b>¡</b> too: <b>¡Qué bien!</b>"
            issues.append(Issue(q, q + m.end(), self.kind, title, msg))
        return issues


class TenseDetector:
    """Spots which tenses a text uses (a hint, not a parser)."""

    NAMES = {"present": "Present", "preterite": "Preterite", "imperfect": "Imperfect",
             "future": "Future", "conditional": "Conditional"}
    PRESENT = frozenset("""soy eres es somos son estoy estás está estamos están tengo tienes tiene tenemos tienen
        hay voy vas va vamos van hago haces hace hacemos hacen puedo puedes puede podemos pueden quiero quieres
        quiere queremos quieren gusta gustan encanta encantan vivo vives vive vivimos viven come comemos comen
        juego juegas juega jugamos juegan prefiero prefieres prefiere pienso piensas piensa creo crees cree
        llamo llama necesito necesita uso usa leo lee veo ves salgo sale salimos duermo duerme empiezo empieza
        hablo hablas habla hablan escribo escribe llevo lleva trabaja estudia sé sabe conozco digo dice vengo
        viene vienes pongo debo debes debe deben parece parecen odio levanto ducho acuesto""".split())
    PRETERITE = frozenset("""fui fue fuiste fuimos fueron hice hizo hiciste hicimos hicieron tuve tuvo tuviste
        tuvimos tuvieron estuve estuvo estuviste estuvimos estuvieron pude pudo pudimos pudieron dije dijo dijimos
        dijeron vine vino vinimos vinieron vi vio vimos vieron di dio dimos dieron puse puso pusimos quise quiso
        supe supo traje trajo anduve""".split())
    IMPERFECT = frozenset("""era eras éramos eran iba ibas íbamos iban veía veías veíamos veían había""".split())
    STOP = frozenset("""qué café bebé josé porqué esté está mamá papá allí aquí así ahí tú él mí sí más jamás
        además después también adiós país quizá menú sofá triste chiste existe insiste consiste resiste persiste
        asiste despiste alemán inglés francés japonés autobús según jardín ratón avión camión corazón""".split())
    INFINITIVES = frozenset("""gustar encantar ser estar ir hacer poder tener querer deber preferir vivir comer
        beber viajar trabajar estudiar visitar comprar ayudar cambiar usar jugar ver leer escribir hablar aprender
        ganar ahorrar reciclar proteger reducir gastar salir llevar pasar encontrar conocer intentar necesitar
        mejorar construir crear elegir haber decir venir poner saber dormir pensar creer volver sentir abrir
        recibir compartir decidir subir asistir correr vender llover nevar""".split())
    IRREGULAR_STEMS = ("tendr", "podr", "har", "dir", "saldr", "pondr", "vendr", "querr", "sabr", "habr", "cabr", "valdr")
    FUTURE_END = ("é", "ás", "á", "emos", "án")
    COND_END = ("ía", "ías", "íamos", "ían")

    def __init__(self):
        verbs = {w.es.split()[0] for w in BANK.all_words(include_mine=False) if w.kind == "verb"}
        verbs = {v[:-2] if v.endswith("se") else v for v in verbs}
        self.infinitives = self.INFINITIVES | verbs

    def classify(self, word: str) -> str | None:
        w = word.lower()
        if len(w) < 2:
            return None
        if w in self.IMPERFECT:
            return "imperfect"
        if w in self.PRETERITE:
            return "preterite"
        for end in self.COND_END:
            if w.endswith(end):
                stem = w[: -len(end)]
                if stem in self.infinitives or stem in self.IRREGULAR_STEMS:
                    return "conditional"
                if stem + "er" in self.infinitives or stem + "ir" in self.infinitives:
                    return "imperfect"
        for end in self.FUTURE_END:
            if w.endswith(end):
                stem = w[: -len(end)]
                if stem in self.infinitives or stem in self.IRREGULAR_STEMS:
                    return "future"
        if re.search(r"(?:aba|abas|ábamos|aban)$", w) and len(w) > 4:
            return "imperfect"
        if w in self.STOP:
            return None
        if len(w) >= 4 and re.search(r"(?:aste|iste|aron|ieron|ió)$", w):
            return "preterite"
        if len(w) >= 4 and (w.endswith(("ué", "ió")) or (w[-1] in "éó" and w[-2] not in "aeiou")):
            return "preterite"
        if w in self.PRESENT:
            return "present"
        return None

    def detect(self, text: str) -> dict[str, list[str]]:
        found: dict[str, list[str]] = {}
        low = text.lower()
        for m in re.finditer(r"[a-záéíóúüñ]+", low):
            tense = self.classify(m.group())
            if tense and m.group() not in found.setdefault(tense, []):
                found[tense].append(m.group())
        for m in re.finditer(r"\b(?:voy|vas|va|vamos|van)\s+a\s+([a-záéíóúñ]+(?:ar|er|ir))\b", low):
            phrase = m.group(0)
            if phrase not in found.setdefault("future", []):
                found["future"].append(phrase)
        return {k: v[:4] for k, v in found.items() if v}

    def tip(self, found: dict[str, list[str]], words: int) -> str:
        if words < 10:
            return "Write a few sentences and I'll check your range of tenses."
        past = "preterite" in found or "imperfect" in found
        future = "future" in found or "conditional" in found
        if past and future and len(found) >= 3:
            return "Great range of tenses: past, present and future. Examiners love this."
        if not past and not future:
            return ("You only use the present. Add a past event (el fin de semana pasado fui…) "
                    "and a plan (voy a + infinitive).")
        if not past:
            return "Add a past tense: ayer comí…, el año pasado fuimos…"
        if not future:
            return "Add a plan or a wish: voy a + infinitive, or me gustaría + infinitive."
        return "Good mix. Can you add one more tense, e.g. the imperfect for description (era, había)?"


@dataclass(frozen=True)
class Convention:
    """One item on a text type's checklist."""

    label: str
    hint: str
    pattern: str = ""
    check: str = "regex"   # regex / title / signature / past
    flags: int = re.IGNORECASE | re.MULTILINE


class WritingCoach:
    """Runs every rule and builds the full Paper 1 analysis."""

    TARGET = (70, 150)
    TEXT_TYPES = {"email": "Email", "informal-letter": "Informal letter", "formal-letter": "Formal letter",
                  "blog": "Blog post", "diary": "Diary entry", "article": "Article", "leaflet": "Leaflet",
                  "speech": "Speech"}
    _SIGN_OFF = r"(un abrazo|un beso|besos|abrazos|saludos|un saludo|hasta pronto|nos vemos|cuídate|escríbeme pronto)"
    CONVENTIONS = {
        "email": [
            Convention("Greeting", "Open with Hola + name, or Querido/a…", r"\A\s*(asunto:.*\n\s*)?(hola|querid[oa]s?|estimad[oa]s?|buenos días|buenas)\b"),
            Convention("Subject line", "Emails often start with 'Asunto: …'", r"\A\s*asunto\s*:"),
            Convention("Asks the reader something", "Ask a question: ¿Qué tal estás? ¿Y tú?", r"\?"),
            Convention("Sign-off", "Close with Un abrazo, Hasta pronto or Saludos", _SIGN_OFF),
            Convention("Your name at the end", "Sign with your name on the last line", check="signature"),
        ],
        "informal-letter": [
            Convention("Place and date", "Start with the place and date: Madrid, 3 de mayo de 2027",
                       r"[a-záéíóúñ]+,\s*\d{1,2}\s+de\s+[a-z]+"),
            Convention("Friendly greeting", "Querido Juan: / Querida Ana: / Hola, Marta:", r"\b(querid[oa]s?|hola)\b"),
            Convention("Asks the reader something", "Ask a question: ¿Cómo estás?", r"\?"),
            Convention("Friendly closing", "Un abrazo, Besos, Escríbeme pronto…",
                       r"(un abrazo|un beso|besos|abrazos|hasta pronto|escríbeme pronto|cuídate|tu amig[oa])"),
            Convention("Signature", "Sign with your name on the last line", check="signature"),
        ],
        "formal-letter": [
            Convention("Date", "Add the date: 3 de mayo de 2027", r"\d{1,2}\s+de\s+[a-z]+"),
            Convention("Formal greeting", "Estimado señor: / Estimada señora:",
                       r"(estimad[oa]s?|muy señor|muy señora|a quien corresponda|distinguid[oa])"),
            Convention("Says why you're writing", "Le escribo para… / Me pongo en contacto con usted para…",
                       r"(le escribo|les escribo|me pongo en contacto|el motivo de|quisiera|me gustaría solicitar)"),
            Convention("Uses usted", "Address the reader as usted: le, su, usted",
                       r"\b(usted|ustedes|le agradecería|le escribo|su empresa|le saluda)\b"),
            Convention("Formal closing", "Atentamente / Un cordial saludo",
                       r"(atentamente|le saluda atentamente|un cordial saludo|reciba un cordial saludo|quedo a la espera)"),
        ],
        "blog": [
            Convention("Title", "Give your post a short title on the first line", check="title"),
            Convention("Talks to readers", "¡Hola a todos! ¿Y vosotros?",
                       r"(\bvosotr[oa]s\b|\bvuestr[oa]s?\b|\bos\b|¿y tú|hola a todos|queridos lectores)"),
            Convention("Personal experience", "Write about you: yo, me, mi…", r"\b(yo|me|mi|mis)\b"),
            Convention("Question for readers", "Ask your readers something", r"\?"),
            Convention("Invites comments", "End with: ¡Dejad vuestros comentarios!",
                       r"(comentarios|comentad|dejad|escribidme|contadme|compartid)"),
        ],
        "diary": [
            Convention("Opening", "Start with Querido diario: or the day and date",
                       r"(querido diario|\A\s*(lunes|martes|miércoles|jueves|viernes|sábado|domingo)|\A\s*\d{1,2}\s+de\s+[a-z]+)"),
            Convention("Feelings", "Say how you felt: estaba nervioso, me sentí feliz",
                       r"\b(me sentí|me siento|estaba|estoy|estuve|feliz|triste|content[oa]|nervios[oa]|preocupad[oa]|emocionad[oa]|cansad[oa])\b"),
            Convention("Past events", "Tell what happened today: hoy fui…, comí…", check="past"),
            Convention("Closing", "Hasta mañana / Buenas noches", r"(hasta mañana|buenas noches|hasta pronto|mañana te cuento)"),
        ],
        "article": [
            Convention("Headline", "Start with a short, catchy headline", check="title"),
            Convention("Byline", "Add who wrote it: Por Ana García", r"^\s*por\s+[a-záéíóúñ]+"),
            Convention("Hooks the reader", "Open with a question or an exclamation", r"[¿¡]"),
            Convention("General statements", "Se puede…, hay que…, es importante…",
                       r"\b(se puede|se debe|hay que|es importante|es necesario|muchos jóvenes|la gente)\b"),
            Convention("Conclusion", "En conclusión… / Para terminar…",
                       r"(en conclusión|para concluir|para terminar|en resumen|en definitiva)"),
        ],
        "leaflet": [
            Convention("Eye-catching title", "A short title on the first line", check="title"),
            Convention("Headings or bullet points", "Use - or • to list key points", r"^\s*([-•*·]|\d+[.)])\s"),
            Convention("Instructions", "Use commands: visita, recicla, no olvides…",
                       r"\b(visita|ven|venid|llama|recicla|usa|apaga|no olvides|participa|únete|descubre|ayuda|reserva|consulta)\b"),
            Convention("Contact details", "Add a web, phone or address", r"(@|www\.|\.com|\.es\b|teléfono|tel\.|dirección|correo)"),
            Convention("Persuasive language", "¡No te lo pierdas! ¡Te esperamos!",
                       r"(¡|no te lo pierdas|gratis|fantástic|increíble|el mejor|la mejor|te esperamos)"),
        ],
        "speech": [
            Convention("Greets the audience", "Buenos días a todos / Queridos compañeros",
                       r"(buenos días|buenas tardes|hola a todos|queridos compañeros|estimad[oa]s|señoras y señores)"),
            Convention("Introduces the topic", "Hoy voy a hablar de…",
                       r"(hoy (voy a|quiero) hablar|quiero hablar|me gustaría hablar|el tema de hoy|vengo a hablar)"),
            Convention("Speaks to the audience", "Use vosotros / ustedes: ¿Sabéis que…?",
                       r"\b(vosotr[oa]s|ustedes|sabéis|pensad|imaginad|os|todos)\b"),
            Convention("Rhetorical question", "Ask a question to make them think", r"\?"),
            Convention("Thanks at the end", "Gracias por vuestra atención",
                       r"(gracias por (su|vuestra) atención|muchas gracias|gracias por escuchar)"),
        ],
    }
    CONNECTORS = {
        "adding": ("además", "también", "y", "asimismo", "incluso"),
        "contrast": ("pero", "sin embargo", "aunque", "en cambio", "por otro lado", "no obstante"),
        "cause": ("porque", "ya que", "puesto que", "debido a"),
        "result": ("por eso", "así que", "por lo tanto", "entonces"),
        "sequence": ("primero", "luego", "después", "más tarde", "finalmente", "por último", "al final"),
        "opinion": ("en mi opinión", "creo que", "pienso que", "me parece que", "para mí", "desde mi punto de vista"),
        "example": ("por ejemplo", "es decir", "en concreto"),
        "time": ("cuando", "mientras", "ayer", "el año pasado", "la semana pasada", "el fin de semana pasado",
                 "en el futuro", "el próximo", "la próxima", "hoy en día"),
    }
    FUNCTION_LABELS = {"adding": "Adding", "contrast": "Contrast", "cause": "Cause", "result": "Result",
                       "sequence": "Sequence", "opinion": "Opinion", "example": "Example", "time": "Time"}
    SUGGEST = {"adding": "además, también", "contrast": "sin embargo, aunque", "cause": "ya que, porque",
               "result": "por eso, así que", "sequence": "primero, luego, por último",
               "opinion": "en mi opinión, creo que", "example": "por ejemplo", "time": "cuando, el año pasado"}
    UPGRADES = {"y": ("además, también, asimismo", None), "pero": ("sin embargo, aunque, en cambio", 3),
                "porque": ("ya que, puesto que, debido a", 3), "entonces": ("por eso, así que, por lo tanto", 2),
                "creo que": ("en mi opinión, me parece que, considero que", 3),
                "después": ("luego, más tarde, a continuación", 3)}
    REGISTER = {
        "tú": r"\b(tú|te|ti|contigo|tu|tus|tienes|eres|estás|puedes|quieres|vienes|sabes|haces|piensas|escríbeme|dime|llámame|cuéntame)\b",
        "usted": r"\b(usted|le escribo|les escribo|le agradecería|su atención|atentamente|le saluda)\b",
        "vosotros": r"\b(vosotr[oa]s|vuestr[oa]s?|tenéis|sabéis|podéis|queréis|habéis|estáis|sois)\b",
    }
    EXPECTED = {"email": "tú", "informal-letter": "tú", "formal-letter": "usted", "blog": "tú",
                "speech": "vosotros"}
    STOPWORDS = frozenset("""para pero porque como este esta esto estos estas muy más también tengo tiene tienes
        hay que con los las una uno unos unas del por mis sus tus nuestro nuestra está estoy estás están cuando
        donde todo todos todas toda mucho mucha muchos muchas sobre entre desde hasta hola gracias somos eres
        ellos ellas nosotros vosotros usted ustedes ser estar soy son fue fui era hace hacer vamos voy además
        luego después siempre nunca algo nada bien mejor aquí allí""".split())
    SYNONYMS = {"bueno": "genial, estupendo, excelente", "buena": "genial, estupenda, excelente",
                "bonito": "precioso, impresionante, bello", "bonita": "preciosa, impresionante, bella",
                "divertido": "entretenido, emocionante, genial", "interesante": "fascinante, curioso",
                "importante": "esencial, fundamental, imprescindible", "malo": "terrible, horrible, fatal",
                "grande": "enorme, amplio", "gusta": "me encanta, me apasiona, disfruto de",
                "cosas": "name the actual things", "cosa": "name the actual thing"}
    PENALTY = {"spanglish": (5, 35), "accent": (2, 16), "punctuation": (2, 10)}
    EXAMPLE = (
        "Hola Marta,\n\n"
        "Como estas? Yo estoy muy bien. Soy 17 años y estoy en mi ultimo año de bachillerato. "
        "En sábado mi amigo y yo fui a la playa y tuvimos un buen tiempo. Hace muy calor en mi ciudad "
        "y la gente son muy simpaticos.\n\n"
        "Me gusto mucho la musica y juego la guitarra en un grupo. Tambien quiero aplicar para un trabajo "
        "en una libreria para ganar dinero, pero es dificil. Mi madre dice que no hace sentido.\n\n"
        "Que vas a hacer en las vacaciones? Que bien, vienes en julio!\n\n"
        "Un abrazo,\nTom"
    )

    def __init__(self):
        self.rules: list[Rule] = [SpanglishRule(), AccentRule(), QuestionWordRule(), OpeningMarkRule()]
        self.tenses = TenseDetector()

    # -- issues -------------------------------------------------------------
    @staticmethod
    def resolve(issues: list[Issue]) -> list[Issue]:
        """Overlaps: keep the earliest, then the longest. Identical spans are merged."""
        merged: dict[tuple[int, int], Issue] = {}
        for i in issues:
            key = (i.start, i.end)
            if key in merged:
                old = merged[key]
                if i.title != old.title:
                    merged[key] = Issue(old.start, old.end, old.kind if old.kind == "punctuation" else i.kind,
                                        f"{old.title} · {i.title}", f"{old.message}<br>{i.message}")
            else:
                merged[key] = i
        ordered = sorted(merged.values(), key=lambda i: (i.start, -(i.end - i.start)))
        kept, last_end = [], -1
        for issue in ordered:
            if issue.start >= last_end:
                kept.append(issue)
                last_end = issue.end
        return kept

    @staticmethod
    def segments(text: str, issues: list[Issue]) -> list[dict]:
        out, pos = [], 0
        for n, issue in enumerate(issues):
            if issue.start > pos:
                out.append({"text": text[pos:issue.start], "issue": None})
            out.append({"text": text[issue.start:issue.end], "issue": n})
            pos = issue.end
        if pos < len(text):
            out.append({"text": text[pos:], "issue": None})
        return out

    # -- other checks -----------------------------------------------------------
    @staticmethod
    def count_words(text: str) -> int:
        return len(re.findall(r"[a-záéíóúüñ0-9]+(?:['’-][a-záéíóúüñ]+)*", text, re.IGNORECASE))

    @staticmethod
    def _count(low: str, phrase: str) -> int:
        return len(re.findall(r"(?<![a-záéíóúüñ])" + re.escape(phrase) + r"(?![a-záéíóúüñ])", low))

    def connectors(self, low: str, words: int) -> dict:
        found = {}
        for func, items in self.CONNECTORS.items():
            hits = [c for c in items if self._count(low, c)]
            if hits:
                found[func] = hits
        missing = [f for f in self.CONNECTORS if f not in found]
        overuse = []
        for word, (better, limit) in self.UPGRADES.items():
            n = self._count(low, word)
            threshold = limit if limit else max(5, words // 18)
            if n >= threshold:
                overuse.append({"word": word, "count": n, "try": better})
        return {"found": found, "missing": missing, "overuse": overuse,
                "labels": self.FUNCTION_LABELS, "suggest": {f: self.SUGGEST[f] for f in missing}}

    def register(self, low: str, text_type: str) -> dict:
        hits = {k: len(re.findall(p, low)) for k, p in self.REGISTER.items()}
        informal = hits["tú"] + hits["vosotros"]
        formal = hits["usted"]
        expected = self.EXPECTED.get(text_type)
        warning = ""
        if informal and formal:
            status, label = "mixed", "Mixed: tú and usted"
            warning = "Pick one register and stick to it: tú (friend) or usted (formal)."
        elif formal:
            status, label = "formal", "Formal (usted)"
            if expected in ("tú", "vosotros"):
                warning = "This text type is usually informal: write to a friend with tú."
        elif informal:
            status, label = "informal", "Informal (tú / vosotros)"
            if expected == "usted":
                warning = "A formal letter needs usted: le escribo, su empresa, atentamente."
        else:
            status, label = "none", "Not clear yet"
        return {"status": status, "label": label, "warning": warning}

    def repeated(self, low: str) -> list[dict]:
        words = [w for w in re.findall(r"[a-záéíóúüñ]+", low) if len(w) >= 4 and w not in self.STOPWORDS]
        counts = Counter(words)
        out = []
        for word, n in counts.most_common(8):
            if n >= 3:
                out.append({"word": word, "count": n, "try": self.SYNONYMS.get(word, "")})
        return out[:5]

    def conventions(self, text: str, text_type: str, tenses: dict) -> list[dict]:
        out = []
        lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
        for conv in self.CONVENTIONS.get(text_type, []):
            if conv.check == "title":
                ok = bool(lines) and len(lines[0].split()) <= 9 and not lines[0].endswith((".", ",")) and len(lines) > 1
            elif conv.check == "signature":
                ok = len(lines) > 1 and 1 <= len(lines[-1].split()) <= 3 and lines[-1][:1].isupper() \
                    and not lines[-1].endswith((".", "?", "!"))
            elif conv.check == "past":
                ok = "preterite" in tenses or "imperfect" in tenses
            else:
                ok = bool(re.search(conv.pattern, text, conv.flags))
            out.append({"label": conv.label, "ok": ok, "hint": conv.hint})
        return out

    # -- the whole analysis -------------------------------------------------------
    def analyse(self, text: str, text_type: str = "email") -> dict:
        text = (text or "").replace("\r\n", "\n")
        if text_type not in self.TEXT_TYPES:
            text_type = "email"
        low = text.lower()
        if len(low) != len(text):  # paranoid: keep offsets valid
            low = "".join(c.lower() if len(c.lower()) == 1 else c for c in text)
        raw = [issue for rule in self.rules for issue in rule.find(text, low)]
        issues = self.resolve(raw)
        words = self.count_words(text)
        tenses = self.tenses.detect(text)
        conventions = self.conventions(text, text_type, tenses)
        connectors = self.connectors(low, words)
        register = self.register(low, text_type)
        repeated = self.repeated(low)
        lo, hi = self.TARGET
        status = "empty" if words == 0 else "short" if words < lo else "long" if words > hi else "ok"
        counts = Counter(i.kind for i in issues)
        result = {
            "type": text_type, "type_label": self.TEXT_TYPES[text_type], "words": words,
            "target": {"min": lo, "max": hi, "status": status},
            "issues": [i.as_dict() for i in issues], "counts": dict(counts),
            "segments": self.segments(text, issues),
            "conventions": conventions, "connectors": connectors,
            "tenses": {"found": tenses, "tip": self.tenses.tip(tenses, words), "names": TenseDetector.NAMES},
            "register": register, "repeated": repeated,
        }
        result["score"] = self.score(result)
        return result

    def score(self, r: dict) -> int:
        words = r["words"]
        if words < 5:
            return 0
        score = 100.0
        for kind, (each, cap) in self.PENALTY.items():
            score -= min(cap, each * r["counts"].get(kind, 0))
        lo, hi = self.TARGET
        if words < lo:
            score -= min(20, (lo - words) * 0.4)
        elif words > hi:
            score -= min(15, (words - hi) * 0.2)
        missing = sum(1 for c in r["conventions"] if not c["ok"])
        score -= min(16, missing * 4)
        covered = len(r["connectors"]["found"])
        score -= max(0, 4 - covered) * 3
        score -= len(r["connectors"]["overuse"]) * 2
        n_tenses = len(r["tenses"]["found"])
        score -= 8 if n_tenses <= 1 else 3 if n_tenses == 2 else 0
        if r["register"]["status"] == "mixed":
            score -= 6
        score -= min(6, 2 * len(r["repeated"]))
        return max(0, min(100, round(score)))
