#!/usr/bin/env python3
"""Demo data server for trying Departures Plus without the real one.

Answers like T-Skylt's data server does (same JSON, same odd HTTP framing), with
made-up departures for three big Berlin stations. Used for the simulator and for the
pictures in the README.

    python3 tools/demo_server.py          # listens on 127.0.0.1:9090
"""
import json
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# id: (name, [(line, mode, destination, direction, every N minutes, offset)])
STATIONS = {
    "de:11000:900100003": ("S+U Alexanderplatz Bhf (Berlin)", [
        ("U2", "METRO", "S+U Pankow ", 1, 5, 1), ("U8", "METRO", "S+U Hermannstr. ", 2, 5, 3),
        ("U5", "METRO", "U Hönow ", 1, 5, 2), ("S7", "TRAIN", "S Potsdam Hauptbahnhof ", 2, 10, 4),
        ("M4", "TRAM", "Falkenberg ", 1, 10, 0), ("100", "BUS", "S+U Zoologischer Garten ", 2, 10, 7)]),
    "de:11000:900003201": ("S+U Berlin Hauptbahnhof", [
        ("S3", "TRAIN", "S Erkner ", 1, 10, 1), ("S5", "TRAIN", "S Strausberg Nord ", 1, 10, 5),
        ("S9", "TRAIN", "S Flughafen BER ", 2, 20, 3), ("U5", "METRO", "U Hönow ", 1, 5, 2),
        ("M10", "TRAM", "S+U Warschauer Str. ", 1, 10, 6), ("RE1", "TRAIN", "Frankfurt (Oder) ", 1, 30, 12)]),
    "de:11000:900023201": ("S+U Zoologischer Garten Bhf (Berlin)", [
        ("U9", "METRO", "U Osloer Str. ", 1, 5, 0), ("U2", "METRO", "U Ruhleben ", 2, 5, 2),
        ("S5", "TRAIN", "S Westkreuz ", 2, 10, 4), ("S7", "TRAIN", "S Ahrensfelde ", 1, 10, 1),
        ("X10", "BUS", "Teltow ", 1, 20, 6), ("200", "BUS", "Michelangelostr. ", 1, 10, 8)]),
}
TIMETABLE_ONLY = ("U8", "100", "X10", "S9")      # lines without real-time data in this demo


def departures(sid, now):
    out = []
    base = now.replace(second=0, microsecond=0)
    minute = base.hour * 60 + base.minute
    for line, mode, dest, direction, every, offset in STATIONS[sid][1]:
        first = (minute - offset) // every
        for i in range(6):
            t = base.replace(hour=0, minute=0) + timedelta(minutes=(first + i) * every + offset)
            if t < now - timedelta(seconds=30): continue
            live = line not in TIMETABLE_ONLY and (t - now).total_seconds() < 900
            out.append({"destination": dest, "direction_code": direction, "expected": t.strftime("%Y-%m-%dT%H:%M:%S"),
                        "line": {"id": line, "transport_mode": mode}, "deviations": [] if live else "#"})
    return out


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass

    def do_GET(self):
        url = urlparse(self.path)
        sid = parse_qs(url.query).get("station", [""])[0]
        now = datetime.now()
        if url.path == "/get_departures":
            if sid in STATIONS: body = {"departures": departures(sid, now), "timestamp": now.timestamp()}
            else: body = {"timestamp": 0, "departures": "", "msg": "Loading..."}
        elif url.path == "/search_stop":
            body = {v[0]: k for k, v in STATIONS.items() if sid.lower() in v[0].lower()} or {"No stations found!": 0}
        elif url.path == "/get_deviations":
            body = ["U2: lift out of service"]
        else:
            body = {}
        # Like the real server: a bare \n after the status line, no Content-Length, closing ends the body.
        self.wfile.write(b"HTTP/1.0 200 OK\nDate: " + now.strftime("%a, %d %b %Y %H:%M:%S +0200").encode() +
                         b"\r\nConnection: close\r\n\r\n" + (json.dumps(body) + "\n").encode())


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 9090), Handler).serve_forever()
