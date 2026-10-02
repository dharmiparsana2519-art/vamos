"""Individual oral practice: visual stimuli drawn procedurally as SVG, plus prompts.

``SceneArtist`` paints an 800×500 landscape from a seed: a sky gradient, the sun
(with a glow) or the moon, clouds by day or stars by night, three sine-wave hills
(darker towards the front), optional sea, and emoji objects along the ground.
Animated parts carry CSS classes (bob / drift / twinkle / shimmer / glow) that
the page's stylesheet animates — and switches off under reduced motion.
"""
from __future__ import annotations

import html
import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Scene:
    """One visual stimulus."""

    id: str
    theme: str
    title: str
    sky: tuple[str, str]
    night: bool
    land: str
    objects: tuple[str, ...]
    hints: tuple[tuple[str, str], ...]
    questions: tuple[str, ...]
    water: bool = False


class Palette:
    """Tiny colour maths for the scene artist."""

    @staticmethod
    def rgb(color: str) -> tuple[int, int, int]:
        c = color.lstrip("#")
        if len(c) == 3:
            c = "".join(ch * 2 for ch in c)
        return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)

    @staticmethod
    def hex(rgb: tuple[float, float, float]) -> str:
        return "#" + "".join(f"{max(0, min(255, round(v))):02x}" for v in rgb)

    @classmethod
    def mix(cls, a: str, b: str, t: float) -> str:
        ra, rb = cls.rgb(a), cls.rgb(b)
        return cls.hex(tuple(x + (y - x) * t for x, y in zip(ra, rb)))

    @classmethod
    def darken(cls, color: str, t: float) -> str:
        return cls.mix(color, "#000000", t)

    @classmethod
    def lighten(cls, color: str, t: float) -> str:
        return cls.mix(color, "#ffffff", t)


class SceneArtist:
    """Draws a Scene as an SVG string. Same seed + scene = same picture."""

    W, H = 800, 500

    def __init__(self, seed: int):
        self.seed = seed
        self.rng = random.Random(seed)
        self.uid = f"sc{seed % 1_000_000}"   # unique ids so two SVGs can share a page

    # -- pieces -------------------------------------------------------------
    def _wave(self, base: float, amp: float, phase: float, freq: float):
        def y(x: float) -> float:
            t = x / self.W * 2 * math.pi
            return base + amp * math.sin(freq * t + phase) + amp * 0.35 * math.sin(2.3 * freq * t + phase * 1.7)
        return y

    def _hill_path(self, y) -> str:
        pts = " ".join(f"L{x},{y(x):.1f}" for x in range(0, self.W + 1, 10))
        return f"M0,{self.H} {pts} L{self.W},{self.H} Z"

    def _defs(self, scene: Scene, sea: str) -> str:
        u = self.uid
        top, bottom = scene.sky
        glow = "#fff6d5" if not scene.night else "#e9e4ff"
        return f"""<defs>
<linearGradient id="{u}-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>
<radialGradient id="{u}-glow"><stop offset="0" stop-color="{glow}" stop-opacity=".9"/><stop offset=".45" stop-color="{glow}" stop-opacity=".35"/><stop offset="1" stop-color="{glow}" stop-opacity="0"/></radialGradient>
<linearGradient id="{u}-sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{Palette.lighten(sea, .15)}"/><stop offset="1" stop-color="{Palette.darken(sea, .25)}"/></linearGradient>
<filter id="{u}-shadow" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="4" stdDeviation="3" flood-color="#1e1530" flood-opacity=".28"/></filter>
<mask id="{u}-moon"><circle cx="0" cy="0" r="30" fill="#fff"/><circle cx="13" cy="-9" r="27" fill="#000"/></mask>
</defs>"""

    def _sun(self, scene: Scene) -> str:
        x = self.rng.randint(110, 690)
        y = self.rng.randint(70, 140)
        u = self.uid
        if scene.night:
            return (f'<g class="glow"><circle cx="{x}" cy="{y}" r="90" fill="url(#{u}-glow)"/></g>'
                    f'<g transform="translate({x} {y})"><circle r="30" fill="#f6f1ff" mask="url(#{u}-moon)"/></g>')
        core = Palette.mix("#ffd54a", scene.sky[1], .15)
        return (f'<g class="glow"><circle cx="{x}" cy="{y}" r="120" fill="url(#{u}-glow)"/></g>'
                f'<circle cx="{x}" cy="{y}" r="40" fill="{core}"/>'
                f'<circle cx="{x}" cy="{y}" r="40" fill="#fff" opacity=".18"/>')

    def _clouds(self) -> str:
        out = []
        for i in range(self.rng.randint(3, 4)):
            cx = self.rng.randint(40, 760)
            cy = self.rng.randint(55, 190)
            s = self.rng.uniform(.7, 1.25)
            dur = self.rng.randint(38, 70)
            puffs = "".join(
                f'<ellipse cx="{dx * s:.0f}" cy="{dy * s:.0f}" rx="{rx * s:.0f}" ry="{ry * s:.0f}"/>'
                for dx, dy, rx, ry in ((0, 0, 48, 20), (-34, 6, 30, 15), (36, 5, 34, 16), (6, -14, 30, 20)))
            out.append(f'<g class="drift" style="animation-duration:{dur}s;animation-delay:-{i * 9}s">'
                       f'<g transform="translate({cx} {cy})" fill="#fff" opacity=".86">{puffs}</g></g>')
        return "".join(out)

    def _stars(self) -> str:
        out = []
        for _ in range(46):
            x, y = self.rng.randint(5, 795), self.rng.randint(5, 260)
            r = self.rng.choice((.8, 1, 1.2, 1.6, 2))
            d = self.rng.uniform(0, 4)
            out.append(f'<circle class="twinkle" cx="{x}" cy="{y}" r="{r}" fill="#fff" '
                       f'style="animation-delay:-{d:.1f}s"/>')
        return "".join(out)

    def _hills(self, scene: Scene) -> tuple[str, object]:
        land = scene.land
        horizon = scene.sky[1]
        if scene.night:
            land = Palette.darken(land, .35)
            horizon = Palette.darken(horizon, .2)
        colors = [Palette.mix(land, horizon, .55), Palette.mix(land, horizon, .28), land]
        r = self.rng
        back = self._wave(r.randint(285, 315), r.randint(18, 30), r.uniform(0, 6.3), r.uniform(1.2, 2.2))
        mid = self._wave(r.randint(335, 360), r.randint(14, 24), r.uniform(0, 6.3), r.uniform(1.0, 1.8))
        front = self._wave(r.randint(395, 415), r.randint(8, 16), r.uniform(0, 6.3), r.uniform(.8, 1.5))
        parts = [f'<path d="{self._hill_path(back)}" fill="{colors[0]}"/>']
        if scene.water:
            sea_top = 330
            parts.append(f'<rect x="0" y="{sea_top}" width="{self.W}" height="{self.H - sea_top}" '
                         f'fill="url(#{self.uid}-sea)"/>')
            for i in range(7):
                y = sea_top + 12 + i * 11
                x = r.randint(20, 640)
                w = r.randint(60, 150)
                parts.append(f'<path class="shimmer" style="animation-delay:-{i * .6:.1f}s" '
                             f'd="M{x},{y} q{w / 4:.0f},-4 {w / 2:.0f},0 t{w / 2:.0f},0" fill="none" '
                             f'stroke="#fff" stroke-opacity=".55" stroke-width="2" stroke-linecap="round"/>')
            sand = self._wave(r.randint(415, 430), r.randint(6, 10), r.uniform(0, 6.3), r.uniform(.6, 1.1))
            parts.append(f'<path d="{self._hill_path(sand)}" fill="{land}"/>')
            return "".join(parts), sand
        parts.append(f'<path d="{self._hill_path(mid)}" fill="{colors[1]}"/>')
        parts.append(f'<path d="{self._hill_path(front)}" fill="{colors[2]}"/>')
        return "".join(parts), front

    def _objects(self, scene: Scene, ground) -> str:
        items = list(scene.objects)
        n = len(items)
        out = []
        slots = [90 + i * (620 / max(1, n - 1)) for i in range(n)]
        for i, (emoji, x) in enumerate(zip(items, slots)):
            x += self.rng.uniform(-18, 18)
            size = self.rng.randint(46, 62)
            gy = ground(x)
            y = gy + 24 + self.rng.uniform(0, 26)
            out.append(f'<ellipse cx="{x:.0f}" cy="{y + 2:.0f}" rx="{size * .42:.0f}" ry="{size * .09:.0f}" '
                       f'fill="#1e1530" opacity=".18"/>')
            out.append(f'<g class="bob" style="animation-delay:-{i * .55:.2f}s">'
                       f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" text-anchor="middle" '
                       f'filter="url(#{self.uid}-shadow)">{html.escape(emoji)}</text></g>')
        return "".join(out)

    # -- whole picture -------------------------------------------------------
    def draw(self, scene: Scene) -> str:
        sea = Palette.mix("#1f8fd6", scene.sky[0], .25)
        hills, ground = self._hills(scene)
        sky_extra = self._stars() if scene.night else self._clouds()
        title = html.escape(scene.title)
        return (f'<svg class="scene-svg" viewBox="0 0 {self.W} {self.H}" xmlns="http://www.w3.org/2000/svg" '
                f'role="img" aria-label="{title}" preserveAspectRatio="xMidYMid slice">'
                f'{self._defs(scene, sea)}'
                f'<rect width="{self.W}" height="{self.H}" fill="url(#{self.uid}-sky)"/>'
                f'{self._sun(scene)}{sky_extra}{hills}{self._objects(scene, ground)}</svg>')


class OralCoach:
    """Picks a stimulus and bundles everything the oral page needs."""

    SCENES = (
        Scene("comida-familiar", "identities", "Una comida familiar", ("#ffcf99", "#fff0d6"), False, "#79b26a",
              ("👵", "👨", "👧", "🍲", "🥖", "🍉"),
              (("la familia", "family"), ("la comida", "lunch, meal"), ("los abuelos", "grandparents"),
               ("compartir", "to share"), ("charlar", "to chat"), ("al aire libre", "outdoors")),
              ("¿Qué están haciendo las personas de la imagen?",
               "¿Con qué frecuencia comes con toda tu familia?",
               "¿Cuál es tu comida favorita? ¿Por qué?",
               "¿Crees que es importante comer en familia?",
               "Háblame de una comida familiar especial.")),
        Scene("vida-sana", "identities", "Una vida sana", ("#8fd8ff", "#eafbff"), False, "#5daf6c",
              ("🏃", "🚴", "🧘", "🍎", "💧", "🥗"),
              (("hacer ejercicio", "to exercise"), ("correr", "to run"), ("sano", "healthy"),
               ("beber agua", "to drink water"), ("relajarse", "to relax"), ("estar en forma", "to be fit")),
              ("¿Qué hacen las personas de la imagen para estar sanas?",
               "¿Qué haces tú para mantenerte en forma?",
               "¿Crees que los jóvenes de hoy llevan una vida sana?",
               "¿Cuántas horas duermes normalmente?",
               "¿Qué cambiarías de tu dieta?")),
        Scene("playa", "experiences", "Un día en la playa", ("#73c3ff", "#dcf3ff"), False, "#f1d29a",
              ("⛱️", "🏐", "🍦", "🐚", "🏄", "🦀"),
              (("la playa", "beach"), ("el mar", "sea"), ("tomar el sol", "to sunbathe"), ("nadar", "to swim"),
               ("la sombrilla", "sunshade"), ("hace calor", "it's hot")),
              ("¿Qué tiempo hace en la imagen?",
               "¿Qué se puede hacer en esta playa?",
               "¿Prefieres las vacaciones en la playa o en la montaña? ¿Por qué?",
               "¿Adónde fuiste de vacaciones el año pasado?",
               "¿Cómo serían tus vacaciones ideales?"), water=True),
        Scene("fiestas-pueblo", "experiences", "Las fiestas del pueblo", ("#1d1446", "#6b3a8c"), True, "#4b3866",
              ("🎆", "💃", "🎸", "🏮", "🎊", "🥁"),
              (("la fiesta", "party, festival"), ("los fuegos artificiales", "fireworks"), ("bailar", "to dance"),
               ("la música", "music"), ("celebrar", "to celebrate"), ("la tradición", "tradition")),
              ("¿Qué se celebra en la imagen, en tu opinión?",
               "¿Cuál es tu fiesta favorita del año? ¿Por qué?",
               "¿Cómo celebraste tu último cumpleaños?",
               "¿Hay fiestas tradicionales en tu ciudad?",
               "¿Son importantes las tradiciones para los jóvenes?")),
        Scene("estacion-tren", "ingenuity", "En la estación de tren", ("#a9c8ff", "#f4ebff"), False, "#7d9f86",
              ("🚆", "🧳", "🎫", "🕒", "☕", "🗺️"),
              (("el tren", "train"), ("el andén", "platform"), ("el billete", "ticket"), ("la maleta", "suitcase"),
               ("el retraso", "delay"), ("viajar", "to travel")),
              ("¿Dónde ocurre la escena? ¿Adónde crees que va la gente?",
               "¿Cómo vas al colegio normalmente?",
               "¿Qué medio de transporte prefieres para viajar? ¿Por qué?",
               "Háblame de un viaje largo que hiciste.",
               "¿Cómo será el transporte en el futuro?")),
        Scene("conectados", "ingenuity", "Siempre conectados", ("#2c1d63", "#d9677f"), True, "#4a3a6a",
              ("📱", "💻", "🎧", "🎮", "📸", "💬"),
              (("el móvil", "mobile phone"), ("las redes sociales", "social media"), ("conectado", "online"),
               ("la pantalla", "screen"), ("los videojuegos", "video games"), ("chatear", "to chat online")),
              ("¿Qué aparatos ves en la imagen?",
               "¿Cuántas horas al día usas el móvil?",
               "¿Para qué usas las redes sociales?",
               "¿Cuáles son las ventajas y las desventajas de la tecnología?",
               "¿Podrías pasar una semana sin móvil? ¿Por qué?")),
        Scene("barrio", "social", "Ayudar en el barrio", ("#ffc7a6", "#fff2de"), False, "#86b768",
              ("🤝", "🏘️", "🛒", "🌳", "👵", "📦"),
              (("el barrio", "neighbourhood"), ("los vecinos", "neighbours"), ("ayudar", "to help"),
               ("el voluntario", "volunteer"), ("hacer la compra", "to do the shopping"),
               ("las personas mayores", "elderly people")),
              ("¿Qué está pasando en la imagen?",
               "¿Cómo es tu barrio?",
               "¿Has hecho voluntariado alguna vez?",
               "¿Qué se puede hacer para ayudar a los vecinos mayores?",
               "¿Qué cambiarías de tu barrio?")),
        Scene("instituto", "social", "Un día en el instituto", ("#bfe2ff", "#fff6e0"), False, "#6dbd88",
              ("🏫", "📚", "✏️", "🎒", "🧪", "⚽"),
              (("el instituto", "secondary school"), ("la asignatura", "school subject"), ("los deberes", "homework"),
               ("el recreo", "break"), ("estudiar", "to study"), ("los compañeros", "classmates")),
              ("¿Qué objetos ves en la imagen?",
               "¿Cuál es tu asignatura favorita? ¿Por qué?",
               "¿Cómo es un día normal en tu instituto?",
               "¿Qué cambiarías de tu colegio?",
               "¿Qué quieres estudiar en el futuro?")),
        Scene("costa", "planet", "Limpieza de la costa", ("#8ad4ff", "#e6fbff"), False, "#ebd19b",
              ("🐢", "♻️", "🗑️", "🥤", "🧤", "🦀"),
              (("la basura", "rubbish"), ("el plástico", "plastic"), ("reciclar", "to recycle"),
               ("la costa", "coast"), ("proteger", "to protect"), ("el medio ambiente", "the environment")),
              ("¿Qué problema muestra la imagen?",
               "¿Por qué hay tanta basura en las playas?",
               "¿Qué haces tú para proteger el medio ambiente?",
               "¿Reciclas en casa? ¿Qué reciclas?",
               "¿Qué deberían hacer los gobiernos?"), water=True),
        Scene("ola-calor", "planet", "Una ola de calor", ("#ffae66", "#ffe7a8"), False, "#c9a25e",
              ("🌡️", "🌵", "💧", "🥵", "🔥", "🌾"),
              (("la ola de calor", "heatwave"), ("la sequía", "drought"), ("hace mucho calor", "it's very hot"),
               ("el agua", "water"), ("el cambio climático", "climate change"), ("la temperatura", "temperature")),
              ("¿Qué tiempo hace en la imagen?",
               "¿Cómo te sientes cuando hace mucho calor?",
               "¿Cómo es el clima en tu país?",
               "¿Crees que el cambio climático es un problema grave? ¿Por qué?",
               "¿Qué podemos hacer para ahorrar agua?")),
    )

    CONVERSATION = {
        "identities": ("¿Cómo eres? Descríbete.", "¿Cómo es tu mejor amigo o amiga?",
                       "¿Te llevas bien con tu familia?", "¿Qué comes en un día normal?",
                       "¿Qué haces para estar sano o sana?"),
        "experiences": ("¿Qué haces normalmente los fines de semana?", "Describe tu rutina diaria.",
                        "¿Qué hiciste el verano pasado?", "¿Cuál es tu fiesta favorita? ¿Cómo la celebras?",
                        "¿Adónde te gustaría viajar en el futuro?"),
        "ingenuity": ("¿Qué tipo de películas o series te gustan?", "¿Cómo te informas de las noticias?",
                      "¿Podrías vivir sin internet?", "¿Cuál es el mejor invento de la historia, en tu opinión?",
                      "¿Cómo te gustaría viajar en el futuro?"),
        "social": ("¿Cómo es tu barrio? ¿Te gusta vivir allí?", "¿Qué piensas de tu instituto?",
                   "¿En qué te gustaría trabajar en el futuro?", "¿Tienes un trabajo a tiempo parcial?",
                   "¿Cuál es el problema social más grave en tu país?"),
        "planet": ("¿Qué tiempo hace hoy?", "¿Qué haces para proteger el medio ambiente?",
                   "¿Cómo es la geografía de tu país?", "¿Qué problemas globales te preocupan más?",
                   "¿Prefieres vivir en el campo o en la ciudad? ¿Por qué?"),
    }

    STARTERS = {
        "Describe": ("En la imagen veo…", "En primer plano hay…", "Al fondo se ve…",
                     "A la izquierda / a la derecha hay…", "Hace sol y…"),
        "Guess": ("Parece que…", "Creo que…", "Me imagino que…", "Probablemente…", "Tal vez…"),
        "Connect": ("Esto me recuerda a…", "En mi país…", "Cuando era pequeño/a…",
                    "El año pasado yo también…", "A mí también me gusta…"),
        "Opinion": ("En mi opinión…", "Pienso que…", "Me parece que…",
                    "Lo bueno es que… / Lo malo es que…", "Estoy de acuerdo porque…"),
    }

    TIMINGS = {
        "exam": [{"id": "prepare", "label": "Prepare", "secs": 900},
                 {"id": "present", "label": "Present", "secs": 120},
                 {"id": "followup", "label": "Follow-up", "secs": 300},
                 {"id": "conversation", "label": "Conversation", "secs": 300}],
        "quick": [{"id": "prepare", "label": "Prepare", "secs": 180},
                  {"id": "present", "label": "Present", "secs": 60},
                  {"id": "followup", "label": "Follow-up", "secs": 120},
                  {"id": "conversation", "label": "Conversation", "secs": 120}],
    }

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def scenes(self, theme: str | None = None) -> list[Scene]:
        return [s for s in self.SCENES if not theme or s.theme == theme]

    def stimulus(self, theme: str | None = None, exclude: str | None = None) -> dict:
        pool = self.scenes(theme) or list(self.SCENES)
        fresh = [s for s in pool if s.id != exclude] or pool
        scene = self.rng.choice(fresh)
        seed = self.rng.randrange(1, 10 ** 9)
        return {
            "id": scene.id, "theme": scene.theme, "title": scene.title,
            "svg": SceneArtist(seed).draw(scene),
            "hints": [list(h) for h in scene.hints],
            "followups": list(scene.questions),
            "conversation": list(self.CONVERSATION[scene.theme]),
            "starters": {k: list(v) for k, v in self.STARTERS.items()},
            "timings": self.TIMINGS,
        }
