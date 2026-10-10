import os
from xml.sax.saxutils import escape as esc

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)

P = {
    "dark": dict(bg="#0E1621", node="#152131", border="#26354A", grid="#22314A",
                 text="#E6EDF3", muted="#8B98A9", amber="#F5A524", teal="#2DD4BF",
                 green="#3FB950", track="#1B2738", on_amber="#1A1206"),
    "light": dict(bg="#F6F8FA", node="#FFFFFF", border="#D0D7DE", grid="#D5DBE2",
                  text="#1F2328", muted="#57606A", amber="#B45309", teal="#0F766E",
                  green="#1A7F37", track="#E3E8EE", on_amber="#FFFFFF"),
}
SANS = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif"
REDUCE = "@media (prefers-reduced-motion: reduce){.m{display:none}}"


def tw(s, size, k=0.56):
    """rough text width"""
    return len(s) * size * k


def frame(w, h, p, body, extra_style=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{SANS}">
<style>{REDUCE}{extra_style}</style>
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="22" fill="{p['bg']}" stroke="{p['border']}" stroke-width="1.5"/>
{body}
</svg>'''


# ---------------------------------------------------------------- header
def header(p):
    W, H = 1200, 400
    b = []
    b.append(f'''<defs><pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse">
<circle cx="2" cy="2" r="1.2" fill="{p['grid']}"/></pattern>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="g"/>
<feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="c"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="22"/></clipPath></defs>
<rect x="620" y="1" width="579" height="{H-2}" fill="url(#dots)" clip-path="url(#c)"/>''')
    # name + intro
    b.append(f'''<text x="64" y="132" font-size="60" font-weight="800" fill="{p['text']}" letter-spacing="-1.5">Pavan Kumar</text>
<text x="64" y="200" font-size="60" font-weight="800" fill="{p['text']}" letter-spacing="-1.5">Vinjamara</text>
<rect x="66" y="226" width="56" height="5" rx="2.5" fill="{p['amber']}"/>
<text x="64" y="272" font-size="22" fill="{p['muted']}">Full stack Java developer. I build event-driven</text>
<text x="64" y="302" font-size="22" fill="{p['muted']}">systems that stay fast under real load.</text>''')
    # status pills
    x = 64
    pills = [("Open to work", True), ("Hyderabad, India", False), ("3+ years", False)]
    for label, live in pills:
        w = tw(label, 15, 0.6) + (54 if live else 34)
        b.append(f'<rect x="{x}" y="332" width="{w:.0f}" height="34" rx="17" fill="{p["node"]}" stroke="{p["border"]}"/>')
        tx = x + 16
        if live:
            b.append(f'''<circle cx="{x+20}" cy="349" r="5" fill="{p['green']}"/>
<circle class="m" cx="{x+20}" cy="349" r="5" fill="none" stroke="{p['green']}" stroke-width="2">
<animate attributeName="r" values="5;12" dur="1.8s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0.9;0" dur="1.8s" repeatCount="indefinite"/></circle>''')
            tx = x + 34
        b.append(f'<text x="{tx}" y="354" font-size="15" font-weight="600" fill="{p["text"]}">{label}</text>')
        x += w + 10

    # architecture diagram
    nodes = {
        "dev": (735, 125, "Devices", "camera events"),
        "kafka": (915, 125, "Kafka", "event stream"),
        "svc": (1095, 125, "Spring Boot", "microservices"),
        "db": (1095, 275, "PostgreSQL", "+ Redis cache"),
        "ui": (915, 275, "React UI", "live dashboards"),
    }
    order = ["dev", "kafka", "svc", "db", "ui"]
    path = "M " + " L ".join(f"{nodes[k][0]} {nodes[k][1]}" for k in order)
    b.append(f'<path d="{path}" fill="none" stroke="{p["border"]}" stroke-width="2" stroke-dasharray="6 6"/>')
    b.append(f'<path id="flow" d="{path}" fill="none" stroke="none"/>')
    for i, col in enumerate([p["amber"], p["teal"], p["amber"]]):
        b.append(f'''<circle class="m" r="5" fill="{col}" filter="url(#glow)">
<animateMotion dur="6s" begin="-{i*2}s" repeatCount="indefinite" rotate="auto"><mpath href="#flow"/></animateMotion></circle>''')
    for k in order:
        cx, cy, t, s = nodes[k]
        hl = k == "kafka"
        b.append(f'''<rect x="{cx-72}" y="{cy-32}" width="144" height="64" rx="14" fill="{p['node']}" stroke="{p['amber'] if hl else p['border']}" stroke-width="{2 if hl else 1.5}">
{'<animate attributeName="stroke-opacity" values="1;0.35;1" dur="2.4s" repeatCount="indefinite"/>' if hl else ''}</rect>
<text x="{cx}" y="{cy-2}" text-anchor="middle" font-size="16" font-weight="700" fill="{p['text']}">{esc(t)}</text>
<text x="{cx}" y="{cy+18}" text-anchor="middle" font-size="12" fill="{p['muted']}">{esc(s)}</text>''')
    b.append(f'<text x="1005" y="360" text-anchor="middle" font-size="13" fill="{p["muted"]}">The kind of pipeline I build and run in production</text>')
    return frame(W, H, p, "\n".join(b))


# ---------------------------------------------------------------- impact bars
def impact(p):
    rows = [
        ("API response time", "2s to under 800ms", 1.0, 0.40, "amber"),
        ("Peak database load", "35% lower", 1.0, 0.65, "amber"),
        ("Manual review effort", "50% less", 1.0, 0.50, "amber"),
        ("Event throughput", "40% higher", 0.714, 1.0, "teal"),
        ("Release frequency", "3x more often", 0.333, 1.0, "teal"),
    ]
    W, x0, x1 = 1200, 56, 1144
    tw_ = x1 - x0
    top, gap = 64, 66
    H = top + gap * len(rows) + 28
    b = [f'<text x="{x0}" y="40" font-size="14" fill="{p["muted"]}">Before and after, measured on production systems (tick marks the starting point)</text>',
         f'<g font-size="13" fill="{p["muted"]}"><rect x="{x1-300}" y="30" width="12" height="12" rx="3" fill="{p["amber"]}"/><text x="{x1-282}" y="40">lower is better</text>'
         f'<rect x="{x1-160}" y="30" width="12" height="12" rx="3" fill="{p["teal"]}"/><text x="{x1-142}" y="40">higher is better</text></g>']
    for i, (label, val, a, z, c) in enumerate(rows):
        y = top + i * gap
        col = p[c]
        b.append(f'''<text x="{x0}" y="{y+18}" font-size="17" font-weight="600" fill="{p['text']}">{label}</text>
<text x="{x1}" y="{y+18}" text-anchor="end" font-size="17" font-weight="700" fill="{col}">{val}</text>
<rect x="{x0}" y="{y+30}" width="{tw_}" height="12" rx="6" fill="{p['track']}"/>
<rect x="{x0}" y="{y+30}" width="{tw_*a:.0f}" height="12" rx="6" fill="{col}" opacity="0.18"/>
<rect x="{x0}" y="{y+30}" width="{tw_*z:.0f}" height="12" rx="6" fill="{col}">
<animate attributeName="width" from="{tw_*a:.0f}" to="{tw_*z:.0f}" dur="1.6s" begin="{0.3+i*0.25:.2f}s" fill="freeze" calcMode="spline" keySplines="0.22 1 0.36 1" keyTimes="0;1" values="{tw_*a:.0f};{tw_*z:.0f}"/></rect>''')
        if z > a:
            b.append(f'<rect x="{x0+tw_*a-1.5:.0f}" y="{y+27}" width="3" height="18" rx="1.5" fill="{p["bg"]}"/>'
                     f'<rect x="{x0+tw_*a-1:.0f}" y="{y+27}" width="2" height="18" rx="1" fill="{p["text"]}" opacity="0.55"/>')
    return frame(W, H, p, "\n".join(b))


# ---------------------------------------------------------------- stack chips
def stack(p):
    layers = [
        ("Backend", ["*Java", "*Spring Boot", "Spring Security", "Hibernate / JPA", "*Microservices", "REST APIs", "Node.js", "Express"]),
        ("Frontend", ["*React", "Redux", "Vue 3", "Pinia", "Next.js", "*TypeScript", "JavaScript", "Tailwind CSS", "Chart.js"]),
        ("Data and messaging", ["*PostgreSQL", "MongoDB", "*Redis", "*Kafka", "Socket.io"]),
        ("Cloud and DevOps", ["AWS EC2 / S3 / Lambda", "*Docker", "Kubernetes", "Jenkins", "CI/CD"]),
        ("Security", ["*JWT", "OAuth2", "RBAC", "Rate limiting", "VAPT remediation"]),
        ("Testing", ["*JUnit 5", "Mockito", "Jest", "Vitest", "Supertest", "Postman"]),
        ("Computer vision", ["YOLOv11 training", "Fabric.js zone editor"]),
    ]
    W, lx, cx0, cx1 = 1200, 48, 280, 1152
    ch, rg, fs = 36, 12, 15
    y = 36
    b = []
    for li, (name, chips) in enumerate(layers):
        # layout chips
        x, rows_y = cx0, y
        placed = []
        for c in chips:
            hl = c.startswith("*")
            t = c.lstrip("*")
            w = tw(t, fs, 0.6 if hl else 0.55) + 36
            if x + w > cx1:
                x = cx0
                rows_y += ch + 10
            placed.append((x, rows_y, w, t, hl))
            x += w + 10
        b.append(f'<text x="{lx}" y="{y+23}" font-size="16" font-weight="700" fill="{p["text"]}">{name}</text>')
        for (x, yy, w, t, hl) in placed:
            b.append(f'<rect x="{x:.0f}" y="{yy}" width="{w:.0f}" height="{ch}" rx="{ch/2}" fill="{p["node"]}" stroke="{p["amber"] if hl else p["border"]}" stroke-width="{1.8 if hl else 1.2}"/>'
                     f'<text x="{x+w/2:.0f}" y="{yy+23}" text-anchor="middle" font-size="{fs}" font-weight="{600 if hl else 500}" fill="{p["text"]}">{esc(t)}</text>')
        y = rows_y + ch + rg
        if li < len(layers) - 1:
            b.append(f'<line x1="{lx}" y1="{y}" x2="{cx1}" y2="{y}" stroke="{p["border"]}" stroke-opacity="0.6"/>')
            y += rg
    y += 8
    b.append(f'<rect x="{lx}" y="{y}" width="26" height="16" rx="8" fill="{p["node"]}" stroke="{p["amber"]}" stroke-width="1.8"/>'
             f'<text x="{lx+36}" y="{y+13}" font-size="13" fill="{p["muted"]}">Outlined in amber: what I use every day</text>')
    H = y + 40
    return frame(W, H, p, "\n".join(b))


# ---------------------------------------------------------------- timeline
def timeline(p):
    items = [
        ("2017 – 2021", "B.Tech, Computer Science", "TKR College, Hyderabad", "CGPA 7.67"),
        ("2022 – 2023", "Full stack trainee", "Newton School", "3+ apps, 50+ mock interviews"),
        ("2022 – 2024", "M.Sc, Computer Science", "Mia Digital University", "Score 85%"),
        ("2023 – now", "Full stack developer", "Zygal, Pune", "5 products, 10,000+ users"),
    ]
    W, H = 1200, 290
    x0, x1, ay = 175, 1025, 110
    step = (x1 - x0) / (len(items) - 1)
    L = x1 - x0
    b = [f'<line x1="{x0}" y1="{ay}" x2="{x1}" y2="{ay}" stroke="{p["track"]}" stroke-width="4" stroke-linecap="round"/>',
         f'''<line x1="{x0}" y1="{ay}" x2="{x1}" y2="{ay}" stroke="{p['amber']}" stroke-width="4" stroke-linecap="round" stroke-dasharray="{L}" stroke-dashoffset="{L}">
<animate attributeName="stroke-dashoffset" from="{L}" to="0" dur="2s" begin="0.2s" fill="freeze" calcMode="spline" keySplines="0.4 0 0.2 1" keyTimes="0;1" values="{L};0"/></line>''']
    for i, (yr, title, org, note) in enumerate(items):
        cx = x0 + i * step
        last = i == len(items) - 1
        b.append(f'<text x="{cx:.0f}" y="{ay-30}" text-anchor="middle" font-size="16" font-weight="700" fill="{p["amber"]}">{esc(yr)}</text>')
        b.append(f'<circle cx="{cx:.0f}" cy="{ay}" r="10" fill="{p["bg"]}" stroke="{p["amber"]}" stroke-width="4"/>')
        if last:
            b.append(f'<circle cx="{cx:.0f}" cy="{ay}" r="5" fill="{p["amber"]}"/>'
                     f'<circle class="m" cx="{cx:.0f}" cy="{ay}" r="10" fill="none" stroke="{p["amber"]}" stroke-width="2">'
                     f'<animate attributeName="r" values="10;22" dur="2s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values="0.8;0" dur="2s" repeatCount="indefinite"/></circle>')
        b.append(f'''<text x="{cx:.0f}" y="{ay+50}" text-anchor="middle" font-size="18" font-weight="700" fill="{p['text']}">{esc(title)}</text>
<text x="{cx:.0f}" y="{ay+76}" text-anchor="middle" font-size="15" fill="{p['text']}" opacity="0.85">{esc(org)}</text>
<text x="{cx:.0f}" y="{ay+100}" text-anchor="middle" font-size="14" fill="{p['muted']}">{esc(note)}</text>''')
    b.append(f'<text x="{W/2:.0f}" y="{H-28}" text-anchor="middle" font-size="13" fill="{p["muted"]}">The M.Sc ran part-time alongside training and work, so the dates overlap.</text>')
    return frame(W, H, p, "\n".join(b))


# ---------------------------------------------------------------- buttons
ICONS = {
    "cv": lambda c: f'<g fill="none" stroke="{c}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M0 -12 h11 l7 7 v19 a2 2 0 0 1 -2 2 h-16 a2 2 0 0 1 -2 -2 v-24 a2 2 0 0 1 2 -2z"/><path d="M8 -1 v10 M3.5 5 L8 9.5 L12.5 5"/></g>',
    "mail": lambda c: f'<g fill="none" stroke="{c}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="-2" y="-9" width="24" height="18" rx="3"/><path d="M-1 -7 L10 2 L21 -7"/></g>',
    "linkedin": lambda c: f'<g><rect x="-2" y="-11" width="22" height="22" rx="4" fill="{c}"/><text x="9" y="5" text-anchor="middle" font-size="14" font-weight="800" fill="BG">in</text></g>',
}


def button(p, kind, label, primary):
    W, H = 270, 64
    fill = p["amber"] if primary else p["node"]
    fg = p["on_amber"] if primary else p["text"]
    stroke = p["amber"] if primary else p["border"]
    icon = ICONS[kind](fg).replace("BG", fill)
    iw = 22
    total = iw + 12 + tw(label, 18, 0.55)
    sx = (W - total) / 2
    shine = ""
    if primary:
        shine = f'''<g clip-path="url(#pill)" class="m"><rect x="-80" y="0" width="50" height="{H}" fill="#FFFFFF" opacity="0.28" transform="skewX(-20)">
<animate attributeName="x" values="-80;-80;{W+60}" keyTimes="0;0.7;1" dur="4s" repeatCount="indefinite"/></rect></g>'''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{SANS}">
<style>{REDUCE}</style>
<defs><clipPath id="pill"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="{(H-2)/2}"/></clipPath></defs>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="{(H-2)/2}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>
{shine}
<g transform="translate({sx+2:.0f} {H/2})">{icon}</g>
<text x="{sx+iw+12:.0f}" y="{H/2+6.5}" font-size="18" font-weight="700" fill="{fg}">{esc(label)}</text>
</svg>'''


for theme, p in P.items():
    files = {
        f"header-{theme}.svg": header(p),
        f"impact-{theme}.svg": impact(p),
        f"stack-{theme}.svg": stack(p),
        f"journey-{theme}.svg": timeline(p),
        f"btn-cv-{theme}.svg": button(p, "cv", "Download CV", True),
        f"btn-email-{theme}.svg": button(p, "mail", "Email me", False),
        f"btn-linkedin-{theme}.svg": button(p, "linkedin", "LinkedIn", False),
    }
    for n, s in files.items():
        open(os.path.join(OUT, n), "w").write(s)
print(sorted(os.listdir(OUT)))
