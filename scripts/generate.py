#!/usr/bin/env python3
"""
Profile asset generator for github.com/pavanvinjamara
------------------------------------------------------
Written from scratch, Python standard library only (no pip installs, no
third-party GitHub Actions). Produces theme-aware SVGs in ./dist:

  header.svg                      animated banner
  btn-*.svg                       CV / contact buttons
  snake-{light,dark}.svg          snake that eats your contribution graph
  stats-{light,dark}.svg          GitHub stats + streaks + top languages
  stack-{light,dark}.svg          tech-stack card with logos

If a network call fails, the previous file is kept, so the README never breaks.
"""
import base64, datetime as dt, html, json, os, re, sys, urllib.request
from collections import deque

# ───────────────────────── profile config ─────────────────────────
USER = os.environ.get("GH_USER", "pavanvinjamara")
NAME = "Pavan Kumar Vinjamara"
TITLE = "Full Stack Java Developer"
ROLES = ["Java + Spring Boot Microservices", "React.js | Vue.js | Node.js",
         "Kafka | Redis | PostgreSQL | AWS", "3+ years shipping production systems"]

STACK = [
    ("Backend", [("java", "Java"), ("spring", "Spring Boot"), ("si-springsecurity", "Spring Security"),
                 ("hibernate", "Hibernate"), ("nodejs", "Node.js"), ("express", "Express.js")]),
    ("Frontend", [("html5", "HTML5"), ("css3", "CSS3"), ("javascript", "JavaScript"), ("typescript", "TypeScript"),
                  ("react", "React.js"), ("redux", "Redux"), ("vuejs", "Vue.js"), ("si-pinia", "Pinia"),
                  ("nextjs", "Next.js"), ("tailwind", "Tailwind"), ("bootstrap", "Bootstrap"), ("chartjs", "Chart.js")]),
    ("Data & Messaging", [("postgresql", "PostgreSQL"), ("mongodb", "MongoDB"), ("redis", "Redis"),
                          ("kafka", "Kafka"), ("socketio", "Socket.io")]),
    ("Cloud & DevOps", [("aws", "AWS"), ("docker", "Docker"), ("kubernetes", "Kubernetes"),
                        ("jenkins", "Jenkins"), ("git", "Git"), ("github", "GitHub")]),
    ("Security & Testing", [("si-jsonwebtokens", "JWT"), ("si-auth0", "OAuth2"), ("junit", "JUnit 5"),
                            ("@Mk", "Mockito"), ("jest", "Jest"), ("vitest", "Vitest"), ("postman", "Postman")]),
    ("AI / ML", [("python", "Python"), ("si-yolo", "YOLOv11"), ("pytorch", "PyTorch"), ("opencv", "OpenCV")]),
]
BRAND = {"si-springsecurity": "#6DB33F", "si-pinia": "#FFD859", "si-jsonwebtokens": "#000000",
         "si-auth0": "#EB5424", "si-yolo": "#111F68"}
# devicon logos whose dark fill disappears on a dark background
DARK_FILLS = {"express": None, "kafka": "#231f20", "github": "#181616", "socketio": "#010101", "aws": "#252f3e"}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS = os.path.join(ROOT, "assets", "icons")
DIST = os.path.join(ROOT, "dist")
FONT = "'Segoe UI',-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"
MONO = "'Fira Code','JetBrains Mono',Consolas,'Courier New',monospace"

THEMES = {
    "dark": dict(bg="#0d1117", card="#161b22", border="#30363d", text="#e6edf3", muted="#8b949e",
                 tile="#21262d", accent1="#a855f7", accent2="#22d3ee",
                 levels=["#262c36", "#0e4429", "#006d32", "#26a641", "#39d353"], empty="#262c36"),
    "light": dict(bg="#ffffff", card="#ffffff", border="#d0d7de", text="#1f2328", muted="#656d76",
                  tile="#f6f8fa", accent1="#7c3aed", accent2="#0891b2",
                  levels=["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"], empty="#ebedf0"),
}

def esc(s): return html.escape(str(s), quote=True)

def write(name, content):
    os.makedirs(DIST, exist_ok=True)
    with open(os.path.join(DIST, name), "w", encoding="utf-8") as f:
        f.write(content)
    print("  wrote", name, f"({len(content)//1024} KB)")

def http(url, data=None, token=None, accept="application/json"):
    headers = {"User-Agent": f"{USER}-profile-generator", "Accept": accept}
    if token: headers["Authorization"] = f"bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")

def luminance(hx):
    hx = hx.lstrip("#"); r, g, b = (int(hx[i:i+2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

# ───────────────────────── data ─────────────────────────
def fetch_calendar():
    """Contribution calendar from the public profile page (no token needed)."""
    page = http(f"https://github.com/users/{USER}/contributions", accept="text/html")
    cells = {}
    for m in re.finditer(r'<td[^>]*?data-date="([\d-]+)"[^>]*?id="contribution-day-component-(\d+)-(\d+)"[^>]*?data-level="(\d)"', page):
        date, row, col, lvl = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        cells[f"{row}-{col}"] = dict(date=date, row=row, col=col, level=lvl, count=0)
    for m in re.finditer(r'for="contribution-day-component-(\d+-\d+)"[^>]*>([^<]*)</tool-tip>', page):
        k, txt = m.group(1), m.group(2)
        n = re.match(r"\s*([\d,]+) contribution", txt)
        if k in cells and n: cells[k]["count"] = int(n.group(1).replace(",", ""))
    total = re.search(r"([\d,]+)\s+contributions?\s+in the last year", page)
    if not cells: raise RuntimeError("calendar parse failed")
    weeks = max(c["col"] for c in cells.values()) + 1
    return dict(cells=list(cells.values()), weeks=weeks,
                total=int(total.group(1).replace(",", "")) if total else sum(c["count"] for c in cells.values()))

def streaks(cells):
    days = sorted(cells, key=lambda c: c["date"])
    today = dt.date.today().isoformat()
    days = [d for d in days if d["date"] <= today]
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 or d["level"] > 0 else 0
        longest = max(longest, run)
    cur = 0
    for i, d in enumerate(reversed(days)):
        active = d["count"] > 0 or d["level"] > 0
        if active: cur += 1
        elif i == 0: continue          # today not done yet: don't break the streak
        else: break
    return cur, longest

def fetch_stats():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        try:
            return fetch_stats_graphql(token)
        except Exception as e:
            print("  GraphQL failed, trying REST:", e, file=sys.stderr)
    return fetch_stats_rest()

def fetch_stats_graphql(token):
    if True:
        q = """query($login:String!){ user(login:$login){
          followers{totalCount}
          pullRequests{totalCount}
          contributionsCollection{ totalCommitContributions restrictedContributionsCount }
          repositories(first:100, ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC){
            totalCount nodes{ stargazerCount
              languages(first:10, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name color } } } } } } }"""
        body = json.dumps({"query": q, "variables": {"login": USER}}).encode()
        u = json.loads(http("https://api.github.com/graphql", body, token))["data"]["user"]
        langs = {}
        for r in u["repositories"]["nodes"]:
            for e in r["languages"]["edges"]:
                n = e["node"]["name"]; langs.setdefault(n, [0, e["node"]["color"] or "#8b949e"])[0] += e["size"]
        cc = u["contributionsCollection"]
        return dict(repos=u["repositories"]["totalCount"],
                    stars=sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
                    followers=u["followers"]["totalCount"], prs=u["pullRequests"]["totalCount"],
                    commits=cc["totalCommitContributions"] + cc["restrictedContributionsCount"], langs=langs)
def fetch_stats_rest():
    user = json.loads(http(f"https://api.github.com/users/{USER}"))
    repos = json.loads(http(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner"))
    repos = [r for r in repos if not r.get("fork")]
    langs = {}
    for r in repos:
        if r.get("language"): langs.setdefault(r["language"], [0, "#8b949e"])[0] += max(r.get("size", 1), 1)
    return dict(repos=len(repos), stars=sum(r["stargazers_count"] for r in repos),
                followers=user.get("followers", 0), prs=None, commits=None, langs=langs)

LANG_COLORS = {"Java": "#b07219", "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "HTML": "#e34c26",
               "CSS": "#563d7c", "Python": "#3572A5", "Vue": "#41b883", "SCSS": "#c6538c", "Shell": "#89e051"}

# ───────────────────────── header ─────────────────────────
def header_svg():
    W, H = 840, 230
    lines, total = [], 0
    per = 3.6  # seconds per role
    cycle = per * len(ROLES)
    for i, role in enumerate(ROLES):
        tw = len(role) * 12.1 + 4
        a, b = i * per / cycle * 100, (i + 1) * per / cycle * 100
        t1, t2, t3 = a + (b - a) * .35, a + (b - a) * .8, b
        lines.append(f"""
  <style>
    @keyframes r{i} {{ 0%,{a:.2f}% {{width:0}} {t1:.2f}% {{width:{tw:.0f}px}} {t2:.2f}% {{width:{tw:.0f}px}} {t3:.2f}%,100% {{width:0}} }}
    @keyframes c{i} {{ 0%,{max(a-.01,0):.2f}% {{opacity:0}} {a:.2f}% {{transform:translateX(0);opacity:1}} {t1:.2f}% {{transform:translateX({tw:.0f}px)}} {t2:.2f}% {{transform:translateX({tw:.0f}px)}} {t3-.01:.2f}% {{transform:translateX(0);opacity:1}} {t3:.2f}%,100% {{opacity:0}} }}
    .r{i} {{ animation: r{i} {cycle}s steps({len(role)}) infinite }}
    .c{i} {{ animation: c{i} {cycle}s steps({len(role)}) infinite }}
  </style>
  <clipPath id="clip{i}"><rect class="r{i}" x="{W/2 - tw/2:.0f}" y="138" height="34" width="0"/></clipPath>
  <text x="{W/2 - tw/2 + 2:.0f}" y="161" font-family="{MONO}" font-size="20" fill="#e0f2fe" clip-path="url(#clip{i})">{esc(role)}</text>
  <rect class="c{i} caret" x="{W/2 - tw/2:.0f}" y="143" width="2.5" height="24" fill="#22d3ee" opacity="0"/>""")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(NAME)} - {esc(TITLE)}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#1e1b4b"><animate attributeName="stop-color" values="#1e1b4b;#312e81;#1e1b4b" dur="10s" repeatCount="indefinite"/></stop>
      <stop offset=".55" stop-color="#4c1d95"/>
      <stop offset="1" stop-color="#0e7490"><animate attributeName="stop-color" values="#0e7490;#1d4ed8;#0e7490" dur="10s" repeatCount="indefinite"/></stop>
    </linearGradient>
    <linearGradient id="name" x1="0" x2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#c4b5fd"/></linearGradient>
    <filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="28"/></filter>
    <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#ffffff" stroke-opacity=".05"/></pattern>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
  </defs>
  <style>
    .fade {{ animation: fade 1.1s ease-out both }}
    .d2 {{ animation-delay: .25s }}
    @keyframes fade {{ from {{ opacity:0; transform: translateY(10px) }} to {{ opacity:1; transform:none }} }}
    .caret {{ animation-timing-function: steps(1) }}
    @keyframes blink {{ 50% {{ opacity: 0 }} }}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    <rect width="{W}" height="{H}" fill="url(#grid)"/>
    <circle cx="120" cy="40" r="90" fill="#a855f7" opacity=".45" filter="url(#blur)">
      <animate attributeName="cx" values="120;200;120" dur="12s" repeatCount="indefinite"/></circle>
    <circle cx="720" cy="200" r="100" fill="#22d3ee" opacity=".35" filter="url(#blur)">
      <animate attributeName="cx" values="720;620;720" dur="14s" repeatCount="indefinite"/></circle>
  </g>
  <g class="fade">
    <text x="{W/2}" y="62" text-anchor="middle" font-family="{FONT}" font-size="15" letter-spacing="4" fill="#a5f3fc" font-weight="600">HELLO, I'M</text>
    <text x="{W/2}" y="108" text-anchor="middle" font-family="{FONT}" font-size="44" font-weight="800" fill="url(#name)">{esc(NAME)}</text>
  </g>
  <g class="fade d2">
    <text x="{W/2}" y="134" text-anchor="middle" font-family="{FONT}" font-size="16" fill="#ddd6fe" font-weight="500" letter-spacing="1">{esc(TITLE)}  ·  Hyderabad, India</text>
  </g>{''.join(lines)}
  <g transform="translate({W/2 - 62},190)">
    <rect width="124" height="24" rx="12" fill="#10b981" fill-opacity=".18" stroke="#34d399" stroke-opacity=".6"/>
    <circle cx="16" cy="12" r="4" fill="#34d399"><animate attributeName="opacity" values="1;.25;1" dur="1.6s" repeatCount="indefinite"/></circle>
    <text x="68" y="16.5" text-anchor="middle" font-family="{FONT}" font-size="12" font-weight="600" fill="#a7f3d0">Open to work</text>
  </g>
</svg>"""

# ───────────────────────── buttons ─────────────────────────
ICON_PATHS = {
    "download": '<path d="M12 3v12m0 0-5-5m5 5 5-5M4 19h16" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2.5" fill="none" stroke="#fff" stroke-width="2"/><path d="m4 7 8 6 8-6" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>',
    "linkedin": '<rect x="3" y="3" width="18" height="18" rx="3.5" fill="#fff"/><path d="M7.2 10.2v6.6M7.2 7.4v.1M10.8 16.8v-6.6m0 3c0-1.8 1-3.1 2.6-3.1s2.4 1.1 2.4 3v3.7" fill="none" stroke="#0A66C2" stroke-width="2.1" stroke-linecap="round"/>',
    "github": '<path fill="#fff" d="M12 2.2a9.8 9.8 0 0 0-3.1 19.1c.5.1.7-.2.7-.5v-1.8c-2.7.6-3.3-1.2-3.3-1.2-.4-1.1-1.1-1.4-1.1-1.4-.9-.6.1-.6.1-.6 1 .1 1.5 1 1.5 1 .9 1.5 2.3 1.1 2.9.8.1-.6.3-1.1.6-1.3-2.2-.3-4.5-1.1-4.5-4.9 0-1.1.4-2 1-2.6-.1-.3-.4-1.3.1-2.7 0 0 .8-.3 2.7 1a9.3 9.3 0 0 1 4.9 0c1.9-1.3 2.7-1 2.7-1 .5 1.4.2 2.4.1 2.7.6.7 1 1.6 1 2.6 0 3.8-2.3 4.6-4.5 4.9.4.3.7.9.7 1.8v2.7c0 .3.2.6.7.5A9.8 9.8 0 0 0 12 2.2z"/>',
}

def button_svg(label, icon, c1, c2, w=190):
    h = 46
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">
  <defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>
  <linearGradient id="shine" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <clipPath id="c"><rect width="{w}" height="{h}" rx="{h/2}"/></clipPath></defs>
  <g clip-path="url(#c)">
    <rect width="{w}" height="{h}" fill="url(#g)"/>
    <rect x="-80" width="60" height="{h}" fill="url(#shine)" transform="skewX(-20)">
      <animate attributeName="x" values="-80;{w+80};{w+80}" keyTimes="0;.35;1" dur="4s" repeatCount="indefinite"/></rect>
  </g>
  <g transform="translate(20,11)">{ICON_PATHS[icon]}</g>
  <text x="{(w+30)/2:.0f}" y="28.5" text-anchor="middle" font-family="{FONT}" font-size="15" font-weight="700" fill="#fff" letter-spacing=".3">{esc(label)}</text>
</svg>"""

# ───────────────────────── stack card ─────────────────────────
def icon_data(key, t):
    if key.startswith("@"):
        return None
    with open(os.path.join(ICONS, key + ".svg"), encoding="utf-8") as f:
        svg = f.read()
    if key in BRAND:                                   # simple-icons: single-path, colour it
        col = BRAND[key]
        if t == "dark" and luminance(col) < .18: col = THEMES[t]["text"]
        svg = svg.replace("<svg ", f'<svg fill="{col}" ', 1)
    elif t == "dark" and key in DARK_FILLS:            # devicon logos that are black
        old = DARK_FILLS[key]
        svg = svg.replace(f'fill="{old}"', f'fill="{THEMES[t]["text"]}"') if old else \
              svg.replace("<svg ", f'<svg fill="{THEMES[t]["text"]}" ', 1)
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

def card_frame(W, H, t, body, title=None, subtitle=None):
    c = THEMES[t]
    head = ""
    if title:
        head = f"""<text x="28" y="40" font-family="{FONT}" font-size="18" font-weight="700" fill="{c['text']}">{esc(title)}</text>
  <rect x="28" y="50" width="44" height="3" rx="1.5" fill="url(#acc)"/>"""
        if subtitle:
            head += f'<text x="{W-28}" y="40" text-anchor="end" font-family="{FONT}" font-size="12.5" fill="{c["muted"]}">{esc(subtitle)}</text>'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title or '')}">
  <defs><linearGradient id="acc" x1="0" x2="1"><stop offset="0" stop-color="{c['accent1']}"/><stop offset="1" stop-color="{c['accent2']}"/></linearGradient></defs>
  <style>
    .pop {{ opacity:0; animation: pop .55s cubic-bezier(.2,.8,.3,1.2) forwards }}
    @keyframes pop {{ from {{ opacity:0; transform: translateY(8px) scale(.96) }} to {{ opacity:1; transform:none }} }}
    .grow {{ transform-box: fill-box; transform-origin: left; transform: scaleX(0); animation: grow 1.2s ease-out forwards }}
    @keyframes grow {{ to {{ transform: scaleX(1) }} }}
  </style>
  <rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="{c['card']}" stroke="{c['border']}"/>
  {head}
  {body}
</svg>"""

def stack_svg(t):
    c = THEMES[t]
    W, cols, tw, th = 840, 8, 94, 96
    x0 = (W - cols * tw) / 2
    y, parts, n = 76, [], 0
    for cat, items in STACK:
        parts.append(f'<text x="{x0+6:.0f}" y="{y}" font-family="{FONT}" font-size="12" font-weight="700" letter-spacing="1.6" fill="{c["accent1"]}">{esc(cat.upper())}</text>')
        parts.append(f'<line x1="{x0+6 + len(cat)*9.2 + 14:.0f}" y1="{y-4}" x2="{W-x0-6:.0f}" y2="{y-4}" stroke="{c["border"]}" stroke-dasharray="3 4"/>')
        y += 14
        for i, (key, label) in enumerate(items):
            col, row = i % cols, i // cols
            tx, ty = x0 + col * tw, y + row * th
            cx = tx + tw / 2
            delay = n * 0.035; n += 1
            data = icon_data(key, t)
            if data:
                ic = f'<image href="{data}" x="{cx-19:.1f}" y="{ty+15}" width="38" height="38"/>'
            else:   # monogram for tools without an official logo
                ic = (f'<rect x="{cx-19:.1f}" y="{ty+15}" width="38" height="38" rx="10" fill="url(#acc)"/>'
                      f'<text x="{cx:.1f}" y="{ty+40}" text-anchor="middle" font-family="{FONT}" font-size="16" font-weight="800" fill="#fff">{esc(key[1:])}</text>')
            parts.append(f'''<g class="pop" style="animation-delay:{delay:.2f}s">
    <rect x="{cx-33:.1f}" y="{ty+4}" width="66" height="60" rx="14" fill="{c["tile"]}" stroke="{c["border"]}" stroke-opacity=".7"/>
    {ic}
    <text x="{cx:.1f}" y="{ty+82}" text-anchor="middle" font-family="{FONT}" font-size="12" font-weight="600" fill="{c["text"]}">{esc(label)}</text></g>''')
        rows = (len(items) + cols - 1) // cols
        y += rows * th + 26
    H = y - 6
    return card_frame(W, H, t, "\n  ".join(parts), "Tech Stack", "Tools I use to build production systems")

# ───────────────────────── stats card ─────────────────────────
STAT_ICONS = {  # simple 16px line icons (own drawings)
    "fire": '<path d="M8 1.5c.5 2.5 3.5 4 3.5 7.5a3.5 3.5 0 0 1-7 0c0-1.6.8-2.6 1.6-3.4C6.4 7.2 7 8 7 8s1.6-2.2 1-6.5z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>',
    "trophy": '<path d="M5 2h6v4a3 3 0 0 1-6 0zM5 3.5H2.5A2.5 2.5 0 0 0 5 7M11 3.5h2.5A2.5 2.5 0 0 1 11 7M8 9v3M5.5 14h5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
    "grid": '<rect x="2" y="2" width="5" height="5" rx="1"/><rect x="9" y="2" width="5" height="5" rx="1"/><rect x="2" y="9" width="5" height="5" rx="1"/><rect x="9" y="9" width="5" height="5" rx="1"/>',
    "repo": '<path d="M3 2.5A1.5 1.5 0 0 1 4.5 1H13v11H4.5A1.5 1.5 0 0 0 3 13.5zM3 13.5A1.5 1.5 0 0 0 4.5 15H13v-3" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>',
    "star": '<path d="m8 1.5 2 4.2 4.5.6-3.3 3.1.8 4.5L8 11.7 4 13.9l.8-4.5L1.5 6.3 6 5.7z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>',
    "users": '<circle cx="6" cy="5" r="2.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M1.5 14c0-2.5 2-4 4.5-4s4.5 1.5 4.5 4M11 3a2.3 2.3 0 0 1 0 4.5M12.5 10c1.3.5 2 1.8 2 4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
}

def fmt(n): return "—" if n is None else (f"{n/1000:.1f}k" if n >= 10000 else f"{n:,}")

def stats_svg(t, cal, st):
    c = THEMES[t]
    W, H = 840, 250
    cur, longest = streaks(cal["cells"]) if cal else (None, None)
    metrics = [
        ("fire", "Current streak", (f"{cur} day" + ("" if cur == 1 else "s")) if cur is not None else "—"),
        ("trophy", "Longest streak", (f"{longest} day" + ("" if longest == 1 else "s")) if longest is not None else "—"),
        ("grid", "Contributions (1y)", fmt(cal["total"]) if cal else "—"),
        ("repo", "Public repos", fmt(st.get("repos"))),
        ("star", "Stars earned", fmt(st.get("stars"))),
        ("users", "Followers", fmt(st.get("followers"))),
    ]
    parts = []
    for i, (ic, label, val) in enumerate(metrics):
        col, row = i % 2, i // 2
        x, y = 28 + col * 196, 74 + row * 56
        parts.append(f'''<g class="pop" style="animation-delay:{i*.08:.2f}s">
    <rect x="{x}" y="{y}" width="184" height="46" rx="11" fill="{c["tile"]}" stroke="{c["border"]}" stroke-opacity=".7"/>
    <g transform="translate({x+13},{y+15})" color="{c["accent1"]}" fill="{c["accent1"]}">{STAT_ICONS[ic]}</g>
    <text x="{x+38}" y="{y+19}" font-family="{FONT}" font-size="11" fill="{c["muted"]}">{esc(label)}</text>
    <text x="{x+38}" y="{y+36}" font-family="{FONT}" font-size="15" font-weight="700" fill="{c["text"]}">{esc(val)}</text></g>''')
    # languages
    lx, lw = 444, W - 444 - 28
    parts.append(f'<text x="{lx}" y="86" font-family="{FONT}" font-size="12" font-weight="700" letter-spacing="1.6" fill="{c["accent1"]}">TOP LANGUAGES</text>')
    langs = sorted((st.get("langs") or {}).items(), key=lambda kv: -kv[1][0])[:5]
    tot = sum(v[0] for _, v in langs) or 1
    if langs:
        bx = lx
        parts.append(f'<clipPath id="bar"><rect x="{lx}" y="98" width="{lw}" height="10" rx="5"/></clipPath><g clip-path="url(#bar)">')
        for name, (size, colr) in langs:
            colr = LANG_COLORS.get(name, colr) if colr in (None, "#8b949e") else colr
            w = size / tot * lw
            parts.append(f'<rect class="grow" x="{bx:.1f}" y="98" width="{w+.5:.1f}" height="10" fill="{colr}"/>'); bx += w
        parts.append("</g>")
        for i, (name, (size, colr)) in enumerate(langs):
            colr = LANG_COLORS.get(name, colr) if colr in (None, "#8b949e") else colr
            y = 134 + i * 21
            parts.append(f'''<g class="pop" style="animation-delay:{.3+i*.07:.2f}s"><circle cx="{lx+5}" cy="{y-4}" r="5" fill="{colr}"/>
    <text x="{lx+18}" y="{y}" font-family="{FONT}" font-size="13" fill="{c["text"]}">{esc(name)}</text>
    <text x="{W-28}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="12.5" fill="{c["muted"]}">{size/tot*100:.1f}%</text></g>''')
    else:
        parts.append(f'<text x="{lx}" y="130" font-family="{FONT}" font-size="13" fill="{c["muted"]}">Updating on next workflow run…</text>')
    parts.append(f'<line x1="424" y1="74" x2="424" y2="{H-28}" stroke="{c["border"]}"/>')
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%d %b %Y")
    return card_frame(W, H, t, "\n  ".join(parts), "GitHub Activity", f"updated {stamp}")

# ───────────────────────── snake ─────────────────────────
def snake_svg(t, cal):
    c = THEMES[t]
    W_weeks = cal["weeks"]
    cell, gap = 11, 3; step = cell + gap
    padx, pady = 28, 66
    W = padx * 2 + W_weeks * step - gap
    H = pady + 7 * step - gap + 52
    grid = {(d["col"], d["row"]): d for d in cal["cells"]}
    targets = {k for k, d in grid.items() if d["level"] > 0}

    # path planning: greedy nearest-target with BFS (own algorithm)
    L = 6                                   # snake length
    start = (-L - 1, 0)
    path = [(x, 0) for x in range(start[0], 0)]
    pos = (0, 0); path.append(pos)
    eat_at = {}
    if pos in targets: eat_at[pos] = 0; targets.discard(pos)
    def neighbors(p):
        x, y = p
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W_weeks and 0 <= ny < 7: yield (nx, ny)
    while targets:
        prev = {pos: None}; dq = deque([pos]); found = None
        while dq:
            p = dq.popleft()
            if p in targets: found = p; break
            for q in neighbors(p):
                if q not in prev: prev[q] = p; dq.append(q)
        if not found: break
        seg = []; p = found
        while p != pos: seg.append(p); p = prev[p]
        for p in reversed(seg):
            path.append(p)
            if p in targets: targets.discard(p); eat_at[p] = len(path) - 1
        pos = found
    # exit upwards out of the frame
    x, y = pos
    for yy in range(y - 1, -L - 6, -1): path.append((x, yy))

    if not eat_at:                          # no contributions: just a lap
        path = [(x, 0) for x in range(start[0], W_weeks + L + 2)]

    dt_step = 0.085
    steps = len(path) - 1
    pause = 1.6
    D = steps * dt_step + L * dt_step + pause
    def px(p): return (padx + p[0] * step + cell / 2, pady + p[1] * step + cell / 2)
    # simplify collinear points (keeps constant speed since all moves are unit steps)
    pts = [path[0]]
    for i in range(1, len(path) - 1):
        a, b, cc = path[i - 1], path[i], path[i + 1]
        if (b[0] - a[0], b[1] - a[1]) != (cc[0] - b[0], cc[1] - b[1]): pts.append(b)
    pts.append(path[-1])
    d_attr = "M" + " L".join(f"{px(p)[0]:.1f},{px(p)[1]:.1f}" for p in pts)

    cells_svg = []
    for (col, row), d in sorted(grid.items()):
        x = padx + col * step; y = pady + row * step
        fill = c["levels"][d["level"]]
        anim = ""
        if (col, row) in eat_at:
            k = eat_at[(col, row)] * dt_step / D
            anim = f'<animate attributeName="fill" calcMode="discrete" values="{fill};{c["empty"]}" keyTimes="0;{k:.4f}" dur="{D:.2f}s" repeatCount="indefinite"/>'
        cells_svg.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{fill}">{anim}</rect>')

    snake = []
    run = steps * dt_step / D
    for i in range(L):
        lag = i * dt_step / D
        size = cell + 1 - i * 0.9
        op = 1 - i * 0.09
        colr = f"url(#sg{i})"
        snake.append(f'''<rect x="{-size/2:.1f}" y="{-size/2:.1f}" width="{size:.1f}" height="{size:.1f}" rx="{size/2.4:.1f}" fill="{colr}" opacity="{op:.2f}">
      <animateMotion path="{d_attr}" dur="{D:.2f}s" repeatCount="indefinite" calcMode="linear"
        keyPoints="0;0;1;1" keyTimes="0;{lag:.4f};{min(lag+run, 1):.4f};1"/></rect>''')
    snake.reverse()  # draw head last (on top)
    grads = "".join(
        f'<linearGradient id="sg{i}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["accent1"]}"/><stop offset="1" stop-color="{c["accent2"]}"/></linearGradient>'
        for i in range(L))
    legend_y = pady + 7 * step + 18
    legend = "".join(f'<rect x="{W - padx - 5*step + i*step - 34}" y="{legend_y}" width="{cell}" height="{cell}" rx="2.5" fill="{c["levels"][i]}"/>' for i in range(5))
    cur, longest = streaks(cal["cells"])
    body = f"""<defs>{grads}<clipPath id="area"><rect x="{padx-6}" y="{pady-8}" width="{W-2*padx+12}" height="{7*step+8}"/></clipPath></defs>
  <g>{''.join(cells_svg)}</g>
  <g clip-path="url(#area)">{''.join(snake)}</g>
  <text x="{padx}" y="{legend_y+9.5}" font-family="{FONT}" font-size="12" fill="{c['muted']}"><tspan font-weight="700" fill="{c['text']}">{cal['total']:,}</tspan> contributions in the last year  ·  current streak <tspan font-weight="700" fill="{c['text']}">{cur}</tspan> day{"" if cur == 1 else "s"}</text>
  <text x="{W - padx - 5*step - 42}" y="{legend_y+9.5}" text-anchor="end" font-family="{FONT}" font-size="11" fill="{c['muted']}">Less</text>
  {legend}
  <text x="{W - padx - 30}" y="{legend_y+9.5}" font-family="{FONT}" font-size="11" fill="{c['muted']}">More</text>"""
    return card_frame(W, H, t, body, "Contribution Snake", "it eats every green square, then starts again")

# ───────────────────────── main ─────────────────────────
def main():
    print("Generating static assets…")
    write("header.svg", header_svg())
    write("btn-cv.svg", button_svg("Download CV", "download", "#7c3aed", "#0891b2", 200))
    write("btn-email.svg", button_svg("Email Me", "mail", "#ea4335", "#c5221f", 170))
    write("btn-linkedin.svg", button_svg("LinkedIn", "linkedin", "#0a66c2", "#004182", 170))
    write("btn-github.svg", button_svg("Follow", "github", "#24292f", "#57606a", 170))
    for t in THEMES:
        write(f"stack-{t}.svg", stack_svg(t))

    print("Fetching contribution calendar…")
    cal = None
    try:
        cal = fetch_calendar()
        print(f"  {len(cal['cells'])} days, {cal['total']} contributions")
        for t in THEMES: write(f"snake-{t}.svg", snake_svg(t, cal))
    except Exception as e:
        print("  calendar failed, keeping previous snake:", e, file=sys.stderr)

    print("Fetching stats…")
    try:
        st = fetch_stats()
    except Exception as e:
        print("  stats failed:", e, file=sys.stderr); st = {}
    if st or cal or not os.path.exists(os.path.join(DIST, "stats-dark.svg")):
        for t in THEMES: write(f"stats-{t}.svg", stats_svg(t, cal, st))

if __name__ == "__main__":
    main()
