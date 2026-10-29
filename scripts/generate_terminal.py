#!/usr/bin/env python3
"""
Genera assets/terminal.svg: una terminal Linux animada para el README de tu perfil de GitHub.

  - Escribe comandos letra a letra con cursor de bloque
  - Directorio de trabajo: ~/themandoftheredshadow
  - Logo de GitHub en ASCII girando 360 grados sin parar

Uso:   python3 generate_terminal.py            (sin dependencias, solo Python 3)
Edita la seccion CONFIG, ejecuta el script y sube el SVG resultante al repo.
"""
import math
import re

# ───────────────────────── CONFIG (edita aqui) ─────────────────────────
USER = "redshadow"                 # usuario del prompt
HOST = "github"                    # host del prompt
DIR = "themandoftheredshadow"      # directorio
OUTPUT = "assets/terminal.svg"

# Estilos: fg (texto), dim (gris), red, blue, green, yellow (para <placeholders>)
# Cada linea de salida es una lista de (texto, estilo).
SESSION = [
    ("out", [("Linux github 6.1.0-redshadow x86_64 GNU/Linux", "dim")]),
    ("out", [("Bienvenido a ", "dim"), (DIR, "red"), (" - acceso concedido", "dim")]),
    ("cmd", "~", f"cd {DIR}", []),
    ("cmd", f"~/{DIR}", "ls --color", [
        [("about.md  ", "fg"), ("skills/  ", "blue"), ("projects/  ", "blue"), ("status.sh", "green")],
    ]),
    ("cmd", f"~/{DIR}", "cat about.md", [
        [("# about.md", "dim")],
        [("> Hola, soy ", "fg"), ("<adar>", "yellow"), (".", "fg")],
        [("> ", "fg"), ("<Cibersegurata>", "yellow")],
        [("> ", "fg"), ("<Tu vida depende de los riesgos que estes dispuesto a tomar>", "yellow")],
    ]),
    ("cmd", f"~/{DIR}", "./status.sh", [
        [("[ ", "dim"), ("OK", "green"), (" ] kernel  -> ", "fg"), ("redshadow 1.0", "red")],
        [("[ ", "dim"), ("OK", "green"), (" ] cafe    -> ", "fg"), ("cargando...", "fg")],
        [("[ ", "dim"), ("OK", "green"), (" ] sombra  -> ", "fg"), ("activa", "fg")],
    ]),
    ("prompt", f"~/{DIR}"),   # prompt final con cursor parpadeando
]
# ───────────────────────────────────────────────────────────────────────

# Paleta
BG, BAR, BORDER = "#0b0b0f", "#14141a", "#2b2b35"
COL = {"fg": "#d8d8e0", "dim": "#6e6e7e", "red": "#ff3b3b", "blue": "#5aa9ff",
       "green": "#5fd75f", "yellow": "#ffd75f"}

# Geometria del terminal
CW, FS, LH = 8.4, 14, 20          # ancho de caracter, tamano de letra, alto de linea
X0, Y0 = 32, 76                   # origen del texto
W_SVG, H_SVG = 900, 372

# Tiempos (segundos)
TYPE_DT = 0.065                   # segundos por letra
HOLD = 6.5                        # pausa final con el cursor parpadeando

# Logo
LW, LH_ROWS = 44, 24              # columnas y filas del logo
LCW, LLH = 6.5, 12                # ancho y alto de celda del logo
LX, LY = 556, 54                  # posicion del logo
FRAMES = 48                       # pasos por vuelta completa
SPIN = 4.8                        # segundos por vuelta
RAMP = " .:+#@"

# ───────────────────── Logo de GitHub (path de Octicons) ─────────────────────
D = ("M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"
     ).replace("0016 8", "0 0 16 8")


def path_to_polygon(d):
    toks = re.findall(r"[A-Za-z]|[-+]?(?:\d*\.\d+|\d+\.?)", d)
    i, pts, cx, cy, cmd = 0, [], 0.0, 0.0, None

    def bez(p0, p1, p2, p3, n=16):
        out = []
        for k in range(1, n + 1):
            t = k / n
            u = 1 - t
            out.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                        u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
        return out

    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            i += 1
        if cmd == "M":
            cx, cy = float(toks[i]), float(toks[i + 1])
            i += 2
            pts.append((cx, cy))
            cmd = "L"
        elif cmd in "Cc":
            v = [float(x) for x in toks[i:i + 6]]
            i += 6
            if cmd == "c":
                v = [v[0]+cx, v[1]+cy, v[2]+cx, v[3]+cy, v[4]+cx, v[5]+cy]
            pts += bez((cx, cy), (v[0], v[1]), (v[2], v[3]), (v[4], v[5]))
            cx, cy = v[4], v[5]
        elif cmd == "A":
            _, _, _, _, sw, x, y = [float(t) for t in toks[i:i + 7]]
            i += 7
            a0, a1 = math.atan2(cy - 8, cx - 8), math.atan2(y - 8, x - 8)
            if sw == 0 and a1 > a0:
                a1 -= 2 * math.pi
            for k in range(1, 13):
                a = a0 + (a1 - a0) * k / 12
                pts.append((8 + 8 * math.cos(a), 8 + 8 * math.sin(a)))
            cx, cy = x, y
        elif cmd in "zZ":
            pass
        else:
            raise ValueError(cmd)
    return pts


POLY = path_to_polygon(D)


def inside(x, y):
    c, n = False, len(POLY)
    for k in range(n):
        x1, y1 = POLY[k]
        x2, y2 = POLY[(k + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def logo_rows(scale, mirrored, ss=3):
    """Devuelve filas [(fila, [(columna, caracter)])] del logo comprimido en horizontal."""
    rows = []
    for r in range(LH_ROWS):
        cells = []
        for c in range(LW):
            hit = 0
            for sy in range(ss):
                for sx in range(ss):
                    xs = (c + (sx + .5) / ss) / LW * 16            # coord. en pantalla
                    ys = (r + (sy + .5) / ss) / LH_ROWS * 16
                    dx = (xs - 8) / scale
                    x = 8 - dx if mirrored else 8 + dx
                    if 0 <= x <= 16 and inside(x, ys):
                        hit += 1
            if hit:
                ch = RAMP[min(len(RAMP) - 1, 1 + int(hit / (ss * ss) * (len(RAMP) - 1.001)))]
                if ch != " ":
                    cells.append((c, ch))
        rows.append((r, cells))
    return rows


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def glyph_text(spans, x0, y, cw):
    """<text> con posicion X exacta por glifo: alinea con el cursor aunque cambie la fuente."""
    out, col = [], 0
    for txt, st in spans:
        xs, chars = [], []
        for ch in txt:
            if ch != " ":
                xs.append(f"{x0 + col * cw:.1f}")
                chars.append(esc(ch))
            col += 1
        if chars:
            out.append(f'<tspan x="{" ".join(xs)}" class="{st}">{"".join(chars)}</tspan>')
    return f'<text y="{y}">{"".join(out)}</text>'


def pct(t, total):
    return round(t / total * 100, 3)


# ───────────────────── Construccion de la sesion ─────────────────────
def build():
    prompt_spans = lambda path: [(f"{USER}@{HOST}", "red"), (":", "fg"), (path, "blue"), ("$ ", "fg")]
    plen = lambda path: len(f"{USER}@{HOST}:{path}$ ")

    # 1) Linea de tiempo
    t = 0.5
    items, row = [], 0
    for ev in SESSION:
        if ev[0] == "out":
            items.append(dict(kind="out", spans=ev[1], row=row, t=t))
            row += 1
            t += 0.35
        elif ev[0] == "cmd":
            _, path, cmd, outs = ev
            tp = t + 0.7
            ts = tp + 0.45
            te = ts + len(cmd) * TYPE_DT
            t_out = te + 0.4
            it = dict(kind="cmd", path=path, cmd=cmd, row=row, tp=tp, ts=ts, te=te)
            row += 1
            it["outs"] = []
            for o in outs:
                it["outs"].append(dict(spans=o, row=row, t=t_out))
                row += 1
                t_out += 0.28
            it["t_end"] = it["outs"][0]["t"] if outs else te + 0.4
            items.append(it)
            t = t_out if outs else te + 0.4
        elif ev[0] == "prompt":
            items.append(dict(kind="prompt", path=ev[1], row=row, tp=t + 0.5))
            t += 0.5
    total = t + HOLD
    T = round(total, 2)

    css, body_text, body_cover, body_cursor = [], [], [], []
    fade_names = {}

    def appear(tt):
        """Devuelve el nombre de un keyframe 'aparece en tt' (deduplicado)."""
        key = round(tt, 3)
        if key not in fade_names:
            n = f"a{len(fade_names)}"
            fade_names[key] = n
            p = pct(tt, T)
            css.append(f"@keyframes {n}{{0%,{max(p - .01, 0)}%{{opacity:0}}{p}%,100%{{opacity:1}}}}")
        return fade_names[key]

    y_of = lambda r: Y0 + r * LH

    for ci, it in enumerate(items):
        y = y_of(it["row"])
        if it["kind"] == "out":
            body_text.append(f'<g class="i" style="animation-name:{appear(it["t"])}">'
                             f'{glyph_text(it["spans"], X0, y, CW)}</g>')
        elif it["kind"] == "cmd":
            pl = plen(it["path"])
            body_text.append(f'<g class="i" style="animation-name:{appear(it["tp"])}">'
                             f'{glyph_text(prompt_spans(it["path"]), X0, y, CW)}</g>')
            first, _, rest = it["cmd"].partition(" ")
            cmd_spans = [(first, "green")] + ([(" " + rest, "fg")] if rest else [])
            cx0 = X0 + pl * CW
            body_text.append(glyph_text(cmd_spans, cx0, y, CW))
            n = len(it["cmd"])
            wpx = round(n * CW, 1)
            # cubre-texto: se desplaza a la derecha en pasos (revela letra a letra)
            ps, pe = pct(it["ts"], T), pct(it["te"], T)
            css.append(f"@keyframes c{ci}{{0%,{ps}%{{transform:translateX(0)}}{pe}%,100%{{transform:translateX({wpx}px)}}}}")
            body_cover.append(f'<rect x="{cx0:.1f}" y="{y - 14}" width="{wpx}" height="19" fill="{BG}" '
                              f'style="animation:c{ci} {T}s infinite steps({n},end)"/>')
            # cursor de bloque: sigue la escritura y desaparece al salir la respuesta
            vp0, vp1 = pct(it["tp"], T), pct(it["t_end"], T)
            css.append(f"@keyframes v{ci}{{0%,{vp0 - .01}%{{opacity:0}}{vp0}%,{vp1 - .01}%{{opacity:1}}{vp1}%,100%{{opacity:0}}}}")
            body_cursor.append(f'<g style="animation:v{ci} {T}s infinite linear;opacity:0">'
                               f'<rect x="{cx0:.1f}" y="{y - 14}" width="{CW}" height="19" fill="{COL["red"]}" '
                               f'style="animation:c{ci} {T}s infinite steps({n},end)"/></g>')
            for o in it["outs"]:
                body_text.append(f'<g class="i" style="animation-name:{appear(o["t"])}">'
                                 f'{glyph_text(o["spans"], X0, y_of(o["row"]), CW)}</g>')
        else:  # prompt final
            pl = plen(it["path"])
            body_text.append(f'<g class="i" style="animation-name:{appear(it["tp"])}">'
                             f'{glyph_text(prompt_spans(it["path"]), X0, y, CW)}</g>')
            vp0 = pct(it["tp"], T)
            css.append(f"@keyframes v{ci}{{0%,{vp0 - .01}%{{opacity:0}}{vp0}%,100%{{opacity:1}}}}")
            body_cursor.append(f'<g style="animation:v{ci} {T}s infinite linear;opacity:0">'
                               f'<rect class="blink" x="{X0 + pl * CW:.1f}" y="{y - 14}" width="{CW}" height="19" '
                               f'fill="{COL["red"]}"/></g>')

    # 2) Logo girando
    frames, uses = {}, []
    for j in range(FRAMES):
        th = 2 * math.pi * j / FRAMES
        c = math.cos(th)
        mirrored = c < -1e-9
        s = max(abs(c), 0.07)
        key = (round(s, 3), mirrored)
        if key not in frames:
            rows = logo_rows(s, mirrored)
            fid = f"f{len(frames)}"
            parts = []
            for r, cells in rows:
                if not cells:
                    continue
                xs = " ".join(f"{LX + c_ * LCW:.1f}" for c_, _ in cells)
                chars = esc("".join(ch for _, ch in cells))
                parts.append(f'<text y="{LY + (r + 1) * LLH}" x="{xs}">{chars}</text>')
            op = round(0.5 + 0.5 * s, 2)
            frames[key] = (fid, f'<g id="{fid}" opacity="{op}">{"".join(parts)}</g>')
        uses.append(f'<use xlink:href="#{frames[key][0]}" class="sl" style="animation-delay:{j * SPIN / FRAMES:.3f}s"/>')
    defs_frames = "".join(v[1] for v in frames.values())

    step = round(100 / FRAMES, 4)
    css_base = f"""
text{{font-family:'JetBrains Mono','Fira Code','DejaVu Sans Mono','Menlo','Consolas','Courier New',monospace;font-size:{FS}px;white-space:pre}}
.fg{{fill:{COL['fg']}}}.dim{{fill:{COL['dim']}}}.red{{fill:{COL['red']};font-weight:700}}
.blue{{fill:{COL['blue']};font-weight:700}}.green{{fill:{COL['green']}}}.yellow{{fill:{COL['yellow']}}}
.i{{opacity:0;animation-duration:{T}s;animation-iteration-count:infinite;animation-timing-function:linear}}
.blink{{animation:blink 1.1s steps(1) infinite}}
@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
.logo text{{font-size:11px}}
.sl{{opacity:0;animation:spin {SPIN}s infinite linear}}
@keyframes spin{{0%,{step - .02}%{{opacity:1}}{step}%,100%{{opacity:0}}}}
#screen{{animation:clear {T}s infinite linear}}
@keyframes clear{{0%,{pct(T - 0.6, T)}%{{opacity:1}}{pct(T - 0.15, T)}%,100%{{opacity:0}}}}
"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W_SVG} {H_SVG}" width="{W_SVG}" height="{H_SVG}" role="img" aria-label="Terminal Linux en ~/{DIR} con logo de GitHub girando">
<title>~/{DIR}</title>
<defs>
<style>{css_base}{''.join(css)}</style>
<linearGradient id="lg" gradientUnits="userSpaceOnUse" x1="0" y1="{LY}" x2="0" y2="{LY + LH_ROWS * LLH}">
<stop offset="0" stop-color="#ff6a5a"/><stop offset="1" stop-color="#b30018"/></linearGradient>
<radialGradient id="glow" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#ff1f1f" stop-opacity=".22"/><stop offset="1" stop-color="#ff1f1f" stop-opacity="0"/></radialGradient>
{defs_frames}
</defs>
<rect x="10" y="10" width="{W_SVG - 20}" height="{H_SVG - 20}" rx="10" fill="{BG}" stroke="{BORDER}"/>
<path d="M10 44V20a10 10 0 0 1 10-10h{W_SVG - 40}a10 10 0 0 1 10 10v24z" fill="{BAR}"/>
<line x1="10" y1="44" x2="{W_SVG - 10}" y2="44" stroke="{BORDER}"/>
<circle cx="34" cy="27" r="6" fill="#ff5f56"/><circle cx="54" cy="27" r="6" fill="#ffbd2e"/><circle cx="74" cy="27" r="6" fill="#27c93f"/>
<text x="{W_SVG // 2}" y="32" text-anchor="middle" class="dim" style="font-size:12px">{USER}@{HOST}: ~/{DIR}</text>
<g id="screen">
{''.join(body_text)}
{''.join(body_cover)}
{''.join(body_cursor)}
</g>
<ellipse cx="{LX + LW * LCW / 2}" cy="{LY + LH_ROWS * LLH / 2}" rx="190" ry="175" fill="url(#glow)"/>
<g class="logo" fill="url(#lg)" style="font-family:'DejaVu Sans Mono','Menlo','Consolas','Courier New',monospace;white-space:pre">
{''.join(uses)}
</g>
</svg>
"""
    return svg, T, len(frames)


if __name__ == "__main__":
    svg, T, nf = build()
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"OK -> {OUTPUT}  ({len(svg) / 1024:.1f} KB, bucle {T}s, {nf} fotogramas unicos de logo)")
