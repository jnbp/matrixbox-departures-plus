#!/usr/bin/env python3
"""Renders the pictures in the README from the real app, running in the MatrixBOX simulator.

    pip install pillow git+https://github.com/MatrixBOX-dev/simulator
    git clone https://github.com/MatrixBOX-dev/matrixbox
    python3 tools/render_docs.py matrixbox

With playwright installed (pip install playwright, playwright install chromium) it also
takes the screenshot of the settings page.
"""
import json, os, shutil, subprocess, sys, tempfile, time, urllib.request
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
SCALE = 6


def station(name, sid, walk):
    return {"name": name, "country": "de", "operator": "vbb", "id": sid, "walk": walk, "on": 1}


ALEX = station("Alexanderplatz", "de:11000:900100003", 4)
HBF = station("Hauptbahnhof", "de:11000:900003201", 9)
ZOO = station("Zoologischer Garten", "de:11000:900023201", 0)
BASE = {"host": "127.0.0.1", "port": 9090, "stations": [ALEX, HBF, ZOO], "intro": 0, "blink": "off", "walk": "show",
        "ticker_dev": 1}       # the ticker shows the demo server's service notice


def shot(app, tmp, name, frames=60, **changes):
    """One frame of the app with these settings, as a 128x32 image."""
    cfg = dict(BASE)
    cfg.update(changes)
    seed = os.path.join(tmp, name + ".json")
    out = os.path.join(tmp, name + ".png")
    with open(seed, "w") as f: json.dump(cfg, f)
    subprocess.run(["matrixbox", "screenshot", app, "--settings", seed, "--rename-settings", "departuresplus.json",
                    "--size", "X", "--after-frames", str(frames), "--gamma", "3", "-o", out],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return Image.open(out).convert("RGB").resize((128, 32), Image.NEAREST)


def led(im):
    """Draws the frame as round LEDs with a little glow, inside a dark housing."""
    s = SCALE
    w, h = im.size
    lit = Image.new("RGB", (w * s, h * s), (0, 0, 0))
    off = Image.new("RGB", (w * s, h * s), (7, 7, 9))
    dl = ImageDraw.Draw(lit)
    do = ImageDraw.Draw(off)
    px = im.load()
    for y in range(h):
        for x in range(w):
            box = (x * s + 1, y * s + 1, x * s + s - 1, y * s + s - 1)
            do.ellipse(box, fill=(20, 20, 23))
            if sum(px[x, y]) > 24: dl.ellipse(box, fill=px[x, y])
    glow = lit.filter(ImageFilter.GaussianBlur(s * 0.7)).point(lambda v: v * 0.55)
    face = ImageChops.lighter(ImageChops.add(off, glow), lit)
    pad = 3 * s
    panel = Image.new("RGB", (w * s + 2 * pad, h * s + 2 * pad), (255, 255, 255))
    ImageDraw.Draw(panel).rounded_rectangle((0, 0, panel.width - 1, panel.height - 1), radius=2 * s, fill=(26, 26, 30))
    panel.paste(face, (pad, pad))
    return panel


def font(size):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                 "/usr/share/fonts/truetype/freefont/FreeSans.ttf", "/Library/Fonts/Arial.ttf", "C:/Windows/Fonts/arial.ttf"):
        if os.path.exists(path): return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def sheet(items, columns=2):
    """A white sheet of captioned panels."""
    f = font(22)
    cell = led(items[0][1])
    gap = 34
    cap = 40
    rows = (len(items) + columns - 1) // columns
    out = Image.new("RGB", (columns * cell.width + (columns + 1) * gap, rows * (cell.height + cap + gap) + gap), (255, 255, 255))
    d = ImageDraw.Draw(out)
    for i, (text, im) in enumerate(items):
        x = gap + (i % columns) * (cell.width + gap)
        y = gap + (i // columns) * (cell.height + cap + gap)
        d.text((x + 4, y), text, fill=(40, 40, 46), font=f)
        out.paste(led(im), (x, y + cap))
    return out


def displays(app, tmp):
    title = dict(intro=10, frames=25)
    hero = [(shot(app, tmp, "t1", **title), 1500), (shot(app, tmp, "d1"), 3000),
            (shot(app, tmp, "t2", stations=[HBF, ZOO, ALEX], **title), 1500), (shot(app, tmp, "d2", stations=[HBF, ZOO, ALEX]), 3000),
            (shot(app, tmp, "t3", stations=[ZOO, ALEX, HBF], **title), 1500), (shot(app, tmp, "d3", stations=[ZOO, ALEX, HBF]), 3000)]
    frames = [led(im).quantize(colors=128, dither=Image.Dither.NONE) for im, ms in hero]
    frames[0].save(os.path.join(DOCS, "rotation.gif"), save_all=True, append_images=frames[1:],
                   duration=[ms for im, ms in hero], loop=0)
    sheet([
        ("Station title with its lines and the walking time", hero[0][0]),
        ("Line signets, clock, date and the operator's service notice", hero[1][0]),
        ("Large text: two departures, status row below", shot(app, tmp, "large", font="large", stations=[ZOO, ALEX, HBF])),
        ("Compact text: five rows", shot(app, tmp, "compact", font="compact", status="off", stations=[HBF, ZOO, ALEX])),
        ("One mixed list of all stations", shot(app, tmp, "merged", mode="merged")),
        ("Real-time mark behind live departures, no date", shot(app, tmp, "live", live="wave", live_anim=0, st_date="off")),
        ("Colored text instead of signets, times as 3'", shot(app, tmp, "text", badge="text", time_fmt="tick", stations=[ZOO, ALEX, HBF])),
        ("Any LED tone, here white, and no date", shot(app, tmp, "white", tone="white", st_date="off", stations=[HBF, ZOO, ALEX])),
    ]).save(os.path.join(DOCS, "display.png"))


def settings_page(app):
    """Screenshot of the settings page, served by the app itself."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright is not installed, skipping the settings page")
        return
    proc = subprocess.Popen(["matrixbox", "app", app, "--size", "X", "--reset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for attempt in range(40):
            time.sleep(1)
            try:
                urllib.request.urlopen("http://127.0.0.1:8080/api/state", timeout=3).read()
                break
            except Exception:
                pass
        req = urllib.request.Request("http://127.0.0.1:8080/api/config", data=json.dumps(dict(BASE, intro=2)).encode(), method="POST")
        urllib.request.urlopen(req, timeout=10).read()
        time.sleep(12)
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get("DP_CHROME") or None)
            page = browser.new_page(viewport={"width": 860, "height": 1180}, device_scale_factor=1.5)
            page.goto("http://127.0.0.1:8080/")
            page.wait_for_timeout(4000)
            page.screenshot(path=os.path.join(DOCS, "settings.png"))
            browser.close()
    finally:
        proc.terminate()


def main():
    if len(sys.argv) != 2: sys.exit(__doc__)
    app = os.path.join(os.path.abspath(sys.argv[1]), "apps", "departuresplus")
    shutil.copytree(os.path.join(ROOT, "departuresplus"), app, dirs_exist_ok=True)
    os.makedirs(DOCS, exist_ok=True)
    server = subprocess.Popen([sys.executable, os.path.join(ROOT, "tools", "demo_server.py")])
    time.sleep(1)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            displays(app, tmp)
        settings_page(app)
    finally:
        server.terminate()


if __name__ == "__main__":
    main()
