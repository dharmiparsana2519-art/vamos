"""Vocabulary: words, themes, false friends and the shared word bank.

Everything here is plain data plus small, well-tested behaviour:
articles (el agua!), plurals, stable keys and the compact list parser.
"""
from __future__ import annotations

import datetime as _dt
import re
import unicodedata
from dataclasses import dataclass, field

from .wordlists import LISTS


class Spelling:
    """Spanish spelling knowledge shared by the vocabulary classes."""

    # Feminine nouns that start with a stressed a-/ha- take "el" in the singular.
    STRESSED_A = frozenset({
        "agua", "aula", "hambre", "área", "arma", "alma", "águila", "hacha",
        "hada", "ave", "ancla", "asma", "haba", "habla", "alga", "ala",
        "arpa", "asa", "aria", "alba", "ánima", "hampa",
    })
    PLURAL_IRREGULAR = {
        "carácter": "caracteres", "régimen": "regímenes", "jersey": "jerséis",
        "espécimen": "especímenes", "club": "clubes",
    }
    # Pluralising a phrase stops at the first of these (fin de semana -> fines de semana).
    FUNCTION_WORDS = frozenset({"de", "del", "a", "al", "en", "con", "para", "por", "sin", "y", "o"})
    INVARIABLE = frozenset({"web", "wifi", "clave", "estrella"})  # páginas web, palabras clave
    VOWELS = "aeiouáéíóúü"
    ACCENTED = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u"}
    ADD_ACCENT = {"a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú"}

    @staticmethod
    def strip_accents(text: str) -> str:
        """'canción' -> 'cancion' (keeps ñ)."""
        out = []
        for ch in text:
            if ch in "ñÑ":
                out.append(ch)
                continue
            out.append("".join(c for c in unicodedata.normalize("NFD", ch)
                               if unicodedata.category(c) != "Mn"))
        return "".join(out)

    @staticmethod
    def slug(text: str) -> str:
        """A readable, stable id: lower case, spaces to '-', accents kept."""
        low = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.UNICODE)
        return re.sub(r"[\s_]+", "-", low.strip())

    @classmethod
    def syllables(cls, word: str) -> int:
        """Rough syllable count: groups of vowels (good enough for plurals)."""
        return max(1, len(re.findall(r"[aeiouáéíóúü]+", word.lower())))

    @classmethod
    def _last_vowel(cls, word: str) -> int:
        for i in range(len(word) - 1, -1, -1):
            if word[i].lower() in cls.VOWELS:
                return i
        return -1

    @classmethod
    def plural_of(cls, word: str) -> str:
        """Plural of a single Spanish noun or adjective."""
        low = word.lower()
        if low in cls.PLURAL_IRREGULAR:
            return cls.PLURAL_IRREGULAR[low]
        if not low:
            return word
        last = low[-1]
        if last in "aeiou" or last in "áéó":
            return word + "s"
        if last in "íú":
            return word + "s"
        if last == "z":
            return word[:-1] + "ces"
        if last in "sx":
            i = cls._last_vowel(word)
            if i >= 0 and word[i] in cls.ACCENTED:
                return cls._drop_accent_unless_hiatus(word, i) + "es"
            if cls.syllables(word) == 1 and last == "s":
                return word + "es"
            return word  # el lunes / los lunes, la crisis / las crisis
        if last in "lnrdjy":
            i = cls._last_vowel(word)
            if i >= 0 and word[i] in cls.ACCENTED and last == "n":
                return cls._drop_accent_unless_hiatus(word, i) + "es"
            if last == "n" and cls.syllables(word) > 1 and not any(c in cls.ACCENTED for c in word):
                # examen -> exámenes, joven -> jóvenes: the stress moves back a syllable.
                j = cls._last_vowel(word[:-2]) if low.endswith(("en", "an", "in", "on", "un")) else -1
                if j >= 0:
                    return word[:j] + cls.ADD_ACCENT.get(word[j], word[j]) + word[j + 1:] + "es"
            return word + "es"
        return word + "s"  # blog -> blogs, robot -> robots

    @classmethod
    def _drop_accent_unless_hiatus(cls, word: str, i: int) -> str:
        ch = word[i]
        if ch in "íú" and i > 0 and word[i - 1].lower() in "aeo":
            return word  # país -> países, baúl -> baúles
        return word[:i] + cls.ACCENTED[ch] + word[i + 1:]

    @classmethod
    def plural_phrase(cls, phrase: str) -> str:
        """Pluralise every word up to the first function word."""
        out, stop = [], False
        for i, part in enumerate(phrase.split()):
            if not stop and part.lower() in cls.FUNCTION_WORDS:
                stop = True
            keep = stop or (i > 0 and part.lower() in cls.INVARIABLE)
            out.append(part if keep else cls.plural_of(part))
        return " ".join(out)


@dataclass(frozen=True)
class Word:
    """One vocabulary item. Immutable, so it can be shared safely."""

    es: str
    en: str
    gender: str | None
    topic: str
    example_es: str = ""
    example_en: str = ""
    tip: str = ""
    kind: str = ""          # noun / verb / adjective / adverb / phrase
    is_plural: bool = False
    custom: bool = False

    KIND_LABELS = {"noun": "noun", "verb": "verb", "adjective": "adjective",
                   "adverb": "adverb", "phrase": "phrase"}

    @property
    def head(self) -> str:
        """The first word, lower-cased: it decides the article ('agua potable' -> 'agua')."""
        return self.es.split()[0].lower() if self.es.strip() else ""

    @property
    def is_noun(self) -> bool:
        return self.gender in ("m", "f")

    @property
    def plural(self) -> str:
        if self.is_plural or not self.is_noun:
            return self.es
        return Spelling.plural_phrase(self.es)

    @property
    def article(self) -> str:
        if not self.is_noun:
            return ""
        if self.is_plural:
            return "los" if self.gender == "m" else "las"
        if self.gender == "f" and self.head in Spelling.STRESSED_A:
            return "el"  # el agua, el aula, el hambre
        return "el" if self.gender == "m" else "la"

    @property
    def display(self) -> str:
        return f"{self.article} {self.es}" if self.article else self.es

    @property
    def key(self) -> str:
        base = Spelling.slug(self.es)
        return f"u-{base}" if self.custom else base

    @property
    def label(self) -> str:
        """What the flip card shows above the word: the article, or the word type."""
        if self.article:
            return self.article
        return self.KIND_LABELS.get(self.kind, "my word" if self.custom else "word")

    @property
    def has_example(self) -> bool:
        return bool(self.example_es.strip())


@dataclass
class Theme:
    """One of the five IB themes (or the learner's own 'My words')."""

    slug: str
    name: str
    name_es: str
    emoji: str
    colors: tuple[str, str]
    topics: list[str]
    words: list[Word] = field(default_factory=list)

    def known_count(self, known: set[str]) -> int:
        return sum(1 for w in self.words if w.key in known)

    def gradient(self, angle: int = 135) -> str:
        return f"linear-gradient({angle}deg, {self.colors[0]}, {self.colors[1]})"


@dataclass(frozen=True)
class FalseFriend:
    """A Spanish word that looks like an English one but means something else."""

    es: str
    meaning: str
    trap: str
    note: str


class WordListParser:
    """Parses the compact 'spanish | english | kind' lists in wordlists.py."""

    KINDS = {
        "m": ("m", "noun", False), "f": ("f", "noun", False),
        "mpl": ("m", "noun", True), "fpl": ("f", "noun", True),
        "v": (None, "verb", False), "adj": (None, "adjective", False),
        "adv": (None, "adverb", False), "phr": (None, "phrase", False),
    }

    def __init__(self, default_topic: str = ""):
        self.default_topic = default_topic

    def parse(self, text: str) -> list[Word]:
        topic = self.default_topic
        words: list[Word] = []
        for number, raw in enumerate(text.splitlines(), 1):
            line = raw.strip()
            if not line:
                continue
            if line.startswith("##"):
                topic = line[2:].strip()
                if not topic:
                    raise ValueError(f"Line {number}: '##' heading has no topic name")
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 3 or not all(parts):
                raise ValueError(
                    f"Line {number}: expected 'spanish | english | kind' but got {raw.strip()!r}")
            es, en, code = parts
            if code not in self.KINDS:
                raise ValueError(
                    f"Line {number}: unknown kind {code!r} in {raw.strip()!r} "
                    f"(use one of: {' '.join(self.KINDS)})")
            if not topic:
                raise ValueError(f"Line {number}: {es!r} comes before any '## Topic' heading")
            words.append(self.make(es, en, code, topic))
        return words

    @classmethod
    def make(cls, es: str, en: str, code: str, topic: str,
             example_es: str = "", example_en: str = "", tip: str = "") -> Word:
        if code not in cls.KINDS:
            raise ValueError(f"Unknown kind code {code!r} for {es!r}")
        gender, kind, plural = cls.KINDS[code]
        return Word(es, en, gender, topic, example_es, example_en, tip, kind, plural)


def W(es: str, en: str, code: str, topic: str,
      example_es: str = "", example_en: str = "", tip: str = "") -> Word:
    """Tiny constructor for the hand-written 'rich' words below."""
    return WordListParser.make(es, en, code, topic, example_es, example_en, tip)


class VocabularyBank:
    """All themes, the false friends, and the learner's own words ('mine')."""

    def __init__(self) -> None:
        self._themes: dict[str, Theme] = {}
        self._false_friends: list[FalseFriend] = []
        self.mine = Theme("mine", "My words", "Mis palabras", "⭐",
                          ("#f7b32b", "#e84a6f"), ["My words"], [])
        self._index: dict[str, Word] | None = None

    # -- themes -------------------------------------------------------
    @property
    def themes(self) -> dict[str, Theme]:
        return dict(self._themes)

    def add_theme(self, theme: Theme) -> None:
        self._themes[theme.slug] = theme
        self._index = None

    def theme(self, slug: str) -> Theme | None:
        if slug == "mine":
            return self.mine
        return self._themes.get(slug)

    def extend_theme(self, slug: str, words: list[Word]) -> int:
        """Add words to a theme, skipping any Spanish word already in the bank."""
        theme = self._themes[slug]
        seen = {w.es.lower() for w in self.all_words(include_mine=False)}
        added = 0
        for word in words:
            if word.es.lower() in seen:
                continue
            theme.words.append(word)
            seen.add(word.es.lower())
            added += 1
        self._index = None
        return added

    def set_mine(self, words: list[Word]) -> None:
        self.mine.words = list(words)
        self._index = None

    # -- false friends ---------------------------------------------------
    @property
    def false_friends(self) -> list[FalseFriend]:
        return list(self._false_friends)

    def add_false_friend(self, ff: FalseFriend) -> bool:
        if any(f.es == ff.es for f in self._false_friends):
            return False
        self._false_friends.append(ff)
        return True

    # -- lookups -----------------------------------------------------------
    def all_words(self, include_mine: bool = True) -> list[Word]:
        words = [w for t in self._themes.values() for w in t.words]
        if include_mine:
            words += self.mine.words
        return words

    def find(self, key: str) -> Word | None:
        if self._index is None:
            self._index = {w.key: w for w in self.all_words()}
        return self._index.get(key)

    def theme_of(self, word: Word) -> Theme | None:
        if word.custom:
            return self.mine
        for theme in self._themes.values():
            if word.topic in theme.topics:
                return theme
        return None

    def nouns(self, include_mine: bool = True) -> list[Word]:
        return [w for w in self.all_words(include_mine) if w.is_noun]

    def word_of_the_day(self, day: _dt.date) -> Word:
        """Same word all day, different word each day. Built-in words only,
        preferring the 'rich' ones that come with an example sentence."""
        pool = [w for w in self.all_words(include_mine=False) if w.has_example]
        pool = pool or self.all_words(include_mine=False)
        pool.sort(key=lambda w: w.key)
        return pool[(day.toordinal() * 37) % len(pool)]

    def total(self, include_mine: bool = False) -> int:
        return len(self.all_words(include_mine))


class BankBuilder:
    """Builds the populated BANK: theme metadata, rich words, lists, false friends."""

    THEMES = [
        ("identities", "Identities", "Identidades", "🧑", ("#ff6b35", "#e84a6f"),
         ["Personal attributes", "Personal relationships", "Eating and drinking", "Physical well-being"]),
        ("experiences", "Experiences", "Experiencias", "🎉", ("#f7b32b", "#ff6b35"),
         ["Daily routine", "Leisure", "Holidays", "Festivals and celebrations"]),
        ("ingenuity", "Human Ingenuity", "Ingenio humano", "💡", ("#8a4fd0", "#4b6cf0"),
         ["Transport", "Entertainment", "Media", "Technology"]),
        ("social", "Social Organization", "Organización social", "🏘️", ("#e84a6f", "#6c3a8c"),
         ["Neighbourhood", "Education", "The workplace", "Social issues"]),
        ("planet", "Sharing the Planet", "Compartir el planeta", "🌍", ("#12a594", "#3a86ff"),
         ["Climate", "Physical geography", "The environment", "Global issues"]),
    ]

    RICH = {
        "identities": [
            W("alto", "tall", "adj", "Personal attributes",
              "Mi padre es alto y delgado.", "My dad is tall and slim.",
              "Looks use ser: es alto. Adjectives agree with the person: alto, alta, altos, altas."),
            W("pelo", "hair", "m", "Personal attributes",
              "Tengo el pelo largo y rizado.", "I have long, curly hair.",
              "Describe hair with tener + el pelo: tengo el pelo corto. It sounds more natural than 'mi pelo es corto'."),
            W("gafas", "glasses", "fpl", "Personal attributes",
              "Mi hermano lleva gafas.", "My brother wears glasses.",
              "Always plural: las gafas. Llevar = to wear. In Latin America you'll also hear los lentes or los anteojos."),
            W("simpático", "nice, friendly", "adj", "Personal attributes",
              "Mi profesora es muy simpática.", "My teacher is really nice.",
              "Not 'sympathetic'! It means nice or friendly. The opposite is antipático."),
            W("hermano", "brother", "m", "Personal relationships",
              "Mi hermano mayor se llama Pablo.", "My older brother is called Pablo.",
              "Los hermanos can mean 'brothers' or 'brothers and sisters'. ¿Tienes hermanos? = Do you have any siblings?"),
            W("padres", "parents", "mpl", "Personal relationships",
              "Mis padres están divorciados.", "My parents are divorced.",
              "Los padres = mum and dad. Careful: los parientes means relatives, not parents."),
            W("amistad", "friendship", "f", "Personal relationships",
              "Nuestra amistad es muy importante para mí.", "Our friendship is very important to me.",
              "Words ending in -dad and -tad are always feminine: la amistad, la ciudad, la libertad."),
            W("llevarse bien", "to get on well", "phr", "Personal relationships",
              "Me llevo muy bien con mi hermana.", "I get on really well with my sister.",
              "Reflexive: me llevo, te llevas, se lleva… + con + person. The opposite is llevarse mal."),
            W("agua", "water", "f", "Eating and drinking",
              "El agua del grifo es potable.", "Tap water is safe to drink.",
              "Feminine, but it takes el because it starts with a stressed a-: el agua fría (the adjective stays feminine), las aguas."),
            W("desayuno", "breakfast", "m", "Eating and drinking",
              "El desayuno es a las siete y media.", "Breakfast is at half past seven.",
              "The verb is desayunar: desayuno cereales. Then la comida (lunch) and la cena (dinner)."),
            W("carne", "meat", "f", "Eating and drinking",
              "No como carne porque soy vegetariana.", "I don't eat meat because I'm vegetarian.",
              "The -e ending doesn't show the gender, so learn la carne. No article after ser for labels: soy vegetariana."),
            W("pescado", "fish (as food)", "m", "Eating and drinking",
              "Los viernes comemos pescado.", "On Fridays we eat fish.",
              "El pescado is fish on your plate; el pez is a live fish swimming in the water."),
            W("tener sed", "to be thirsty", "phr", "Eating and drinking",
              "Tengo mucha sed. ¿Hay agua?", "I'm really thirsty. Is there any water?",
              "Spanish 'has' thirst: tener sed, tener hambre, tener calor. Sed is a noun, so say mucha sed, never 'muy sed'."),
            W("mano", "hand", "f", "Physical well-being",
              "Me duele la mano derecha.", "My right hand hurts.",
              "Ends in -o but it's feminine: la mano. The classic exception, so learn it with its article."),
            W("salud", "health", "f", "Physical well-being",
              "Hacer deporte es bueno para la salud.", "Doing sport is good for your health.",
              "Feminine, like the -tud words (la juventud, la actitud). ¡Salud! also means 'cheers!' and 'bless you!'."),
            W("doler", "to hurt", "v", "Physical well-being",
              "Me duelen los pies.", "My feet hurt.",
              "Works like gustar: me duele la cabeza (one thing), me duelen los pies (plural). Stem change: o → ue."),
            W("médico", "doctor", "m", "Physical well-being",
              "Mañana tengo que ir al médico.", "Tomorrow I have to go to the doctor's.",
              "a + el = al: voy al médico. A female doctor is la médica."),
            W("sano", "healthy", "adj", "Physical well-being",
              "Llevo una vida sana: duermo ocho horas.", "I lead a healthy life: I sleep eight hours.",
              "Sano describes people and lifestyles; saludable is common for food and habits. Both work in una dieta sana / saludable."),
        ],
        "experiences": [
            W("día", "day", "m", "Daily routine",
              "Todos los días me levanto a las siete.", "Every day I get up at seven.",
              "Ends in -a but it's masculine: el día, buenos días. A must-know exception."),
            W("levantarse", "to get up", "v", "Daily routine",
              "Los sábados me levanto tarde.", "On Saturdays I get up late.",
              "Reflexive verb: me levanto, te levantas, se levanta… The pronoun goes before the conjugated verb."),
            W("rutina", "routine", "f", "Daily routine",
              "Mi rutina diaria es bastante aburrida.", "My daily routine is quite boring.",
              "Order your routine with connectors: primero, luego, después, por último."),
            W("fin de semana", "weekend", "m", "Leisure",
              "El fin de semana voy al cine con mis amigos.", "At the weekend I go to the cinema with my friends.",
              "No 'en' needed: el fin de semana = at the weekend; el sábado = on Saturday."),
            W("jugar al fútbol", "to play football", "phr", "Leisure",
              "Juego al fútbol dos veces a la semana.", "I play football twice a week.",
              "Jugar a + sport (a + el = al): juego al tenis. Instruments use tocar instead: toco la guitarra."),
            W("tocar", "to play (an instrument), to touch", "v", "Leisure",
              "Toco la guitarra desde hace tres años.", "I've been playing the guitar for three years.",
              "Instruments always use tocar, never jugar. Desde hace + time = for (and still going)."),
            W("vacaciones", "holidays", "fpl", "Holidays",
              "Las vacaciones de verano son muy largas.", "The summer holidays are very long.",
              "Always plural: las vacaciones. Ir de vacaciones = to go on holiday."),
            W("viaje", "trip, journey", "m", "Holidays",
              "El viaje en tren duró seis horas.", "The train journey took six hours.",
              "Words ending in -aje are masculine: el viaje, el equipaje, el paisaje. ¡Buen viaje! = Have a good trip!"),
            W("foto", "photo", "f", "Holidays",
              "Saqué muchas fotos en la playa.", "I took lots of photos on the beach.",
              "Short for la fotografía, so it stays feminine despite the -o. Sacar or hacer una foto = to take a photo."),
            W("mapa", "map", "m", "Holidays",
              "Necesitamos un mapa de la ciudad.", "We need a map of the city.",
              "Ends in -a but it's masculine: el mapa. Learn it with el día and el planeta."),
            W("playa", "beach", "f", "Holidays",
              "El verano pasado fuimos a la playa todos los días.", "Last summer we went to the beach every day.",
              "Fuimos is the preterite of ir (and of ser!). Context tells you which: fuimos a la playa = we went."),
            W("alojarse", "to stay (in accommodation)", "v", "Holidays",
              "Nos alojamos en un hotel cerca del mar.", "We stayed in a hotel near the sea.",
              "You can also say quedarse: nos quedamos en un camping. Cerca de + el = cerca del."),
            W("fiesta", "party, festival", "f", "Festivals and celebrations",
              "La fiesta es en mi casa el sábado.", "The party is at my house on Saturday.",
              "Where an event takes place uses ser, not estar: la fiesta es en mi casa."),
            W("costumbre", "custom, tradition", "f", "Festivals and celebrations",
              "Es costumbre comer doce uvas en Nochevieja.", "It's a custom to eat twelve grapes on New Year's Eve.",
              "Words ending in -umbre are feminine: la costumbre, la legumbre, la cumbre."),
            W("cumpleaños", "birthday", "m", "Festivals and celebrations",
              "¡Feliz cumpleaños! ¿Cuántos años cumples?", "Happy birthday! How old are you turning?",
              "Same form in singular and plural: el cumpleaños, los cumpleaños. Cumplir años = to have a birthday."),
            W("Día de los Muertos", "Day of the Dead", "m", "Festivals and celebrations",
              "El Día de los Muertos se celebra en México el 1 y el 2 de noviembre.",
              "The Day of the Dead is celebrated in Mexico on 1 and 2 November.",
              "Masculine because of el día. Families build altars (ofrendas) to remember their loved ones."),
            W("celebrar", "to celebrate", "v", "Festivals and celebrations",
              "Celebramos la Navidad en casa de mis abuelos.", "We celebrate Christmas at my grandparents' house.",
              "Navidad ends in -dad, so it's feminine: la Navidad, ¡Feliz Navidad!"),
        ],
        "ingenuity": [
            W("moto", "motorbike", "f", "Transport",
              "Mi hermano va al trabajo en moto.", "My brother goes to work by motorbike.",
              "Short for la motocicleta, so it's feminine despite the -o. Transport uses en (en moto, en tren), but a pie = on foot."),
            W("coche", "car", "m", "Transport",
              "Prefiero ir en coche porque es más rápido.", "I prefer to go by car because it's quicker.",
              "Spain says el coche; in Latin America you'll hear el carro or el auto."),
            W("billete", "ticket (for travel)", "m", "Transport",
              "Un billete de ida y vuelta a Madrid, por favor.", "A return ticket to Madrid, please.",
              "Spain: el billete. Latin America: el boleto. A ticket for a show or a match is una entrada."),
            W("avión", "plane", "m", "Transport",
              "Viajar en avión contamina mucho.", "Travelling by plane causes a lot of pollution.",
              "It ends in -ión but not -ción or -sión, and it's masculine: el avión. The accent drops in the plural: los aviones."),
            W("tele", "TV", "f", "Entertainment",
              "Por la noche vemos la tele en familia.", "In the evening we watch TV as a family.",
              "Short for la televisión (-sión words are feminine), so it's la tele. Ver la tele = to watch TV."),
            W("programa", "programme", "m", "Entertainment",
              "Mi programa favorito es un concurso de cocina.", "My favourite programme is a cooking competition.",
              "Words ending in -ma that come from Greek are masculine: el programa, el problema, el tema, el sistema."),
            W("película", "film", "f", "Entertainment",
              "Anoche vimos una película de terror.", "Last night we watched a horror film.",
              "Types: una película de acción, de terror, de ciencia ficción, romántica. Vimos = we watched (ver)."),
            W("radio", "radio", "f", "Media",
              "Escucho la radio en el coche.", "I listen to the radio in the car.",
              "Short for la radiodifusión, so it's feminine in Spain: la radio. (Parts of Latin America say el radio.)"),
            W("información", "information", "f", "Media",
              "Busco información en internet.", "I look up information online.",
              "Words ending in -ción are always feminine: la información, la canción. The accent drops in the plural: las canciones."),
            W("noticias", "news", "fpl", "Media",
              "Veo las noticias todas las noches.", "I watch the news every night.",
              "Usually plural: las noticias. Una noticia = one piece of news."),
            W("periódico", "newspaper", "m", "Media",
              "Mi abuelo lee el periódico cada mañana.", "My grandad reads the newspaper every morning.",
              "El periódico = newspaper. A journalist is el periodista or la periodista."),
            W("redes sociales", "social media", "fpl", "Media",
              "Paso demasiado tiempo en las redes sociales.", "I spend too much time on social media.",
              "La red = the network (or the net). In the plural the adjective agrees too: las redes sociales."),
            W("móvil", "mobile phone", "m", "Technology",
              "No puedo vivir sin mi móvil.", "I can't live without my phone.",
              "Spain: el móvil. Latin America: el celular."),
            W("ordenador", "computer", "m", "Technology",
              "Hago los deberes en el ordenador.", "I do my homework on the computer.",
              "Spain: el ordenador. Latin America: la computadora. Words ending in -or are usually masculine."),
            W("mensaje", "message", "m", "Technology",
              "Te mando un mensaje esta tarde.", "I'll send you a message this afternoon.",
              "Words ending in -aje are masculine: el mensaje, el viaje, el paisaje."),
            W("descargar", "to download", "v", "Technology",
              "Descargo música para escucharla sin conexión.", "I download music to listen to it offline.",
              "Related verbs: subir (to upload), compartir (to share), buscar (to search)."),
            W("contraseña", "password", "f", "Technology",
              "Es importante tener una contraseña segura.", "It's important to have a secure password.",
              "Es importante + infinitive is a great phrase for giving advice in Paper 1."),
        ],
        "social": [
            W("barrio", "neighbourhood", "m", "Neighbourhood",
              "Mi barrio es tranquilo, pero no hay mucho que hacer.", "My neighbourhood is quiet, but there isn't much to do.",
              "Hay = there is and there are. No hay mucho que hacer = there isn't much to do."),
            W("ciudad", "city, town", "f", "Neighbourhood",
              "Vivo en una ciudad grande del norte.", "I live in a big city in the north.",
              "Words ending in -dad are feminine: la ciudad, la universidad, la comunidad."),
            W("calle", "street", "f", "Neighbourhood",
              "Mi casa está en una calle peatonal.", "My house is on a pedestrian street.",
              "Location uses estar: mi casa está en… The -e ending doesn't give the gender away: la calle."),
            W("colegio", "school", "m", "Education",
              "Voy al colegio en autobús.", "I go to school by bus.",
              "Colegio = school, not college! In Spain, el instituto is secondary school and la universidad is university."),
            W("asignatura", "school subject", "f", "Education",
              "Mi asignatura favorita es la historia.", "My favourite subject is history.",
              "Subjects take the article: me gusta la historia, me encantan las matemáticas (plural → encantan)."),
            W("idioma", "language", "m", "Education",
              "Hablo tres idiomas: inglés, español y francés.", "I speak three languages: English, Spanish and French.",
              "A Greek -ma word, so masculine: el idioma. Language names are lower case: el español."),
            W("aula", "classroom", "f", "Education",
              "El aula de ciencias está en el primer piso.", "The science classroom is on the first floor.",
              "Feminine, but el aula (stressed a-). The adjective stays feminine: el aula nueva. Plural: las aulas."),
            W("deberes", "homework", "mpl", "Education",
              "Esta noche tengo muchos deberes de matemáticas.", "Tonight I have lots of maths homework.",
              "Always plural in Spain: los deberes. Hacer los deberes = to do your homework. Latin America: la tarea."),
            W("trabajo", "work, job", "m", "The workplace",
              "Mi madre busca trabajo desde hace un año.", "My mum has been looking for work for a year.",
              "Buscar already means 'to look for', so no 'para': busco trabajo."),
            W("sueldo", "salary, wages", "m", "The workplace",
              "El sueldo es bajo, pero el trabajo es interesante.", "The pay is low, but the work is interesting.",
              "Also el salario. Ganar = to earn: gana mil euros al mes."),
            W("solicitar", "to apply for", "v", "The workplace",
              "Voy a solicitar un puesto de camarero.", "I'm going to apply for a job as a waiter.",
              "Don't say 'aplicar para' (Spanglish!). Apply for a job = solicitar un trabajo or un puesto."),
            W("jefe", "boss", "m", "The workplace",
              "Mi jefe es muy exigente.", "My boss is very demanding.",
              "A female boss is la jefa. Exigente = demanding."),
            W("paro", "unemployment", "m", "Social issues",
              "Muchos jóvenes están en el paro.", "Lots of young people are unemployed.",
              "Spain: estar en el paro = to be unemployed. Elsewhere you'll hear el desempleo."),
            W("problema", "problem", "m", "Social issues",
              "El desempleo es un problema muy grave.", "Unemployment is a very serious problem.",
              "Ends in -a, but it's masculine because it comes from Greek: el problema, like el tema and el sistema."),
            W("pobreza", "poverty", "f", "Social issues",
              "La pobreza afecta a millones de personas.", "Poverty affects millions of people.",
              "Afectar a + people: la crisis afecta a los jóvenes."),
            W("igualdad", "equality", "f", "Social issues",
              "Luchamos por la igualdad entre hombres y mujeres.", "We fight for equality between men and women.",
              "-dad → feminine: la igualdad. Luchar por = to fight for."),
            W("ayudar", "to help", "v", "Social issues",
              "Los sábados ayudo en un comedor social.", "On Saturdays I help out at a soup kitchen.",
              "Ayudar a + person: ayudo a mi abuela. A volunteer is un voluntario or una voluntaria."),
        ],
        "planet": [
            W("clima", "climate", "m", "Climate",
              "El clima de mi región es templado.", "The climate in my region is mild.",
              "A Greek -ma word, so masculine: el clima. For today's weather use el tiempo: hace buen tiempo."),
            W("hace calor", "it's hot (weather)", "phr", "Climate",
              "En agosto hace mucho calor.", "In August it's very hot.",
              "Weather uses hacer: hace calor, hace frío, hace sol. Calor is a noun, so mucho calor — never 'muy calor' or 'el tiempo es caliente'."),
            W("llover", "to rain", "v", "Climate",
              "En el norte llueve mucho en invierno.", "In the north it rains a lot in winter.",
              "Stem change o → ue: llueve. La lluvia = the rain. Está lloviendo = it's raining right now."),
            W("sequía", "drought", "f", "Climate",
              "La sequía es un problema grave en el sur de España.", "Drought is a serious problem in the south of Spain.",
              "Say it in three syllables: se-quí-a. The accent keeps the í and the a apart."),
            W("paisaje", "landscape", "m", "Physical geography",
              "El paisaje de la sierra es impresionante.", "The mountain landscape is stunning.",
              "Words ending in -aje are masculine: el paisaje, el viaje, el mensaje."),
            W("montaña", "mountain", "f", "Physical geography",
              "Subimos a la montaña más alta de la región.", "We climbed the highest mountain in the region.",
              "Superlatives: la montaña más alta de… = the highest mountain in… (use de, not en)."),
            W("río", "river", "m", "Physical geography",
              "El río Ebro pasa por Zaragoza.", "The River Ebro flows through Zaragoza.",
              "Rivers are masculine: el Ebro, el Amazonas. Don't forget the accent: río."),
            W("mar", "sea", "m", "Physical geography",
              "Vivo cerca del mar.", "I live near the sea.",
              "de + el = del: cerca del mar. (Poets and sailors sometimes say la mar.)"),
            W("naturaleza", "nature", "f", "Physical geography",
              "Me encanta pasar tiempo en la naturaleza.", "I love spending time in nature.",
              "Words ending in -eza are feminine: la naturaleza, la pobreza, la belleza."),
            W("contaminación", "pollution", "f", "The environment",
              "La contaminación del aire es peor en las ciudades.", "Air pollution is worse in cities.",
              "Words ending in -ción are always feminine. Contaminar = to pollute."),
            W("reciclar", "to recycle", "v", "The environment",
              "En casa reciclamos el plástico y el vidrio.", "At home we recycle plastic and glass.",
              "El reciclaje = recycling (-aje → masculine). Reutilizar = to reuse."),
            W("medio ambiente", "the environment", "m", "The environment",
              "Tenemos que proteger el medio ambiente.", "We have to protect the environment.",
              "Tener que + infinitive = to have to. A strong phrase for Paper 1."),
            W("basura", "rubbish", "f", "The environment",
              "Hay mucha basura en la playa.", "There's a lot of rubbish on the beach.",
              "Usually uncountable: la basura. Tirar la basura = to throw away or take out the rubbish."),
            W("energía", "energy", "f", "The environment",
              "En mi casa usamos energía solar.", "At home we use solar energy.",
              "Renewable energy = la energía renovable: solar, eólica (wind). Stress: e-ner-gí-a."),
            W("hambre", "hunger", "f", "Global issues",
              "El hambre sigue siendo un problema en el mundo.", "Hunger is still a problem in the world.",
              "Feminine, but el hambre (stressed a-). The adjective stays feminine: tengo mucha hambre."),
            W("cambio climático", "climate change", "m", "Global issues",
              "El cambio climático es el mayor reto de nuestra generación.",
              "Climate change is the biggest challenge of our generation.",
              "Climático agrees with cambio (masculine). El mayor reto = the biggest challenge."),
            W("guerra", "war", "f", "Global issues",
              "Muchas familias huyen de la guerra.", "Many families flee from war.",
              "Huir de = to flee from. Its opposite, la paz, is feminine too, even though it ends in -z."),
        ],
    }

    FALSE_FRIENDS = [
        FalseFriend("embarazada", "pregnant", "embarrassed",
                    "Embarrassed = avergonzado/a, or say 'me da vergüenza'."),
        FalseFriend("éxito", "success", "exit",
                    "Exit = la salida. Tener éxito = to be successful."),
        FalseFriend("librería", "bookshop", "library",
                    "Library = la biblioteca."),
        FalseFriend("carpeta", "folder", "carpet",
                    "Carpet = la alfombra."),
        FalseFriend("actual", "current, present-day", "actual, real",
                    "Real = real or verdadero. Actually = en realidad. Actualmente = currently."),
        FalseFriend("realizar", "to carry out, to achieve", "to realise",
                    "To realise = darse cuenta de: me di cuenta de que era tarde."),
        FalseFriend("constipado", "having a cold", "constipated",
                    "Estoy constipado = I've got a cold. Constipated = estreñido."),
        FalseFriend("sensible", "sensitive", "sensible",
                    "Sensible = sensato/a or razonable."),
        FalseFriend("molestar", "to bother, to annoy", "to molest",
                    "It's an everyday verb: ¿Te molesta la música? = Does the music bother you?"),
        FalseFriend("asistir", "to attend", "to assist",
                    "To help = ayudar. Asisto a clase = I attend class."),
        FalseFriend("recordar", "to remember, to remind", "to record",
                    "To record = grabar."),
        FalseFriend("pariente", "relative", "parent",
                    "Parents = los padres. Mis parientes = my relatives."),
        FalseFriend("ropa", "clothes", "rope",
                    "Rope = la cuerda."),
        FalseFriend("soportar", "to put up with, to stand", "to support",
                    "To support = apoyar. No soporto el ruido = I can't stand the noise."),
        FalseFriend("introducir", "to insert, to put in", "to introduce (a person)",
                    "To introduce someone = presentar: te presento a mi amiga Ana."),
    ]

    @classmethod
    def build(cls) -> VocabularyBank:
        bank = VocabularyBank()
        for slug, name, name_es, emoji, colors, topics in cls.THEMES:
            bank.add_theme(Theme(slug, name, name_es, emoji, colors, list(topics),
                                 list(cls.RICH.get(slug, []))))
        for slug, text in LISTS.items():
            bank.extend_theme(slug, WordListParser().parse(text))
        for ff in cls.FALSE_FRIENDS:
            bank.add_false_friend(ff)
        return bank


BANK = BankBuilder.build()
