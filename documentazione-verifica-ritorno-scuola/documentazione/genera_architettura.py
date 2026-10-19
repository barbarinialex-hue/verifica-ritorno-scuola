from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 2400, 2820
OUTPUT = Path(__file__).with_name("architettura_sistema.jpg")

COLORS = {
    "background": "#F1F6F3",
    "ink": "#17302D",
    "muted": "#627571",
    "line": "#C6D7CE",
    "green": "#176B59",
    "deep": "#123E37",
    "lime": "#D5EE83",
    "coral": "#DC684C",
    "white": "#FFFFFF",
    "blue": "#24698A",
    "blue_light": "#E6F1F5",
    "gold": "#B77B25",
    "gold_light": "#FBF2DF",
    "gray": "#E8EFEB",
    "external": "#FCEAE5",
}

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_TITLE = ImageFont.truetype(BOLD_PATH, 48)
FONT_SUBTITLE = ImageFont.truetype(FONT_PATH, 25)
FONT_SECTION = ImageFont.truetype(BOLD_PATH, 32)
FONT_NODE = ImageFont.truetype(BOLD_PATH, 25)
FONT_BODY = ImageFont.truetype(FONT_PATH, 20)
FONT_SMALL = ImageFont.truetype(FONT_PATH, 18)
FONT_ARROW = ImageFont.truetype(BOLD_PATH, 22)
FONT_LEGEND = ImageFont.truetype(FONT_PATH, 19)
FONT_LEGEND_BOLD = ImageFont.truetype(BOLD_PATH, 19)

image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["background"])
draw = ImageDraw.Draw(image)


def text_width(text, font):
    return draw.textbbox((0, 0), text, font=font)[2]


def draw_panel(top, height, title, label):
    draw.rounded_rectangle((48, top, WIDTH - 48, top + height), radius=24, fill=COLORS["white"], outline=COLORS["line"], width=3)
    draw.text((82, top + 27), title, fill=COLORS["deep"], font=FONT_SECTION)
    draw.text((WIDTH - 90, top + 35), label, fill=COLORS["muted"], font=FONT_SMALL, anchor="ra")


def draw_box(x, y, width, height, title, lines, fill, accent, small=False):
    draw.rounded_rectangle((x, y, x + width, y + height), radius=18, fill=fill, outline=accent, width=3)
    draw.rounded_rectangle((x, y, x + width, y + 57), radius=16, fill=accent)
    draw.rectangle((x, y + 40, x + width, y + 58), fill=accent)
    draw.text((x + 20, y + 13), title, fill=COLORS["white"], font=FONT_NODE)
    body_font = FONT_SMALL if small else FONT_BODY
    max_width = width - 40
    cursor_y = y + 77
    line_height = 26 if small else 30
    for line in lines:
        wrapped = wrap(line, width=max(20, int(max_width / (12 if small else 11))), break_long_words=False)
        for part in wrapped:
            if text_width(part, body_font) > max_width:
                while text_width(part, body_font) > max_width and len(part) > 8:
                    part = part[:-2] + "…"
            draw.text((x + 20, cursor_y), part, fill=COLORS["ink"], font=body_font)
            cursor_y += line_height
        cursor_y += 4


def draw_arrow(points, number, color, badge):
    draw.line(points, fill=color, width=5, joint="curve")
    start = points[-2]
    end = points[-1]
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux, uy = dx / length, dy / length
    base_x, base_y = end[0] - ux * 18, end[1] - uy * 18
    side = 11
    draw.polygon([
        end,
        (base_x - uy * side, base_y + ux * side),
        (base_x + uy * side, base_y - ux * side),
    ], fill=color)
    bx, by = badge
    radius = 19
    draw.ellipse((bx - radius, by - radius, bx + radius, by + radius), fill=COLORS["white"], outline=color, width=4)
    label = str(number)
    bounds = draw.textbbox((0, 0), label, font=FONT_ARROW)
    draw.text((bx - (bounds[2] - bounds[0]) / 2, by - (bounds[3] - bounds[1]) / 2 - 2), label, fill=color, font=FONT_ARROW)


def draw_legend_item(x, y, number, text, width=1050):
    radius = 16
    draw.ellipse((x, y + 2, x + radius * 2, y + 2 + radius * 2), fill=COLORS["white"], outline=COLORS["green"], width=3)
    value = str(number)
    bounds = draw.textbbox((0, 0), value, font=FONT_LEGEND_BOLD)
    draw.text((x + radius - (bounds[2] - bounds[0]) / 2, y + radius - (bounds[3] - bounds[1]) / 2), value, fill=COLORS["deep"], font=FONT_LEGEND_BOLD)
    lines = wrap(text, width=88, break_long_words=False)
    for index, line in enumerate(lines[:2]):
        draw.text((x + 48, y + index * 25), line, fill=COLORS["ink"], font=FONT_LEGEND)


# Header
draw.rectangle((0, 0, WIDTH, 132), fill=COLORS["deep"])
draw.rectangle((0, 126, WIDTH, 135), fill=COLORS["lime"])
draw.text((70, 24), "ARCHITETTURA — VERIFICA RITORNO SCUOLA", fill=COLORS["white"], font=FONT_TITLE)
draw.text((74, 83), "Vista logica e distribuzione fisica · frecce numerate e legenda", fill="#D3E1DC", font=FONT_SUBTITLE)

# Logical view
draw_panel(155, 865, "1. Architettura logica", "COMPONENTI E INTERAZIONI")
draw_box(85, 390, 310, 245, "Attori", [
    "Cittadino / visitatore",
    "Membro del comitato",
    "Amministratore",
    "Browser desktop o mobile",
], COLORS["blue_light"], COLORS["blue"])
draw_box(500, 285, 620, 470, "Applicazione Flask", [
    "Frontend: HTML/Jinja, CSS, JavaScript, Bootstrap",
    "Autenticazione: registrazione, JWT cookie, Google OAuth",
    "Segnalazioni: CRUD, immagini, coordinate e mappa",
    "Moderazione, dossier, sostegni e ruoli",
    "SQLAlchemy / Flask-Migrate / Flask-WTF / Limiter",
    "Validazione immagini e invio link reset via SMTP",
], "#E7F2EC", COLORS["green"])
draw_box(1285, 350, 340, 225, "MySQL 8", [
    "Utenti e quartieri",
    "Categorie e segnalazioni",
    "Allegati e sostegni",
    "Dossier e associazioni",
], COLORS["gold_light"], COLORS["gold"])
draw_box(1285, 675, 340, 155, "File upload", [
    "JPG / PNG / WebP / video",
    "Percorsi salvati nel DB",
], COLORS["gray"], COLORS["muted"], small=True)
draw.rounded_rectangle((1755, 265, 2290, 885), radius=20, fill="#FAFBFA", outline=COLORS["coral"], width=3)
draw.text((1780, 285), "Servizi esterni", fill=COLORS["deep"], font=FONT_NODE)
draw_box(1780, 345, 480, 100, "OpenStreetMap tiles", ["Cartografia visualizzata nel browser"], COLORS["blue_light"], COLORS["blue"], small=True)
draw_box(1780, 470, 480, 100, "Nominatim", ["Ricerca indirizzi su richiesta"], COLORS["blue_light"], COLORS["blue"], small=True)
draw_box(1780, 595, 225, 110, "Google OAuth", ["Opzionale"], COLORS["external"], COLORS["coral"], small=True)
draw_box(2030, 595, 230, 110, "SMTP", ["Email reset · opzionale"], COLORS["external"], COLORS["coral"], small=True)

draw_arrow([(395, 500), (500, 500)], 1, COLORS["green"], (448, 478))
draw_arrow([(1120, 425), (1285, 425)], 2, COLORS["gold"], (1202, 400))
draw_arrow([(1120, 680), (1190, 680), (1190, 750), (1285, 750)], 3, COLORS["muted"], (1190, 720))
draw_arrow([(395, 610), (445, 900), (1735, 900), (1735, 395), (1780, 395)], 4, COLORS["blue"], (900, 900))
draw_arrow([(395, 630), (455, 930), (1715, 930), (1715, 520), (1780, 520)], 5, COLORS["blue"], (1160, 930))
draw_arrow([(395, 410), (445, 225), (1725, 225), (1725, 650), (1780, 650)], 6, COLORS["coral"], (1440, 225))
draw_arrow([(1120, 735), (1160, 855), (2030, 855), (2030, 705)], 7, COLORS["coral"], (1580, 855))

# Physical view
draw_panel(1040, 900, "2. Architettura fisica", "DEPLOYMENT ATTUALE E ALTERNATIVA DOCKER")
draw_box(85, 1320, 310, 220, "Client", [
    "Browser utente",
    "Internet / HTTPS in produzione",
    "Porta inoltrata Codespaces",
], COLORS["blue_light"], COLORS["blue"])
draw.rounded_rectangle((485, 1120, 1180, 1600), radius=20, fill="#E7F2EC", outline=COLORS["green"], width=4)
draw.text((515, 1140), "GitHub Codespace · /workspaces", fill=COLORS["deep"], font=FONT_NODE)
draw_box(525, 1210, 380, 205, "Flask dev server", [
    "Python · run.py",
    "0.0.0.0:5000",
    "Moduli app/ + static/ + templates/",
], COLORS["white"], COLORS["green"], small=True)
draw_box(935, 1210, 205, 205, "Workspace", [
    "instance/uploads",
    "Persistente in /workspaces",
], COLORS["white"], COLORS["muted"], small=True)
draw_box(1290, 1190, 320, 225, "MySQL remoto", [
    "DATABASE_URL da .env",
    "Schema verifica_ritorno_scuola",
    "Connessione PyMySQL",
], COLORS["gold_light"], COLORS["gold"], small=True)
draw.rounded_rectangle((1745, 1095, 2290, 1615), radius=20, fill="#FAFBFA", outline=COLORS["coral"], width=3)
draw.text((1770, 1115), "Internet · servizi", fill=COLORS["deep"], font=FONT_NODE)
draw_box(1775, 1170, 485, 95, "OpenStreetMap", ["Tile server · browser"], COLORS["blue_light"], COLORS["blue"], small=True)
draw_box(1775, 1280, 485, 95, "Nominatim", ["Geocoding · chiamata esplicita"], COLORS["blue_light"], COLORS["blue"], small=True)
draw_box(1775, 1390, 230, 105, "Google OAuth", ["Solo se configurato"], COLORS["external"], COLORS["coral"], small=True)
draw_box(2020, 1390, 240, 105, "Provider SMTP", ["Solo se configurato"], COLORS["external"], COLORS["coral"], small=True)

draw_arrow([(395, 1390), (525, 1320)], 8, COLORS["green"], (452, 1345))
draw_arrow([(1180, 1240), (1290, 1240)], 9, COLORS["gold"], (1235, 1218))
draw_arrow([(905, 1395), (935, 1395)], 10, COLORS["muted"], (920, 1185))
draw_arrow([(85, 1340), (60, 1340), (60, 1100), (1700, 1100), (1700, 1215), (1775, 1215)], 11, COLORS["blue"], (1000, 1100))
draw_arrow([(395, 1435), (450, 1640), (1700, 1640), (1700, 1325), (1775, 1325)], 12, COLORS["blue"], (1080, 1640))
draw_arrow([(1180, 1135), (1675, 1135), (1675, 1440), (1775, 1440)], 13, COLORS["coral"], (1430, 1135))
draw_arrow([(1180, 1160), (1715, 1160), (1715, 1450), (2020, 1450)], 14, COLORS["coral"], (1510, 1160))

draw.rounded_rectangle((500, 1650, 2250, 1895), radius=18, fill="#F2F3F2", outline=COLORS["muted"], width=3)
draw.text((525, 1668), "Alternativa di deployment · Docker Compose", fill=COLORS["deep"], font=FONT_NODE)
draw_box(530, 1720, 420, 140, "Container web", ["Flask + Gunicorn :8000"], COLORS["white"], COLORS["green"], small=True)
draw_box(1100, 1720, 390, 140, "Container db", ["MySQL 8.4 · rete Compose"], COLORS["gold_light"], COLORS["gold"], small=True)
draw_box(1640, 1720, 250, 140, "Volume uploads", ["File media"], COLORS["white"], COLORS["muted"], small=True)
draw_box(1930, 1720, 285, 140, "Volume mysql_data", ["Dati DB"], COLORS["white"], COLORS["muted"], small=True)
draw_arrow([(950, 1787), (1100, 1787)], 15, COLORS["gold"], (1025, 1765))
draw_arrow([(740, 1860), (740, 1880), (1760, 1880), (1760, 1860)], 16, COLORS["muted"], (1250, 1880))
draw_arrow([(1290, 1860), (1290, 1905), (2070, 1905), (2070, 1860)], 17, COLORS["muted"], (1690, 1905))

# Numbered arrow legend
draw_panel(1980, 760, "Legenda delle frecce", "I NUMERI NEL DIAGRAMMA CORRISPONDONO A QUESTE INTERAZIONI")
logical = [
    "Browser → Flask: richieste HTTP, pagine, filtri e invio form; Flask restituisce HTML/JSON.",
    "Flask → MySQL: query SQL per utenti, segnalazioni, allegati, sostegni e dossier.",
    "Flask → storage: salva/legge immagini e video; nel DB resta il percorso del file.",
    "Browser → OpenStreetMap: scarica tile cartografici e mostra i marker ricevuti dall'app.",
    "Browser → Nominatim: invia l'indirizzo digitato e riceve coordinate per il marker.",
    "Browser ↔ Google OAuth: redirect e ritorno con identità verificata (opzionale).",
    "Flask → SMTP: invio email col link di reset password (opzionale).",
]
physical = [
    "Client → Codespace: traffico web attraverso la porta inoltrata 5000.",
    "Processo Flask → MySQL remoto: connessione configurata da DATABASE_URL nel .env.",
    "Processo Flask → /workspaces: file upload persistenti nella cartella del progetto.",
    "Browser → OSM: richieste tile dirette dal client, con attribuzione e Referer policy.",
    "Browser → Nominatim: geocoding dal browser; il testo indirizzo esce verso il provider.",
    "Codespace → Google: autenticazione facoltativa, se client ID/secret sono impostati.",
    "Codespace → SMTP: email facoltative, se server e mittente sono configurati.",
    "Compose web ↔ db: SQL sulla rete privata Docker, porta 3306.",
    "Container web → volume uploads: persistenza dei file media.",
    "Container db → volume mysql_data: persistenza dei dati MySQL.",
]

legend_start_y = 2065
row_height = 62
for index, text in enumerate(logical, start=1):
    draw_legend_item(85, legend_start_y + (index - 1) * row_height, index, text)
for offset, text in enumerate(physical, start=0):
    draw_legend_item(1235, legend_start_y + offset * row_height, offset + 8, text)

draw.text((80, 2765), "Nota: configurazione corrente in Codespaces usa Flask sulla porta 5000 e MySQL esterno; Docker Compose è un'alternativa documentata.", fill=COLORS["muted"], font=FONT_SMALL)
image.save(OUTPUT, format="JPEG", quality=94, optimize=True, progressive=True)
print(OUTPUT)