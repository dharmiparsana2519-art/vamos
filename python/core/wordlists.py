"""Compact extra word lists, one theme per entry.

Format (parsed by ``WordListParser`` in vocab.py)::

    ## Topic name                 <- sets the topic for the lines below
    spanish | english | kind      <- one word per line

Kind codes:
    m    masculine noun           f    feminine noun
    mpl  masculine plural noun    fpl  feminine plural noun
    v    verb                     adj  adjective
    adv  adverb                   phr  fixed phrase

Write nouns WITHOUT their article: the gender code supplies it.
Spain Spanish is the default (ordenador, móvil, coche, zumo, patata).
Any Spanish word that is already in the bank is skipped automatically.
"""

LISTS = {
    # ------------------------------------------------------------------
    "identities": """
## Personal attributes
nombre | name | m
apellido | surname | m
edad | age | f
nacionalidad | nationality | f
personalidad | personality | f
carácter | character, nature | m
ojo | eye | m
nariz | nose | f
bajo | short (height) | adj
delgado | slim, thin | adj
fuerte | strong | adj
guapo | good-looking | adj
feo | ugly | adj
rubio | blond, fair-haired | adj
moreno | dark-haired, dark-skinned | adj
pelirrojo | red-haired | adj
largo | long | adj
corto | short (length) | adj
rizado | curly | adj
liso | straight (hair) | adj
barba | beard | f
bigote | moustache | m
inteligente | intelligent | adj
trabajador | hard-working | adj
perezoso | lazy | adj
tímido | shy | adj
divertido | fun, funny | adj
serio | serious | adj
antipático | unfriendly, unpleasant | adj
generoso | generous | adj
amable | kind | adj
hablador | chatty, talkative | adj
creativo | creative | adj
joven | young | adj
mayor | older, elderly | adj
alegre | cheerful | adj
orgulloso | proud | adj
parecerse a | to look like | phr
llamarse | to be called | v

## Personal relationships
familia | family | f
madre | mother | f
padre | father | m
hermana | sister | f
hijo | son | m
hija | daughter | f
abuelo | grandfather | m
abuela | grandmother | f
tío | uncle | m
tía | aunt | f
primo | cousin (male) | m
prima | cousin (female) | f
sobrino | nephew | m
marido | husband | m
mujer | woman, wife | f
pareja | partner, couple | f
novio | boyfriend | m
novia | girlfriend | f
amigo | friend | m
relación | relationship | f
gemelo | twin | m
hijo único | only child | m
casado | married | adj
soltero | single, unmarried | adj
divorciado | divorced | adj
discutir | to argue | v
confiar | to trust | v
conocer | to know (a person), to meet | v
llevarse mal | to get on badly | phr
compartir | to share | v
apoyar | to support | v
nacer | to be born | v
mascota | pet | f
perro | dog | m
gato | cat | m

## Eating and drinking
comida | food, meal, lunch | f
cena | dinner, evening meal | f
almuerzo | lunch | m
merienda | afternoon snack | f
pan | bread | m
leche | milk | f
huevo | egg | m
queso | cheese | m
jamón | ham | m
pollo | chicken | m
arroz | rice | m
verdura | vegetables | f
fruta | fruit | f
manzana | apple | f
naranja | orange | f
plátano | banana | m
tomate | tomato | m
patata | potato | f
ensalada | salad | f
sopa | soup | f
postre | dessert | m
azúcar | sugar | m
sal | salt | f
zumo | juice | m
café | coffee | m
té | tea | m
refresco | soft drink | m
bebida | drink | f
vaso | glass (for drinking) | m
botella | bottle | f
restaurante | restaurant | m
camarero | waiter | m
cuenta | bill | f
receta | recipe | f
comida rápida | fast food | f
cocinar | to cook | v
beber | to drink | v
comer | to eat | v
probar | to try, to taste | v
pedir | to order, to ask for | v
delicioso | delicious | adj
picante | spicy | adj
dulce | sweet | adj
vegetariano | vegetarian | adj

## Physical well-being
cuerpo | body | m
cabeza | head | f
brazo | arm | m
pierna | leg | f
pie | foot | m
espalda | back | f
estómago | stomach | m
diente | tooth | m
garganta | throat | f
corazón | heart | m
enfermedad | illness, disease | f
dolor | pain, ache | m
fiebre | fever, temperature | f
gripe | flu | f
resfriado | cold (illness) | m
farmacia | chemist's, pharmacy | f
medicamento | medicine | m
hospital | hospital | m
ejercicio | exercise | m
dieta | diet | f
sueño | sleep, dream | m
estrés | stress | m
cita | appointment, date | f
vida sana | healthy lifestyle | f
enfermo | ill, sick | adj
cansado | tired | adj
equilibrado | balanced | adj
dormir | to sleep | v
descansar | to rest | v
adelgazar | to lose weight | v
engordar | to put on weight | v
fumar | to smoke | v
en forma | fit, in shape | phr
""",
    # ------------------------------------------------------------------
    "experiences": """
## Daily routine
mañana | morning (also: tomorrow) | f
tarde | afternoon, evening | f
noche | night | f
hora | hour, time | f
semana | week | f
mes | month | m
año | year | m
reloj | clock, watch | m
despertador | alarm clock | m
tareas domésticas | housework | fpl
lunes | Monday | m
sábado | Saturday | m
domingo | Sunday | m
despertarse | to wake up | v
ducharse | to have a shower | v
vestirse | to get dressed | v
peinarse | to comb your hair | v
prepararse | to get ready | v
acostarse | to go to bed | v
desayunar | to have breakfast | v
almorzar | to have lunch | v
cenar | to have dinner | v
lavarse los dientes | to brush your teeth | phr
temprano | early | adv
siempre | always | adv
a menudo | often | adv
a veces | sometimes | adv
nunca | never | adv
normalmente | usually | adv
luego | then, later | adv
después | afterwards, after | adv
antes | before | adv

## Leisure
tiempo libre | free time | m
pasatiempo | hobby, pastime | m
deporte | sport | m
equipo | team | m
partido | match, game | m
piscina | swimming pool | f
gimnasio | gym | m
polideportivo | sports centre | m
parque | park | m
guitarra | guitar | f
entrada | ticket (for a show) | f
museo | museum | m
ajedrez | chess | m
senderismo | hiking | m
nadar | to swim | v
leer | to read | v
bailar | to dance | v
cantar | to sing | v
pasear | to go for a walk | v
quedar | to meet up | v
salir | to go out | v
dibujar | to draw | v
pintar | to paint | v
ir de compras | to go shopping | phr
montar en bici | to ride a bike | phr
aburrido | boring, bored | adj
emocionante | exciting | adj
relajante | relaxing | adj

## Holidays
equipaje | luggage | m
maleta | suitcase | f
pasaporte | passport | m
hotel | hotel | m
camping | campsite | m
albergue | hostel | m
alojamiento | accommodation | m
habitación | room, bedroom | f
extranjero | abroad (also: foreigner) | m
crema solar | sun cream | f
recuerdo | souvenir, memory | m
postal | postcard | f
excursión | trip, excursion | f
destino | destination | m
temporada alta | high season | f
vista | view | f
sombrilla | sunshade, beach umbrella | f
reservar | to book | v
visitar | to visit | v
tomar el sol | to sunbathe | phr
hacer turismo | to go sightseeing | phr
hacer la maleta | to pack your suitcase | phr
pasarlo bien | to have a good time | phr
inolvidable | unforgettable | adj
precioso | lovely, beautiful | adj

## Festivals and celebrations
Navidad | Christmas | f
Nochevieja | New Year's Eve | f
Año Nuevo | New Year | m
Semana Santa | Holy Week, Easter | f
Reyes Magos | the Three Kings | mpl
Carnaval | carnival | m
boda | wedding | f
regalo | present, gift | m
tarta | cake | f
vela | candle | f
invitado | guest | m
disfraz | costume, fancy dress | m
desfile | parade | m
fuegos artificiales | fireworks | mpl
tradición | tradition | f
feria | fair, festival | f
procesión | procession | f
santo | saint's day | m
uva | grape | f
villancico | Christmas carol | m
invitar | to invite | v
felicitar | to congratulate | v
disfrazarse | to dress up | v
reunirse | to get together | v
brindar | to make a toast | v
cumplir años | to have a birthday | phr
tradicional | traditional | adj
religioso | religious | adj
""",
    # ------------------------------------------------------------------
    "ingenuity": """
## Transport
tren | train | m
autobús | bus | m
metro | underground, metro | m
bicicleta | bicycle | f
barco | boat, ship | m
camión | lorry, truck | m
taxi | taxi | m
estación | station | f
aeropuerto | airport | m
vuelo | flight | m
parada | stop (bus) | f
andén | platform | m
horario | timetable | m
pasajero | passenger | m
retraso | delay | m
tráfico | traffic | m
atasco | traffic jam | m
carretera | road | f
gasolina | petrol | f
conducir | to drive | v
tomar | to take (transport) | v
llegar | to arrive | v
aparcar | to park | v
perder el tren | to miss the train | phr
a pie | on foot | phr
de ida y vuelta | return (ticket) | phr
lento | slow | adj
rápido | fast, quick | adj
cómodo | comfortable | adj

## Entertainment
cine | cinema | m
teatro | theatre | m
concierto | concert | m
canción | song | f
música | music | f
grupo | band, group | m
serie | series | f
videojuego | video game | m
actor | actor | m
actriz | actress | f
dibujos animados | cartoons | mpl
comedia | comedy | f
documental | documentary | m
concurso | quiz show, competition | m
pantalla | screen | f
escenario | stage | m
estreno | premiere, release | m
butaca | seat (in a theatre) | f
taquilla | box office | f
divertirse | to have fun | v
escuchar | to listen to | v
ver | to watch, to see | v
aplaudir | to clap | v
gracioso | funny | adj
entretenido | entertaining | adj
famoso | famous | adj

## Media
revista | magazine | f
prensa | the press | f
anuncio | advert | m
publicidad | advertising | f
artículo | article | m
titular | headline | m
entrevista | interview | f
canal | channel | m
emisora | radio station | f
presentador | presenter | m
medios de comunicación | the media | mpl
noticias falsas | fake news | fpl
opinión | opinion | f
público | audience, public | m
seguidor | follower | m
blog | blog | m
podcast | podcast | m
comentario | comment | m
tema | topic, theme | m
reportaje | report, feature | m
informar | to inform, to report | v
publicar | to publish | v
suscribirse | to subscribe | v
fiable | reliable | adj
falso | false, fake | adj

## Technology
red | network, the net | f
portátil | laptop | m
tableta | tablet | f
teclado | keyboard | m
ratón | mouse | m
aplicación | app | f
correo electrónico | email | m
página web | website | f
buscador | search engine | m
archivo | file | m
batería | battery | f
conexión | connection | f
usuario | user | m
sistema | system | m
inteligencia artificial | artificial intelligence | f
robot | robot | m
invento | invention | m
cámara | camera | f
auriculares | headphones | mpl
videollamada | video call | f
enviar | to send | v
buscar | to look for, to search | v
subir | to upload, to go up | v
guardar | to save, to keep | v
cargar | to charge, to load | v
inventar | to invent | v
digital | digital | adj
adicto | addicted | adj
útil | useful | adj
peligroso | dangerous | adj
""",
    # ------------------------------------------------------------------
    "social": """
## Neighbourhood
pueblo | village, small town | m
casa | house, home | f
piso | flat, floor | m
edificio | building | m
vecino | neighbour | m
plaza | square | f
tienda | shop | f
supermercado | supermarket | m
mercado | market | m
biblioteca | library | f
ayuntamiento | town hall | m
iglesia | church | f
banco | bank, bench | m
centro comercial | shopping centre | m
ruido | noise | m
ambiente | atmosphere | m
afueras | outskirts | fpl
zona verde | green space | f
semáforo | traffic lights | m
puente | bridge | m
mudarse | to move house | v
alquilar | to rent | v
cerca de | near | phr
lejos de | far from | phr
al lado de | next to | phr
enfrente de | opposite | phr
tranquilo | quiet, calm | adj
ruidoso | noisy | adj
limpio | clean | adj
sucio | dirty | adj
seguro | safe, sure | adj
peatonal | pedestrian | adj

## Education
instituto | secondary school | m
universidad | university | f
profesor | teacher | m
alumno | pupil, student | m
examen | exam | m
nota | mark, grade | f
clase | class, lesson | f
recreo | break (at school) | m
uniforme | uniform | m
pizarra | board | f
cuaderno | exercise book | m
libro | book | m
mochila | school bag, backpack | f
matemáticas | maths | fpl
ciencias | science | fpl
historia | history, story | f
inglés | English (language) | m
educación física | PE | f
intercambio | exchange | m
bachillerato | upper secondary, sixth form | m
horario escolar | school timetable | m
aprobar | to pass (an exam) | v
suspender | to fail (an exam) | v
estudiar | to study | v
aprender | to learn | v
enseñar | to teach, to show | v
repasar | to revise | v
sacar buenas notas | to get good marks | phr
difícil | difficult | adj
fácil | easy | adj
obligatorio | compulsory | adj

## The workplace
empleo | job, employment | m
empresa | company, business | f
oficina | office | f
fábrica | factory | f
puesto | position, post | m
jornada laboral | working day | f
contrato | contract | m
currículum | CV | m
experiencia | experience | f
entrevista de trabajo | job interview | f
compañero | colleague, classmate | m
cliente | customer, client | m
dinero | money | m
abogado | lawyer | m
enfermero | nurse | m
ingeniero | engineer | m
dependiente | shop assistant | m
cocinero | cook, chef | m
prácticas | work experience, internship | fpl
reunión | meeting | f
carrera | career, degree | f
formación | training | f
trabajar | to work | v
ganar | to earn, to win | v
ahorrar | to save (money) | v
jubilarse | to retire | v
a tiempo parcial | part-time | phr
a tiempo completo | full-time | phr
bien pagado | well paid | phr
exigente | demanding | adj

## Social issues
desempleo | unemployment | m
desigualdad | inequality | f
racismo | racism | m
discriminación | discrimination | f
violencia | violence | f
acoso escolar | bullying | m
ciberacoso | cyberbullying | m
droga | drug | f
alcohol | alcohol | m
delincuencia | crime | f
inmigración | immigration | f
derecho | right, law | m
voluntario | volunteer | m
voluntariado | volunteering | m
solidaridad | solidarity | f
injusticia | injustice | f
sociedad | society | f
juventud | youth, young people | f
tercera edad | old age, senior citizens | f
comedor social | soup kitchen | m
ley | law | f
gobierno | government | m
respetar | to respect | v
luchar | to fight, to struggle | v
votar | to vote | v
sin techo | homeless | phr
pobre | poor | adj
rico | rich | adj
justo | fair | adj
grave | serious | adj
""",
    # ------------------------------------------------------------------
    "planet": """
## Climate
tiempo | weather, time | m
sol | sun | m
lluvia | rain | f
nieve | snow | f
viento | wind | m
nube | cloud | f
tormenta | storm | f
temperatura | temperature | f
grado | degree | m
calor | heat | m
frío | cold | m
primavera | spring | f
verano | summer | m
otoño | autumn | m
invierno | winter | m
estación del año | season | f
ola de calor | heatwave | f
calentamiento global | global warming | m
inundación | flood | f
huracán | hurricane | m
pronóstico | forecast | m
nevar | to snow | v
hace frío | it's cold (weather) | phr
húmedo | humid, damp | adj
seco | dry | adj
caluroso | hot (day, climate) | adj
nublado | cloudy | adj
soleado | sunny | adj
templado | mild, temperate | adj

## Physical geography
isla | island | f
costa | coast | f
lago | lake | m
bosque | forest, wood | m
selva | jungle, rainforest | f
desierto | desert | m
volcán | volcano | m
valle | valley | m
campo | countryside, field | m
colina | hill | f
sierra | mountain range | f
océano | ocean | m
cueva | cave | f
ola | wave | f
norte | north | m
sur | south | m
este | east | m
oeste | west | m
continente | continent | m
frontera | border | f
país | country | m
región | region | f
tierra | earth, land, soil | f
piedra | stone | f
arena | sand | f
montañoso | mountainous | adj
llano | flat | adj
situado | located, situated | adj

## The environment
planeta | planet | m
reciclaje | recycling | m
plástico | plastic | m
vidrio | glass (material) | m
papel | paper | m
residuos | waste | mpl
contenedor | recycling bin, container | m
bolsa | bag | f
envase | packaging | m
aire | air | m
árbol | tree | m
animal | animal | m
especie | species | f
transporte público | public transport | m
huella de carbono | carbon footprint | f
deforestación | deforestation | f
paneles solares | solar panels | mpl
proteger | to protect | v
reutilizar | to reuse | v
reducir | to reduce | v
malgastar | to waste | v
contaminar | to pollute | v
apagar | to switch off, to turn off | v
ahorrar energía | to save energy | phr
ecológico | eco-friendly, ecological | adj
sostenible | sustainable | adj
renovable | renewable | adj

## Global issues
paz | peace | f
refugiado | refugee | m
crisis | crisis | f
derechos humanos | human rights | mpl
población | population | f
recursos | resources | mpl
agua potable | drinking water | f
escasez | shortage, lack | f
desarrollo | development | m
terremoto | earthquake | m
incendio | fire (blaze) | m
catástrofe | disaster | f
emergencia | emergency | f
ayuda humanitaria | humanitarian aid | f
extinción | extinction | f
vacuna | vaccine | f
pandemia | pandemic | f
desnutrición | malnutrition | f
analfabetismo | illiteracy | m
mundo | world | m
futuro | future | m
donar | to donate | v
sobrevivir | to survive | v
solidario | caring, supportive | adj
mundial | global, worldwide | adj
urgente | urgent | adj
""",
}
