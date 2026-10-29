#!/usr/bin/env python3
"""
Actualiza tu perfil de GitHub con datos reales de tu cuenta:

  - README.md  -> secciones entre <!--SKILLS:START/END--> y <!--PROJECTS:START/END-->
  - assets/stats.svg       (repos, estrellas, seguidores, contribuciones)
  - assets/languages.svg   (lenguajes que mas usas)

Solo usa la libreria estandar de Python. Lo ejecuta el workflow de GitHub Actions,
pero tambien puedes lanzarlo a mano:   GH_USER=tu-usuario python3 scripts/update_profile.py
Lo que quieras controlar a mano se edita en profile.config.json.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
import urllib.request
from collections import Counter
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_CFG = {
    "username": "",
    "projects": {"max": 6, "pin": [], "hide": [], "descriptions": {},
                 "include_forks": False, "include_archived": False},
    "skills": {"max": 12, "min_percent": 1.0, "use_topics": True, "max_topics": 6,
               "hide": [], "extra": []},
}

# lenguaje -> (logo de simple-icons, color del logo)
LOGOS = {
    "JavaScript": ("javascript", "F7DF1E"), "TypeScript": ("typescript", "3178C6"),
    "Python": ("python", "4B8BBE"), "HTML": ("html5", "E34F26"), "CSS": ("css3", "2965F1"),
    "SCSS": ("sass", "CC6699"), "Shell": ("gnubash", "4EAA25"), "C": ("c", "A8B9CC"),
    "C++": ("cplusplus", "659AD2"), "C#": ("csharp", "9B4F96"), "Go": ("go", "00ADD8"),
    "Rust": ("rust", "DEA584"), "PHP": ("php", "777BB4"), "Ruby": ("ruby", "CC342D"),
    "Kotlin": ("kotlin", "7F52FF"), "Swift": ("swift", "F05138"), "Dart": ("dart", "0175C2"),
    "Lua": ("lua", "5C6BC0"), "Dockerfile": ("docker", "2496ED"), "Docker": ("docker", "2496ED"),
    "Jupyter Notebook": ("jupyter", "F37626"), "PowerShell": ("powershell", "5391FE"),
    "Java": ("openjdk", "ED8B00"), "Linux": ("linux", "FCC624"), "Git": ("git", "F05032"),
    "Vue": ("vuedotjs", "4FC08D"), "Svelte": ("svelte", "FF3E00"), "SQL": ("postgresql", "4169E1"),
}
PALETTE = ["#ff3b3b", "#ff6a5a", "#d62839", "#ff9a8b", "#b30018", "#7a0f1f"]
BG, BORDER, FG, DIM, RED = "#0b0b0f", "#2b2b35", "#d8d8e0", "#6e6e7e", "#ff3b3b"


# ───────────────────────── utilidades ─────────────────────────
def load_cfg(root):
    cfg = json.loads(json.dumps(DEFAULT_CFG))
    path = os.path.join(root, "profile.config.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            user = json.load(f)
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    return cfg


def api(path, token, payload=None):
    url = path if path.startswith("http") else "https://api.github.com" + path
    req = urllib.request.Request(url, data=json.dumps(payload).encode() if payload else None)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-updater")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if payload:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def paginate(path, token):
    out, page = [], 1
    while True:
        sep = "&" if "?" in path else "?"
        chunk = api(f"{path}{sep}per_page=100&page={page}", token)
        out += chunk
        if len(chunk) < 100:
            return out
        page += 1


def esc(s):
    return html.escape(str(s), quote=True)


# ───────────────────────── datos ─────────────────────────
def fetch(user, token, cfg):
    pc = cfg["projects"]
    raw = paginate(f"/users/{user}/repos?type=owner&sort=pushed", token)
    repos = []
    for r in raw:
        if r.get("private") or r["name"].lower() == user.lower():
            continue
        if r.get("fork") and not pc["include_forks"]:
            continue
        if r.get("archived") and not pc["include_archived"]:
            continue
        if r["name"].lower() in {h.lower() for h in pc["hide"]}:
            continue
        repos.append(r)

    langs, topics = Counter(), Counter()
    for r in repos[:80]:
        for name, b in api(f"/repos/{user}/{r['name']}/languages", token).items():
            langs[name] += b
        for t in r.get("topics", []):
            topics[t] += 1

    info = api(f"/users/{user}", token)
    contrib = None
    if token:
        try:
            q = '{ user(login:"%s"){ contributionsCollection{ contributionCalendar{ totalContributions } } } }' % user
            res = api("https://api.github.com/graphql", token, {"query": q})
            contrib = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
        except Exception as e:  # noqa: BLE001
            print("aviso: no se pudieron leer las contribuciones:", e, file=sys.stderr)
    return dict(repos=repos, langs=langs, topics=topics,
                stars=sum(r["stargazers_count"] for r in repos),
                followers=info.get("followers", 0), public_repos=info.get("public_repos", len(repos)),
                contrib=contrib)


def mock_data():
    mk = lambda n, d, l, s, t: dict(name=n, html_url=f"https://github.com/demo/{n}", description=d,
                                    language=l, stargazers_count=s, pushed_at=t, topics=[])
    repos = [mk("previwerpdf", "Extensión Chrome/Firefox que fuerza la previsualización de PDF.", "JavaScript", 3, "2026-10-28T10:00:00Z"),
             mk("moodle-lab", "Entorno de pruebas local | con pipes y <etiquetas>.", "Python", 0, "2026-10-20T10:00:00Z"),
             mk("dotfiles", None, "Shell", 1, "2026-09-02T10:00:00Z")]
    repos[0]["topics"] = ["chrome-extension", "manifest-v3"]
    return dict(repos=repos, langs=Counter({"JavaScript": 52000, "Python": 31000, "Shell": 9000, "HTML": 6000, "CSS": 2500}),
                topics=Counter({"chrome-extension": 1, "manifest-v3": 1}), stars=4, followers=2, public_repos=3, contrib=187)


# ───────────────────────── Markdown ─────────────────────────
def badge(name, logo=None, color=None):
    label = quote(name.replace("-", "--").replace("_", "__").replace(" ", "_"), safe="")
    url = f"https://img.shields.io/badge/{label}-0b0b0f?style=flat-square"
    if logo:
        url += f"&logo={logo}&logoColor={color or 'ff3b3b'}"
    else:
        url += "&logo=gnometerminal&logoColor=ff3b3b"
    return f'<img src="{url}" alt="{esc(name)}" />'


def skills_md(data, cfg):
    sc = cfg["skills"]
    hide = {h.lower() for h in sc["hide"]}
    total = sum(data["langs"].values()) or 1
    names, seen = [], set()

    def add(name, logo=None, color=None):
        if name.lower() in seen or name.lower() in hide:
            return
        seen.add(name.lower())
        lg = LOGOS.get(name)
        names.append(badge(name, logo or (lg[0] if lg else None), color or (lg[1] if lg else None)))

    for name, b in data["langs"].most_common():
        if b / total * 100 >= sc["min_percent"] and len(names) < sc["max"]:
            add(name)
    if sc["use_topics"]:
        n = 0
        for t, _ in data["topics"].most_common():
            if n >= sc["max_topics"]:
                break
            if t.lower() not in seen and t.lower() not in hide:
                add(t)
                n += 1
    for e in sc["extra"]:  # skills manuales
        if isinstance(e, str):
            add(e)
        else:
            add(e["name"], e.get("logo"), e.get("color"))
    if not names:
        return "_Aún no hay suficiente código público para detectar skills._"
    return "<p>\n  " + "\n  ".join(names) + "\n</p>"


def projects_md(data, cfg):
    pc = cfg["projects"]
    repos = data["repos"]
    pinned = [r for n in pc["pin"] for r in repos if r["name"].lower() == n.lower()]
    rest = sorted((r for r in repos if r not in pinned), key=lambda r: r["pushed_at"], reverse=True)
    chosen = (pinned + rest)[: pc["max"]]
    if not chosen:
        return "_Aún no hay proyectos públicos. Aparecerán aquí solos cuando subas el primero._"
    lines = ["| Proyecto | Descripción | Lenguaje | ★ |", "|---|---|---|---|"]
    for r in chosen:
        desc = pc["descriptions"].get(r["name"]) or r.get("description") or "Sin descripción todavía"
        desc = esc(" ".join(desc.split())[:140]).replace("|", "&#124;")
        lines.append(f"| [**{esc(r['name'])}**]({r['html_url']}) | {desc} | {esc(r.get('language') or '-')} | {r['stargazers_count']} |")
    return "\n".join(lines)


def replace_block(text, tag, content):
    pat = re.compile(rf"(<!--{tag}:START-->)(.*?)(<!--{tag}:END-->)", re.S)
    if not pat.search(text):
        print(f"aviso: faltan los marcadores <!--{tag}:START--> / <!--{tag}:END--> en README.md", file=sys.stderr)
        return text
    return pat.sub(lambda m: f"{m.group(1)}\n{content}\n{m.group(3)}", text)


# ───────────────────────── SVG ─────────────────────────
CSS = (f"text{{font-family:'JetBrains Mono','Fira Code','DejaVu Sans Mono','Menlo','Consolas','Courier New',monospace}}"
       f".t{{fill:{RED};font-size:16px;font-weight:700}}.d{{fill:{DIM};font-size:12px}}"
       f".v{{fill:{FG};font-size:13px;font-weight:700}}.n{{fill:{FG};font-size:12px}}"
       f"@keyframes b{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}.c{{animation:b 1.1s steps(1) infinite}}")
W, H = 420, 190


def frame(title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(title)}">'
            f'<style>{CSS}</style><rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>'
            f'<text x="24" y="38" class="t">$ {esc(title)}</text>'
            f'<rect class="c" x="{24 + (len(title) + 3) * 9.6:.0f}" y="25" width="9" height="16" fill="{RED}"/>{body}</svg>')


def stats_svg(data, updated):
    rows = [("repos públicos", data["public_repos"]), ("estrellas recibidas", data["stars"]),
            ("seguidores", data["followers"]),
            ("contribuciones (1 año)", data["contrib"] if data["contrib"] is not None else "n/d")]
    body = "".join(f'<text x="24" y="{76 + i * 25}" class="d">{esc(k)}</text>'
                   f'<text x="{W - 24}" y="{76 + i * 25}" class="v" text-anchor="end">{esc(v)}</text>'
                   for i, (k, v) in enumerate(rows))
    body += f'<text x="24" y="{H - 16}" class="d" style="font-size:10px">actualizado {updated}</text>'
    return frame("git stats", body)


def languages_svg(data, updated):
    total = sum(data["langs"].values()) or 1
    top = data["langs"].most_common(6)
    other = total - sum(b for _, b in top)
    items = [(n, b) for n, b in top] + ([("otros", other)] if other > 0 else [])
    x, bar = 24, ""
    for i, (n, b) in enumerate(items):
        w = (W - 48) * b / total
        bar += f'<rect x="{x:.1f}" y="56" width="{w:.1f}" height="10" fill="{PALETTE[i] if i < len(PALETTE) else "#4a4a57"}"/>'
        x += w
    body = f'<clipPath id="r"><rect x="24" y="56" width="{W - 48}" height="10" rx="5"/></clipPath><g clip-path="url(#r)">{bar}</g>'
    for i, (n, b) in enumerate(items[:6]):
        cx, cy = 24 + (i % 2) * 190, 98 + (i // 2) * 24
        col = PALETTE[i] if i < len(PALETTE) else "#4a4a57"
        body += (f'<rect x="{cx}" y="{cy - 9}" width="10" height="10" rx="2" fill="{col}"/>'
                 f'<text x="{cx + 16}" y="{cy}" class="n">{esc(n[:13])} <tspan class="d">{b / total * 100:.1f}%</tspan></text>')
    if not items:
        body += f'<text x="24" y="100" class="d">sin datos de lenguajes todavía</text>'
    body += f'<text x="24" y="{H - 16}" class="d" style="font-size:10px">actualizado {updated}</text>'
    return frame("git langs", body)


def placeholder_svg(title):
    return frame(title, f'<text x="24" y="90" class="d">se generará solo en la primera ejecución</text>'
                        f'<text x="24" y="112" class="d">del workflow "Update profile"</text>')


# ───────────────────────── main ─────────────────────────
def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--mock", action="store_true", help="datos de ejemplo (sin red)")
    ap.add_argument("--placeholder", action="store_true", help="solo crea los SVG vacíos iniciales")
    a = ap.parse_args()
    assets = os.path.join(a.root, "assets")

    if a.placeholder:
        write(os.path.join(assets, "stats.svg"), placeholder_svg("git stats"))
        write(os.path.join(assets, "languages.svg"), placeholder_svg("git langs"))
        return

    cfg = load_cfg(a.root)
    user = os.environ.get("GH_USER") or cfg["username"]
    token = os.environ.get("GITHUB_TOKEN")
    if a.mock:
        data = mock_data()
    else:
        if not user:
            sys.exit("Falta el usuario: define GH_USER o 'username' en profile.config.json")
        data = fetch(user, token, cfg)

    updated = datetime.date.today().isoformat()
    write(os.path.join(assets, "stats.svg"), stats_svg(data, updated))
    write(os.path.join(assets, "languages.svg"), languages_svg(data, updated))

    readme = os.path.join(a.root, "README.md")
    with open(readme, encoding="utf-8") as f:
        text = f.read()
    text = replace_block(text, "SKILLS", skills_md(data, cfg))
    text = replace_block(text, "PROJECTS", projects_md(data, cfg))
    write(readme, text)
    print(f"OK: {len(data['repos'])} repos, {sum(data['langs'].values()):,} bytes de código analizados")


if __name__ == "__main__":
    main()
