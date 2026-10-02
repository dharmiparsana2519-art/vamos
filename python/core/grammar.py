"""Grammar knowledge: noun gender rules, persons, ser/estar and the present tense.

Every wrong option the quiz offers is built here *with its own explanation*,
so feedback can say why a choice is wrong as well as why the answer is right.
"""
from __future__ import annotations

import html
import random
from dataclasses import dataclass
from typing import ClassVar

from .vocab import Spelling, Word


@dataclass
class ChoiceSet:
    """A multiple-choice set: the answer, the options and one explanation each."""

    answer: str
    options: list[str]
    explanations: dict[str, str | None]
    correct_expl: str
    pattern: str


class GenderRules:
    """Decides which rule explains a noun's gender (and so its article)."""

    RULES = {
        "plural": "Plural nouns take los (masculine) or las (feminine). Some words only live in the plural: "
                  "las vacaciones, los deberes, las gafas.",
        "stressed-a": "Feminine nouns that start with a stressed a- (or ha-) take el in the singular, to avoid "
                      "'la a…': el agua, el aula, el hambre. They're still feminine: el agua fría, las aguas.",
        "greek-ma": "Words ending in -ma that come from Greek are masculine: el problema, el clima, "
                    "el programa, el idioma, el tema, el sistema.",
        "masc-a": "A few everyday words end in -a but are masculine: el día, el mapa, el planeta. "
                  "Learn them as exceptions.",
        "fem-o": "A handful of words end in -o but are feminine. La mano is the one you'll meet most.",
        "short": "Shortened words keep the gender of the full word: la foto (la fotografía), la moto "
                 "(la motocicleta), la radio, la tele (la televisión).",
        "dad": "Words ending in -dad, -tad and -tud are feminine: la ciudad, la amistad, la juventud "
               "(and la salud follows the same pattern).",
        "cion": "Words ending in -ción and -sión are always feminine: la información, la televisión.",
        "umbre": "Words ending in -umbre are feminine: la costumbre, la legumbre.",
        "aje": "Words ending in -aje are masculine: el viaje, el paisaje, el mensaje.",
        "or": "Words ending in -or are usually masculine: el ordenador, el calor, el color.",
        "o": "Most nouns ending in -o are masculine: el libro, el barrio, el trabajo.",
        "a": "Most nouns ending in -a are feminine: la casa, la playa, la montaña.",
        "memorise": "The ending doesn't give the gender away, so learn the word together with its article.",
    }
    # Which gender each rule predicts (None = no prediction).
    PREDICTS = {"stressed-a": "f", "greek-ma": "m", "masc-a": "m", "fem-o": "f", "short": "f",
                "dad": "f", "cion": "f", "umbre": "f", "aje": "m", "or": "m", "o": "m", "a": "f"}

    GREEK_MA = frozenset({
        "problema", "clima", "programa", "idioma", "tema", "sistema", "drama", "poema", "esquema",
        "dilema", "panorama", "diploma", "síntoma", "trauma", "aroma", "enigma", "dogma",
        "fantasma", "emblema", "lema", "telegrama", "crucigrama", "diagrama", "prisma", "carisma",
    })
    MASC_A = frozenset({"día", "mapa", "planeta", "sofá", "tranvía", "pijama"})
    FEM_O = frozenset({"mano"})
    SHORT = {"foto": "la fotografía", "moto": "la motocicleta", "radio": "la radiodifusión",
             "tele": "la televisión", "bici": "la bicicleta"}
    FEM_UD = frozenset({"salud"})

    @classmethod
    def _candidate(cls, word: Word) -> str:
        head = word.head
        if word.is_plural:
            return "plural"
        if word.gender == "f" and head in Spelling.STRESSED_A:
            return "stressed-a"
        if head in cls.GREEK_MA:
            return "greek-ma"
        if head in cls.MASC_A:
            return "masc-a"
        if head in cls.FEM_O:
            return "fem-o"
        if head in cls.SHORT:
            return "short"
        if head.endswith(("dad", "tad", "tud")) or head in cls.FEM_UD:
            return "dad"
        if head.endswith(("ción", "sión")):
            return "cion"
        if head.endswith("umbre"):
            return "umbre"
        if head.endswith("aje"):
            return "aje"
        if head.endswith("or"):
            return "or"
        if head.endswith("o"):
            return "o"
        if head.endswith("a"):
            return "a"
        return "memorise"

    @classmethod
    def rule_for(cls, word: Word) -> str:
        """The rule tag for a noun. Falls back to 'memorise' if a rule would mislead
        (e.g. a learner's own 'la flor', which breaks the -or rule)."""
        tag = cls._candidate(word)
        predicted = cls.PREDICTS.get(tag)
        if predicted and word.gender and predicted != word.gender:
            return "memorise"
        return tag

    @classmethod
    def explain(cls, word: Word) -> str:
        tag = cls.rule_for(word)
        if tag == "memorise":
            return f"{cls.RULES['memorise']} So: {word.display}."
        if tag == "short" and word.head in cls.SHORT:
            return f"{cls.RULES['short']} So: {word.display}."
        return f"{cls.RULES[tag]} So: {word.display}."

    @classmethod
    def gender_name(cls, word: Word) -> str:
        name = "masculine" if word.gender == "m" else "feminine"
        return f"{name} plural" if word.is_plural else name


@dataclass(frozen=True)
class Person:
    """A grammatical person: yo, tú, él, nosotros, ellos."""

    code: str
    label: str
    index: int
    subjects: tuple[str, ...]

    _ALL: ClassVar[tuple] = ()  # filled in below
    NEIGHBOURS: ClassVar[dict] = {"yo": "él", "tú": "él", "él": "tú", "nosotros": "ellos", "ellos": "él"}

    @classmethod
    def all(cls) -> tuple["Person", ...]:
        return cls._ALL

    @classmethod
    def get(cls, code: str) -> "Person":
        for p in cls._ALL:
            if p.code == code:
                return p
        raise KeyError(code)

    @classmethod
    def neighbour(cls, code: str) -> "Person":
        """A plausible wrong person for the same subject (used for distractors)."""
        return cls.get(cls.NEIGHBOURS[code])

    @classmethod
    def subject(cls, code: str, rng: random.Random) -> str:
        return rng.choice(cls.get(code).subjects)


Person._ALL = (
    Person("yo", "yo", 0, ("Yo",)),
    Person("tú", "tú", 1, ("Tú",)),
    Person("él", "él / ella", 2, ("Mi hermana", "Mi padre", "Lucía", "El profesor")),
    Person("nosotros", "nosotros", 3, ("Nosotros", "Mi amigo y yo")),
    Person("ellos", "ellos / ellas", 4, ("Mis padres", "Mis amigos", "Ellos", "Los alumnos")),
)


@dataclass
class SerEstarItem:
    """One gap-fill sentence for ser vs estar."""

    sentence: str   # with ___ for the gap
    en: str
    verb: str       # "ser" or "estar"
    person: str     # Person code
    reason: str     # tag in SerEstar.REASONS
    note: str = ""  # an extra teaching point for this sentence

    @property
    def filled(self) -> str:
        return self.sentence.replace("___", SerEstar.FORMS[self.verb][self.person])


class SerEstar:
    """Ser vs estar: forms, reasons and the gap-fill bank."""

    FORMS = {
        "ser": {"yo": "soy", "tú": "eres", "él": "es", "nosotros": "somos", "ellos": "son"},
        "estar": {"yo": "estoy", "tú": "estás", "él": "está", "nosotros": "estamos", "ellos": "están"},
    }
    REASONS = {
        "origin": "Origin and nationality use ser: es de Colombia, somos ingleses.",
        "profession": "Jobs use ser, with no article: es médico, son profesores.",
        "characteristic": "Lasting characteristics (personality, looks) use ser: es alto, son simpáticos.",
        "time": "Days, dates and times use ser: hoy es lunes, son las tres.",
        "event": "Where or when an event takes place uses ser: la fiesta es en mi casa.",
        "identity": "Saying who or what someone is uses ser: es mi mejor amiga.",
        "location": "Where a person, place or thing is uses estar: Madrid está en el centro de España.",
        "emotion": "Feelings and moods use estar: estoy triste, están contentos.",
        "condition": "Temporary states and conditions use estar: el café está frío, estamos cansados.",
        "progressive": "estar + -ando / -iendo describes what's happening right now: están viendo una película.",
    }
    ITEMS = [
        SerEstarItem("Mi profesora ___ de Colombia.", "My teacher is from Colombia.", "ser", "él", "origin"),
        SerEstarItem("Nosotros ___ ingleses.", "We are English.", "ser", "nosotros", "origin"),
        SerEstarItem("Tú ___ de Madrid, ¿verdad?", "You're from Madrid, aren't you?", "ser", "tú", "origin"),
        SerEstarItem("Mi madre ___ enfermera.", "My mum is a nurse.", "ser", "él", "profession"),
        SerEstarItem("Ellos ___ profesores de inglés.", "They are English teachers.", "ser", "ellos", "profession"),
        SerEstarItem("Yo ___ estudiante de bachillerato.", "I'm a sixth-form student.", "ser", "yo", "profession"),
        SerEstarItem("Mis abuelos ___ muy simpáticos.", "My grandparents are very nice.", "ser", "ellos", "characteristic",
                     "Mis abuelos = ellos, so the verb is plural."),
        SerEstarItem("Mi hermano ___ alto y moreno.", "My brother is tall and dark-haired.", "ser", "él", "characteristic"),
        SerEstarItem("Tú ___ muy inteligente.", "You are very intelligent.", "ser", "tú", "characteristic"),
        SerEstarItem("Hoy ___ lunes.", "Today is Monday.", "ser", "él", "time"),
        SerEstarItem("Ya ___ las tres y media.", "It's already half past three.", "ser", "ellos", "time",
                     "Times are plural (son las tres) — except one o'clock: es la una."),
        SerEstarItem("Hoy ___ 3 de mayo.", "Today is 3 May.", "ser", "él", "time"),
        SerEstarItem("La fiesta ___ en mi casa.", "The party is at my house.", "ser", "él", "event"),
        SerEstarItem("El concierto ___ en el estadio.", "The concert is (taking place) in the stadium.", "ser", "él", "event"),
        SerEstarItem("La reunión ___ a las diez.", "The meeting is at ten.", "ser", "él", "event"),
        SerEstarItem("Ella ___ mi mejor amiga.", "She is my best friend.", "ser", "él", "identity"),
        SerEstarItem("¿Tú ___ el hermano de Ana?", "Are you Ana's brother?", "ser", "tú", "identity"),
        SerEstarItem("¿Dónde ___ el baño?", "Where is the bathroom?", "estar", "él", "location"),
        SerEstarItem("Madrid ___ en el centro de España.", "Madrid is in the centre of Spain.", "estar", "él", "location"),
        SerEstarItem("Mi casa ___ cerca del colegio.", "My house is near the school.", "estar", "él", "location"),
        SerEstarItem("Yo ___ en la biblioteca ahora.", "I'm in the library now.", "estar", "yo", "location"),
        SerEstarItem("Yo ___ triste porque mi perro está enfermo.", "I'm sad because my dog is ill.", "estar", "yo", "emotion"),
        SerEstarItem("Mis amigos ___ contentos porque no hay clase.", "My friends are happy because there's no class.", "estar", "ellos", "emotion"),
        SerEstarItem("Tú ___ muy nervioso antes del examen.", "You're very nervous before the exam.", "estar", "tú", "emotion"),
        SerEstarItem("Nosotros ___ muy cansados hoy.", "We are very tired today.", "estar", "nosotros", "condition"),
        SerEstarItem("El café ___ frío.", "The coffee is cold (it has gone cold).", "estar", "él", "condition"),
        SerEstarItem("Las ventanas ___ abiertas.", "The windows are open.", "estar", "ellos", "condition",
                     "Las ventanas = ellas, so the verb is plural."),
        SerEstarItem("¿Cómo ___ tú hoy?", "How are you today?", "estar", "tú", "condition"),
        SerEstarItem("Ellos ___ viendo una película.", "They are watching a film.", "estar", "ellos", "progressive"),
        SerEstarItem("Yo ___ estudiando para el examen.", "I'm studying for the exam.", "estar", "yo", "progressive"),
        SerEstarItem("Nosotros ___ hablando por teléfono.", "We are talking on the phone.", "estar", "nosotros", "progressive"),
    ]

    @classmethod
    def other(cls, verb: str) -> str:
        return "estar" if verb == "ser" else "ser"

    @classmethod
    def choices(cls, item: SerEstarItem) -> ChoiceSet:
        e = html.escape
        right = cls.FORMS[item.verb][item.person]
        other_verb = cls.other(item.verb)
        wrong_verb = cls.FORMS[other_verb][item.person]
        near = Person.neighbour(item.person)
        wrong_person = cls.FORMS[item.verb][near.code]
        both_wrong = cls.FORMS[other_verb][near.code]
        person = Person.get(item.person)
        reason = cls.REASONS[item.reason]
        explanations: dict[str, str | None] = {
            right: None,
            wrong_verb: f"<b>{e(wrong_verb)}</b> is a form of <b>{other_verb}</b>, but this is a "
                        f"<b>{item.verb}</b> sentence. {e(reason)}",
            wrong_person: f"Right verb ({item.verb}), wrong person: <b>{e(wrong_person)}</b> is the "
                          f"{e(near.label)} form. This sentence needs the {e(person.label)} form: "
                          f"<b>{e(right)}</b>.",
            both_wrong: f"<b>{e(both_wrong)}</b> is the wrong verb ({other_verb}) <i>and</i> the wrong "
                        f"person ({e(near.label)}). You need {item.verb} in the {e(person.label)} form.",
        }
        correct = f"<b>{e(right)}</b> is {item.verb}, {e(person.label)} form. {e(reason)}"
        if item.note:
            correct += f" {e(item.note)}"
        return ChoiceSet(right, [right, wrong_verb, wrong_person, both_wrong], explanations,
                         correct, f"serestar:{item.reason}")


@dataclass
class Verb:
    """A regular present-tense verb with a sentence frame that suits any subject."""

    infinitive: str
    en: str
    frame: str   # e.g. "___ en un piso pequeño."

    @property
    def group(self) -> str:
        return self.infinitive[-2:]

    @property
    def stem(self) -> str:
        return self.infinitive[:-2]


class Conjugator:
    """Regular present tense for -ar, -er and -ir verbs."""

    ENDINGS = {
        "ar": {"yo": "o", "tú": "as", "él": "a", "nosotros": "amos", "ellos": "an"},
        "er": {"yo": "o", "tú": "es", "él": "e", "nosotros": "emos", "ellos": "en"},
        "ir": {"yo": "o", "tú": "es", "él": "e", "nosotros": "imos", "ellos": "en"},
    }
    VERBS = [
        Verb("hablar", "to speak", "___ español con los vecinos."),
        Verb("estudiar", "to study", "___ historia por la tarde."),
        Verb("trabajar", "to work", "___ en un hospital."),
        Verb("escuchar", "to listen to", "___ música en el autobús."),
        Verb("bailar", "to dance", "___ salsa los sábados."),
        Verb("cantar", "to sing", "___ en el coro del colegio."),
        Verb("cocinar", "to cook", "___ paella los domingos."),
        Verb("viajar", "to travel", "___ a Francia en verano."),
        Verb("comprar", "to buy", "___ fruta en el mercado."),
        Verb("tomar", "to take", "___ el autobús a las ocho."),
        Verb("ayudar", "to help", "___ en casa los fines de semana."),
        Verb("reciclar", "to recycle", "___ el plástico y el papel."),
        Verb("nadar", "to swim", "___ en la piscina municipal."),
        Verb("visitar", "to visit", "___ a los abuelos en Navidad."),
        Verb("usar", "to use", "___ el ordenador para estudiar."),
        Verb("cenar", "to have dinner", "___ a las nueve de la noche."),
        Verb("desayunar", "to have breakfast", "___ cereales con leche."),
        Verb("necesitar", "to need", "___ un diccionario nuevo."),
        Verb("comer", "to eat", "___ en la cafetería del instituto."),
        Verb("beber", "to drink", "___ mucha agua en verano."),
        Verb("leer", "to read", "___ el periódico en el móvil."),
        Verb("aprender", "to learn", "___ japonés en una academia."),
        Verb("comprender", "to understand", "___ las instrucciones del examen."),
        Verb("correr", "to run", "___ en el parque por la mañana."),
        Verb("vender", "to sell", "___ ropa de segunda mano."),
        Verb("deber", "to have to, must", "___ estudiar más."),
        Verb("creer", "to believe", "___ en la igualdad."),
        Verb("vivir", "to live", "___ en un piso pequeño."),
        Verb("escribir", "to write", "___ correos electrónicos a los clientes."),
        Verb("abrir", "to open", "___ la ventana porque hace calor."),
        Verb("recibir", "to receive", "___ muchos mensajes cada día."),
        Verb("compartir", "to share", "___ fotos en las redes sociales."),
        Verb("decidir", "to decide", "___ el destino de las vacaciones."),
        Verb("subir", "to upload", "___ vídeos a internet."),
        Verb("asistir", "to attend", "___ a clase de baile los martes."),
        Verb("discutir", "to argue, to discuss", "___ de política durante la cena."),
        Verb("describir", "to describe", "___ la imagen en el examen oral."),
    ]

    @classmethod
    def ending(cls, group: str, person: str) -> str:
        return cls.ENDINGS[group][person]

    @classmethod
    def conjugate(cls, verb: Verb, person: str) -> str:
        return verb.stem + cls.ending(verb.group, person)

    @classmethod
    def find(cls, infinitive: str) -> Verb | None:
        for v in cls.VERBS:
            if v.infinitive == infinitive:
                return v
        return None

    @classmethod
    def verbs_in_group(cls, group: str) -> list[Verb]:
        return [v for v in cls.VERBS if v.group == group]

    @classmethod
    def wrong_groups(cls, group: str, person: str) -> list[str]:
        """Other verb groups, most tempting slip first (vivemos for vivimos)."""
        if group == "ar":
            return ["er", "ir"]
        if person == "nosotros":
            return ["ir", "ar"] if group == "er" else ["er", "ar"]
        return ["ar", "ir" if group == "er" else "er"]

    @classmethod
    def rule(cls, verb: Verb, person: str) -> str:
        """'viv + es = vives'"""
        return f"{verb.stem} + {cls.ending(verb.group, person)} = {cls.conjugate(verb, person)}"

    @classmethod
    def choices(cls, verb: Verb, person: str, rng: random.Random) -> ChoiceSet:
        e = html.escape
        right = cls.conjugate(verb, person)
        p = Person.get(person)
        options = [right]
        explanations: dict[str, str | None] = {right: None}

        near = Person.neighbour(person)
        near_form = cls.conjugate(verb, near.code)
        if near_form not in options:
            options.append(near_form)
            explanations[near_form] = (
                f"<b>{e(near_form)}</b> is the {e(near.label)} form ({e(cls.rule(verb, near.code))}). "
                f"This subject needs the {e(p.label)} form: <b>{e(cls.rule(verb, person))}</b>.")

        for group in cls.wrong_groups(verb.group, person):
            form = verb.stem + cls.ending(group, person)
            if form not in options:
                options.append(form)
                explanations[form] = (
                    f"<b>{e(form)}</b> uses the -{group} ending -{cls.ending(group, person)}, but "
                    f"{e(verb.infinitive)} is an <b>-{verb.group}</b> verb: <b>{e(cls.rule(verb, person))}</b>.")
                break

        others = [q for q in Person.all() if q.code not in (person, near.code)]
        rng.shuffle(others)
        for q in others:
            if len(options) >= 4:
                break
            form = cls.conjugate(verb, q.code)
            if form not in options:
                options.append(form)
                explanations[form] = (
                    f"<b>{e(form)}</b> is the {e(q.label)} form. "
                    f"This subject needs the {e(p.label)} form: <b>{e(cls.rule(verb, person))}</b>.")

        correct = (f"<b>{e(right)}</b>: {e(verb.infinitive)} is an -{verb.group} verb, so for "
                   f"{e(p.label)} it's <b>{e(cls.rule(verb, person))}</b>.")
        return ChoiceSet(right, options, explanations, correct, f"verbs:{verb.group}")
