#!/usr/bin/env python3
"""The DAEMONS playground's server: the game in a browser, the companion beside it, what's new in each release.

    ./bindPlayground.sh                       the usual way (this, on port 4740)
    python3 server/playground.py              the latest ROM RELEASE in ../DAEMONS
    python3 server/playground.py --build      DAEMONS' engineGba build instead (what ./bindDaemons.sh last made)
    python3 server/playground.py --port 8000
    python3 server/playground.py --companion http://other-mac.local:8081/   the COMPANION tab (default: this host, 8081)

The page (site/index.html) asks for the edition, DEBUG or not, and a .sav to start from (or none: a new game); plays it
in the page on EmulatorJS's mGBA core, loaded from EmulatorJS's own CDN; keeps the save between visits and downloads it
at any time; and has the companion and the release notes in tabs beside the game.

THE ROMS ARE NOT IN THIS REPOSITORY, AND NEVER LEAVE THIS MACHINE'S NETWORK. They are read from DAEMONS' ROM RELEASE/
(beside this repository: ../DAEMONS, or $DAEMONS_ROOT) at the moment they are asked for -- the newest release each time,
so a release made while this runs is the next one played -- and this server answers only this machine, the private
ranges a LAN uses and the tailnet (100.64.0.0/10, fd7a:115c:a1e0::/48). Anything else is refused before a byte is read.
"""
import argparse, http.server, ipaddress, json, os, re, socket, subprocess, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))   # through DAEMONS/playground's symlink to the repo
DAEMONS = os.environ.get("DAEMONS_ROOT") or os.path.join(os.path.dirname(ROOT), "DAEMONS")
SITE = os.path.join(ROOT, "site")
RELEASES = os.path.join(DAEMONS, "ROM RELEASE")
NAMES = {"content": "daemonsContent", "context": "daemonsContext"}
TAILNET = [ipaddress.ip_network("100.64.0.0/10"), ipaddress.ip_network("fd7a:115c:a1e0::/48")]


def allowed(host):
    try:
        ip = ipaddress.ip_address(host.split("%")[0])
    except ValueError:
        return False
    if getattr(ip, "ipv4_mapped", None):
        ip = ip.ipv4_mapped
    return ip.is_loopback or ip.is_private or any(ip in n for n in TAILNET if n.version == ip.version)


def version_key(name):
    """v11.306.3 -> (11, 306, 3); a sealed group, v11.305.x, holds that bible's last release: after all its numbers."""
    m = re.match(r"v(\d+)\.(\d+)\.(\d+|x)$", name)
    if not m:
        return None
    return (int(m[1]), int(m[2]), 10 ** 6 if m[3] == "x" else int(m[3]))


def releases(base):
    """Every release folder under ROM RELEASE/, newest first: (name, path). A sealed group (v11.305.x) holds its last
    release's ROMs flattened, and its notes only as a PDF."""
    found = []
    for group in os.listdir(base) if os.path.isdir(base) else []:
        gpath = os.path.join(base, group)
        if not os.path.isdir(gpath):
            continue
        for name, path in [(group, gpath)] + [(r, os.path.join(gpath, r)) for r in os.listdir(gpath)]:
            if version_key(name) and os.path.isdir(path):
                found.append((name, path))
    return sorted(found, key=lambda r: version_key(r[0]), reverse=True)


def find_roms(build, base=RELEASES):
    """{content, context, content_debug, context_debug: path} and what to call where they came from."""
    if build:
        eng = os.path.join(DAEMONS, "engineGba")
        roms = {k: os.path.join(eng, n + ".gba") for k, n in NAMES.items()}
        roms.update({k + "_debug": os.path.join(eng, n + "_debug.gba") for k, n in NAMES.items()})
        return {k: p for k, p in roms.items() if os.path.isfile(p)}, "build"
    for label, path in releases(base):
        if all(os.path.isfile(os.path.join(path, n + ".gba")) for n in NAMES.values()):
            roms = {k: os.path.join(path, n + ".gba") for k, n in NAMES.items()}
            roms.update({k + "_debug": os.path.join(path, "DEBUG", n + "_debug.gba") for k, n in NAMES.items()})
            return {k: p for k, p in roms.items() if os.path.isfile(p)}, label
    return {}, None


def notes(base=RELEASES, most=12):
    """The newest releases' notes, as written (RELEASE_NOTES.md): what changed in the engine and the design since the
    one before. Their PATCHES table is for patching a cart, not for playing here, so it is left off."""
    out = []
    for label, path in releases(base):
        md = os.path.join(path, "RELEASE_NOTES.md")
        if os.path.isfile(md):
            text = open(md, encoding="utf-8").read()
            out.append({"release": label, "notes": re.split(r"\n## Patches\b", text)[0].rstrip() + "\n"})
            if len(out) == most:
                break
    return out


def local_name():
    """This machine on the local network: its Bonjour name on a Mac (what the companion's pairing uses), else its own."""
    try:
        out = subprocess.run(["scutil", "--get", "LocalHostName"], capture_output=True, text=True, timeout=3)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip() + ".local"
    except Exception:
        pass
    return socket.gethostname()


def tailnet_name():
    try:
        out = subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True, timeout=3).stdout
        return json.loads(out)["Self"]["DNSName"].rstrip(".")
    except Exception:
        return None


class Handler(http.server.SimpleHTTPRequestHandler):
    build, base, companion = False, RELEASES, None

    def __init__(self, *a, **k):
        super().__init__(*a, directory=SITE, **k)

    def log_message(self, fmt, *args):
        sys.stderr.write("playground: %s %s\n" % (self.client_address[0], fmt % args))

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def json(self, value, head=False):
        body = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head:
            self.wfile.write(body)

    def do_HEAD(self):
        self.do_GET(head=True)

    def do_GET(self, head=False):
        if not allowed(self.client_address[0]):
            return self.send_error(403, "this page is for this machine's network only")
        path = urllib.parse.urlparse(self.path).path
        if path == "/info.json":
            roms, label = find_roms(self.build, self.base)
            return self.json({"release": label, "editions": sorted(roms), "companion": self.companion}, head)
        if path == "/notes.json":
            return self.json([] if self.build else notes(self.base), head)
        # /rom/<release>/<file>.gba: the release in the path, so a browser's cache never plays an older one; the file name
        # the ROM's own, which the emulator names the save after -- the same save across releases, as in mGBA
        m = re.match(r"^/rom/[^/]+/(daemonsCont(?:ent|ext))(_debug)?\.gba$", path)
        if m:
            key = {v: k for k, v in NAMES.items()}[m[1]] + (m[2] or "")
            rom = find_roms(self.build, self.base)[0].get(key)
            if not rom:
                return self.send_error(404, "no such ROM in this release")
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(os.path.getsize(rom)))
            self.end_headers()
            if not head:
                with open(rom, "rb") as f:
                    while chunk := f.read(1 << 20):
                        self.wfile.write(chunk)
            return
        if path.startswith("/rom/"):
            return self.send_error(404)
        return super().do_GET() if not head else super().do_HEAD()


def main():
    ap = argparse.ArgumentParser(description="The DAEMONS playground: the game in a browser, the companion beside it")
    ap.add_argument("--port", type=int, default=4740)
    ap.add_argument("--build", action="store_true", help="DAEMONS' engineGba build, not the latest ROM RELEASE")
    ap.add_argument("--companion", help="the COMPANION tab's site (default: the page's own host, port 8081)")
    ap.add_argument("--releases", default=RELEASES, help="where the releases are (default: ../DAEMONS/ROM RELEASE)")
    a = ap.parse_args()
    roms, label = find_roms(a.build, a.releases)
    if not roms:
        where = "DAEMONS/engineGba (make -C engineGba firered ...)" if a.build else a.releases + " (DAEMONS tools/romrelease.py)"
        sys.exit(f"playground: no ROMs found in {where}")
    Handler.build, Handler.base, Handler.companion = a.build, a.releases, a.companion
    sys.stdout.reconfigure(line_buffering=True)
    srv = http.server.ThreadingHTTPServer(("0.0.0.0", a.port), Handler)
    print(f"playground: {label} -- {', '.join(sorted(roms))}")
    print(f"playground: http://localhost:{a.port}/")
    name = tailnet_name()
    if name:
        print(f"playground: http://{name}:{a.port}/   (the tailnet: the phone, away from home)")
    print(f"playground: http://{local_name()}:{a.port}/   (this network)")
    print("playground: answering this machine, private addresses and the tailnet only. Ctrl-C stops it.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
