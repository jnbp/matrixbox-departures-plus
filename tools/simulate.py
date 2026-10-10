#!/usr/bin/env python3
"""Tries Departures Plus in the MatrixBOX simulator with made-up departures, in any board size.

    pip install git+https://github.com/MatrixBOX-dev/simulator
    git clone https://github.com/MatrixBOX-dev/matrixbox
    python3 tools/simulate.py matrixbox --size XL

Starts the demo data server and the app, points the app at the demo data and opens the
simulator. The settings page is at http://127.0.0.1:8080/. Ctrl+C ends everything.
"""
import argparse, json, os, shutil, subprocess, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIONS = [("Alexanderplatz", "de:11000:900100003", 4), ("Hauptbahnhof", "de:11000:900003201", 9), ("Zoologischer Garten", "de:11000:900023201", 0)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("matrixbox", help="a clone of the MatrixBOX firmware")
    ap.add_argument("--size", default="X", choices=("XS", "X", "XL", "2X"))
    a = ap.parse_args()
    app = os.path.join(os.path.abspath(a.matrixbox), "apps", "departuresplus")
    shutil.copytree(os.path.join(ROOT, "departuresplus"), app, dirs_exist_ok=True)
    procs = [subprocess.Popen([sys.executable, os.path.join(ROOT, "tools", "demo_server.py")]),
             subprocess.Popen(["matrixbox", "app", app, "--size", a.size, "--reset"])]
    try:
        for _ in range(40):
            time.sleep(1)
            try:
                urllib.request.urlopen("http://127.0.0.1:8080/api/state", timeout=3).read()
                break
            except Exception:
                pass
        cfg = {"host": "127.0.0.1", "port": 9090,
               "stations": [{"name": n, "country": "de", "operator": "vbb", "id": i, "walk": w, "on": 1} for n, i, w in STATIONS]}
        req = urllib.request.Request("http://127.0.0.1:8080/api/config", data=json.dumps(cfg).encode(), method="POST")
        urllib.request.urlopen(req, timeout=10).read()
        print("Departures Plus runs in size %s. Settings page: http://127.0.0.1:8080/" % a.size)
        subprocess.call(["matrixbox", "simulator"])
    except KeyboardInterrupt:
        pass
    finally:
        for p in procs: p.terminate()


if __name__ == "__main__":
    main()
