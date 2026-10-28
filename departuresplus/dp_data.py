# Departures Plus - clock arithmetic, HTTP and departure parsing.
from __main__ import pool
import time, json
import dp_cfg

_MON = "JanFebMarAprMayJunJulAugSepOctNovDec"


def mono_ms():
    # Integer milliseconds. time.monotonic() is a 30-bit float on the device and
    # loses sub-second precision after a few hours of uptime.
    return time.monotonic_ns() // 1000000


def _days(y, m, d):
    # Days since 1970-01-01 (proleptic Gregorian).
    if m <= 2: y -= 1
    era = y // 400
    yoe = y - era * 400
    doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + d - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


def iso_secs(s):
    # "2026-10-09T02:16:00" -> seconds, read as a naive local time
    return _days(int(s[0:4]), int(s[5:7]), int(s[8:10])) * 86400 + int(s[11:13]) * 3600 + int(s[14:16]) * 60 + int(s[17:19])


def hdr_secs(v, gmt_off=7200):
    # "Fri, 09 Oct 2026 02:15:17 +0200" -> seconds in the server's local time.
    # A GMT date gets gmt_off added: two hours, the same assumption the stock app makes,
    # until a BVG answer tells the real offset.
    p = v.strip().split()
    mon = _MON.find(p[2]) // 3 + 1
    h = p[4].split(":")
    secs = _days(int(p[3]), mon, int(p[1])) * 86400 + int(h[0]) * 3600 + int(h[1]) * 60 + int(h[2])
    if len(p) > 5 and p[5] == "GMT": secs += gmt_off
    return secs


def split_secs(secs):
    # -> (hour, minute, weekday 0=Mon, day, month)
    days = secs // 86400
    rem = secs - days * 86400
    z = days + 719468
    era = z // 146097
    doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    d = doy - (153 * mp + 2) // 5 + 1
    m = mp + (3 if mp < 10 else -9)
    return rem // 3600, (rem % 3600) // 60, (days + 3) % 7, d, m


class Net:
    def __init__(self):
        self.t_off = None      # server local seconds minus monotonic seconds
        self.last = {}         # what the most recent request did, for /api/debug
        self.tz = None         # local offset from UTC in seconds, once a BVG answer told it
        self.ctx = None        # TLS context, made on the first HTTPS request
        self.idle = None       # called while waiting for an answer, so the ticker keeps moving

    def now(self):
        if self.t_off is None: return None
        return self.t_off + mono_ms() // 1000

    def set_tz(self, off):
        """The real offset from UTC, read from a BVG time. Corrects the clock taken from a GMT date header."""
        old = self.tz if self.tz is not None else 7200
        self.tz = off
        if self.t_off is not None and self.last.get("date", "")[-3:] == "GMT": self.t_off += off - old

    def _tls(self, sock, host):
        if self.ctx is None:
            try:
                from __main__ import ssl_context
                self.ctx = ssl_context
            except Exception:
                import ssl
                self.ctx = ssl.create_default_context()
        return self.ctx.wrap_socket(sock, server_hostname=host)

    def get(self, host, port, path, limit=60000, tls=False):
        """HTTP/1.0 GET, over TLS when asked. Returns the body as str, or None."""
        t0 = mono_ms()
        info = {"path": path, "at": t0 // 1000, "bytes": 0, "error": "", "date": "", "connect_ms": 0, "ms": 0, "ticker_turns": 0}
        self.last = info
        req = ("GET " + path + " HTTP/1.0\r\nHost: " + host + "\r\nUser-Agent: DeparturesPlus/" + dp_cfg.VERSION +
               " (MatrixBOX)\r\nAccept: application/json\r\nConnection: close\r\n\r\n")
        data = bytearray()
        s = None
        try:
            s = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
            if tls: s = self._tls(s, host)
            s.settimeout(8 if tls else 5)
            s.connect((host, int(port)))
            info["connect_ms"] = mono_ms() - t0
            out = req.encode("utf-8")
            sent = 0
            while sent < len(out):
                n = s.send(out[sent:])
                if n: sent += n
            buf = bytearray(1024)
            # The server takes a moment to answer. Short timeouts hand that time to the ticker instead of freezing it.
            if self.idle: s.settimeout(0.03)
            end = mono_ms() + (10000 if tls else 6000)
            while len(data) < limit:
                try:
                    n = s.recv_into(buf)
                except OSError as e:
                    if self.idle and _waiting(e) and mono_ms() < end:
                        info["ticker_turns"] += 1
                        self.idle()
                        continue
                    raise
                if not n: break
                data += buf[:n]
        except Exception as e:
            info["error"] = "socket: " + str(e)
            if not data: return None
        finally:
            try:
                if s: s.close()
            except Exception:
                pass
        info["bytes"] = len(data)
        info["ms"] = mono_ms() - t0
        try:
            raw = bytes(data)
            cut = raw.find(b"\r\n\r\n")
            skip = 4
            if cut < 0:
                cut = raw.find(b"\n\n")
                skip = 2
            if cut < 0:
                info["error"] = "no header end"
                return None
            # The server ends its status line with a bare \n, so split on \n and trim.
            for line in raw[:cut].decode("utf-8").split("\n"):
                line = line.strip()
                if line[:5].lower() == "date:":
                    info["date"] = line[5:].strip()
                    try: self.t_off = hdr_secs(line[5:], self.tz if self.tz is not None else 7200) - mono_ms() // 1000
                    except Exception as e: info["error"] = "date: " + str(e)
            if raw[:12].find(b" 200") < 0 and raw[:4] == b"HTTP":
                info["error"] = raw[:raw.find(b"\n")].decode("utf-8").strip()[:40]
            body = raw[cut + skip:].decode("utf-8")
            info["body"] = body[:120]
            return body
        except Exception as e:
            info["error"] = "decode: " + str(e)
            return None


def _waiting(e):
    """A read that timed out with nothing there yet, not a broken connection."""
    if getattr(e, "errno", None) in (11, 110, 116): return True     # EAGAIN, ETIMEDOUT on the board
    return "timed out" in str(e)


def clean_dest(d, strip_prefix, strip=(), district=False):
    d = str(d)
    cut = d.find("(")
    if cut > 0: d = d[:cut]
    d = d.replace("->", "\u2192")          # "Wittenau -> Bus 22": a real arrow
    if district:
        cut = d.rfind(", ")                # "Lankwitz, Halbauer Weg": the district is not needed on the display
        if cut > 0 and len(d) > cut + 3: d = d[cut + 2:]
    for s in strip:
        if s: d = d.replace(s, "")
    d = d.strip()
    if strip_prefix:
        for p in ("S+U ", "U ", "S "):
            if d[:len(p)] == p and len(d) > len(p) + 1:
                d = d[len(p):]
                break
    return d


def parse(body, st, cfg):
    """-> (departures, message). A departure is [when, line, mode, dest, delay, cancelled, color, direction, live].
    message is None, "loading", "nodata" or "msg:<text from the server>"."""
    try: j = json.loads(body)
    except Exception:
        # A very long list cut off by the size limit: keep the complete entries.
        cut = body.rfind('}, {"destination"')
        if cut < 0: return None, "nodata"
        try: j = json.loads(body[:cut + 1] + "]}")
        except Exception: return None, "nodata"
    deps = j.get("departures") if isinstance(j, dict) else None
    if not isinstance(deps, list):
        msg = str(j.get("msg", "")) if isinstance(j, dict) else ""
        if "oading" in msg: return None, "loading"
        return None, ("msg:" + msg[:40]) if msg else "nodata"
    f = _filters(st, cfg)
    out = []
    for d in deps:
        try:
            ln = d.get("line") or {}
            line = str(ln.get("id", "") or ln.get("designation", ""))
            if line == "0": line = ""
            dc = int(d.get("direction_code", 0) or 0)
            r = _keep(f, line, str(ln.get("transport_mode", "")), dc, cfg)
            if r is None: continue
            delay = d.get("delay") or 0
            try: delay = int(delay)
            except Exception: delay = 0
            out.append([iso_secs(d["expected"]), r[0], r[1], clean_dest(d.get("destination", ""), cfg["strip_prefix"], f[4], cfg.get("dest_district")), delay,
                        1 if d.get("cancelled") else 0, d.get("color") or "", dc,
                        0 if d.get("deviations") == "#" else 1])     # the server marks timetable-only times with "#"
        except Exception:
            pass
    out.sort(key=lambda x: x[0])
    return out[:60], None


def _filters(st, cfg):
    # "U2 S7" only these lines, "-M4" not this one, "U7:1" / "-U7:2" the same for one direction only
    inc = []; exc = []
    for x in str(st.get("lines", "")).upper().replace(",", " ").split():
        neg = x[:1] in ("-", "!")
        if neg: x = x[1:]
        p = x.split(":")
        try: rd = int(p[1]) if len(p) > 1 else 0
        except Exception: rd = 0
        if p[0]: (exc if neg else inc).append((p[0], rd))
    modes = [x.strip() for x in str(st.get("modes", "")).split(",") if x.strip()]
    strip = [x.strip() for x in str(cfg.get("strip", "")).split(",") if x.strip()]
    return inc, exc, modes, int(st.get("dir", 0) or 0), strip


def _keep(f, line, mode, dc, cfg):
    """-> (line, mode) when the station's filters let this departure through, else None."""
    inc, exc, modes, wdir = f[0], f[1], f[2], f[3]
    if modes and mode not in modes: return None
    key = line.upper().replace(" ", "")
    if inc and not [1 for r in inc if r[0] == key and (not r[1] or not dc or r[1] == dc)]: return None
    if [1 for r in exc if r[0] == key and (not r[1] or r[1] == dc)]: return None
    if wdir and dc and dc != wdir: return None
    cut = int(cfg.get("line_len", 0) or 0)
    return (line[:cut] if cut else line), mode


# ---- BVG/VBB API (v6.bvg.transport.rest), Berlin-Brandenburg only ---------------
BVG_MODE = {"subway": "METRO", "suburban": "TRAIN", "regional": "TRAIN", "express": "TRAIN", "tram": "TRAM", "bus": "BUS", "ferry": "SHIP"}


def bvg_ok(country, operator, sid):
    """The BVG API can stand in for this station: a VBB or Berlin station with a VBB number."""
    return country == "de" and operator in ("vbb", "be") and bvg_id(sid) is not None


def bvg_id(sid):
    # "de:11000:900100003" (T-Skylt's VBB numbers) or "900100003" -> "900100003"
    for p in reversed(str(sid).split(":")):
        if len(p) >= 6 and p.isdigit(): return p
    return None


def split_url(u):
    """"https://host[:port][/prefix]" -> (tls, host, port, prefix)"""
    u = str(u).strip()
    tls = u[:7] != "http://"
    for p in ("https://", "http://"):
        if u[:len(p)] == p: u = u[len(p):]
    cut = u.find("/")
    pre = ""
    if cut >= 0: pre = u[cut:].rstrip("/"); u = u[:cut]
    port = 443 if tls else 80
    cut = u.find(":")
    if cut >= 0:
        try: port = int(u[cut + 1:])
        except Exception: pass
        u = u[:cut]
    return tls, u, port, pre


def bvg_path(pre, sid, st, results):
    path = pre + "/stops/" + bvg_id(sid) + "/departures?results=" + str(results) + "&duration=120&remarks=false&linesOfStops=false&pretty=false"
    modes = [x.strip() for x in str(st.get("modes", "")).split(",") if x.strip()]
    if modes:      # leave out what the station does not show, so the answer stays small
        for k in BVG_MODE:
            if BVG_MODE[k] not in modes: path += "&" + k + "=false"
    return path


def _tz(t):
    # "2026-10-21T03:08:00+02:00" -> 7200
    try:
        z = t[19:]
        if len(z) < 6: return None
        v = int(z[1:3]) * 3600 + int(z[4:6]) * 60
        return -v if z[0] == "-" else v
    except Exception:
        return None


def parse_bvg(body, st, cfg, net):
    """Same result as parse(), from a BVG API answer."""
    try: j = json.loads(body)
    except Exception:
        cut = body.rfind(',{"tripId"')        # cut off by the size limit: keep the complete entries
        if cut < 0: return None, "nodata"
        try: j = json.loads(body[:cut] + "]}")
        except Exception: return None, "nodata"
    deps = j.get("departures") if isinstance(j, dict) else None
    if not isinstance(deps, list):
        msg = str(j.get("message", "")) if isinstance(j, dict) else ""
        return None, ("msg:" + msg[:40]) if msg else "nodata"
    f = _filters(st, cfg)
    out = []
    tz = None
    for d in deps:
        try:
            ln = d.get("line") or {}
            t = d.get("when") or d.get("plannedWhen")
            if not t: continue
            if tz is None: tz = _tz(t)
            r = _keep(f, str(ln.get("name", "")), BVG_MODE.get(str(ln.get("product", "")), "BUS"), 0, cfg)
            if r is None: continue
            dl = d.get("delay")
            out.append([iso_secs(t), r[0], r[1], clean_dest(d.get("direction") or "", cfg["strip_prefix"], f[4], cfg.get("dest_district")),
                        int(dl) // 60 if dl else 0, 1 if d.get("cancelled") else 0, "", 0,
                        0 if dl is None else 1])     # no delay value: timetable only
        except Exception:
            pass
        d = None
    j = None
    if tz is not None and tz != net.tz: net.set_tz(tz)
    out.sort(key=lambda x: x[0])
    return out[:60], None
