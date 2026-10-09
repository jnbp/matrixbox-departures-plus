#!/usr/bin/env python3
"""Copies Departures Plus onto a MatrixBOX over WiFi, through the board's own file manager.

    python3 install.py 192.168.1.50

The board must not be plugged into a computer by USB while you do this:
its storage is read-only to its own code then. An older version on the board
is removed first; saved settings (departuresplus.json) are left alone.
"""
import json, os, sys, time, urllib.request

PREFIX = None

def post(ip, route, path, body=b""):
    req = urllib.request.Request("http://%s%s/%s" % (ip, PREFIX, route), data=body, method="POST", headers={"x-path": path})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8") or "{}")

def get(ip, path):
    try: urllib.request.urlopen("http://%s%s" % (ip, path), timeout=15).read()
    except Exception: pass

def find_prefix(ip):
    # Newer firmware serves the file manager under /system/fm, older (e.g. v0.97) under /fm.
    global PREFIX
    for attempt in range(4):
        for cand in ("/system/fm", "/fm"):
            PREFIX = cand
            try:
                if post(ip, "ls", "/").get("items"): return True
            except Exception:
                pass
        time.sleep(2)
    return False

def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    ip = sys.argv[1]
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "departuresplus")
    get(ip, "/exit")                       # the file manager only answers on the home screen
    time.sleep(3)
    if not find_prefix(ip):
        sys.exit("No file manager found at %s. Right IP, same network, board on its home screen?" % ip)
    try: post(ip, "mkdir", "/departuresplus")
    except Exception: pass
    # Remove the previous version first: the board has little room, and overwriting a file
    # needs space for both copies. Stations and settings (departuresplus.json) stay.
    try:
        for item in post(ip, "ls", "/departuresplus").get("items", []):
            if item.get("n") != "departuresplus.json": post(ip, "del", "/departuresplus/" + item["n"])
    except Exception:
        pass
    bad = 0
    for name in sorted(os.listdir(src)):
        if name.startswith(".") or name == "departuresplus.json" or name == "__pycache__":
            continue
        with open(os.path.join(src, name), "rb") as f:
            data = f.read()
        res = post(ip, "write", "/departuresplus/" + name, data)
        bad += 0 if res.get("ok") else 1
        print(("ok     " if res.get("ok") else "FAILED ") + name + ("" if res.get("ok") else "  " + str(res.get("error"))))
    if bad:
        sys.exit("Incomplete. Storage full or read-only (USB connected)?")
    get(ip, "/?run=departuresplus")
    print("Done. Settings page: http://%s/" % ip)

if __name__ == "__main__":
    main()
