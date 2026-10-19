#!/usr/bin/env python3
"""The DAEMONS playground's server: the game in a browser, the companion beside it, what's new in each release.

    ./bindPlayground.sh                       the usual way (this, on port 4740)
    python3 server/playground.py              the latest ROM RELEASE in ../DAEMONS
    python3 server/playground.py --build      DAEMONS' engineGba build instead (what ./bindDaemons.sh last made)
    python3 server/playground.py --port 8000
    python3 server/playground.py --companion http://localhost:8081/   the COMPANION tab's site (default: its own export)
    python3 server/playground.py --no-companion       the tab on its site's own server, not the playground's companion

The page (site/index.html) asks for the edition, DEBUG or not, and a .sav to start from (or none: a new game); plays it
in the page on EmulatorJS's mGBA core, loaded from EmulatorJS's own CDN; keeps the save between visits and downloads it
at any time; and has the companion and the release notes in tabs beside the game.

THE COMPANION TAB IS A COMPANION OF THE PLAYGROUND'S OWN (DAEMONS T-428, companion C-169), never the user's: one for each
build (CONTENT 4731, CONTEXT 4732, their DEBUG builds 4733 and 4734), each with its own database under data/companions/
and, for its save, the browser's -- the page posts the game's save here (POST /save/<build>.sav, into data/saves/)
whenever it changes, and asks its companion to SYNC as the tab opens. A daemon SENT AWAY in the game is taken by that
SYNC, and the save the companion wrote goes back into the game. Each companion is daemons-companion's own server (beside
DAEMONS, linked as DAEMONS/companion), started the first time its build asks for it and stopped with this one. It listens
on this machine only: the companion's site reaches it through this server, at /companion/<build>/, so a phone on the
tailnet uses it with no pairing -- and what only the Mac may do (pairing, its dialogs, the network, the save's path)
is refused here. --no-companion leaves the tab on the companion site's own server, as before.

THE COMPANION'S SITE IS THE PLAYGROUND'S OWN TOO: a static web export of daemons-companion's app (expo export --platform
web, into data/companion-site/), made as this starts and again whenever the companion's HEAD or what is uncommitted in
its app/, server/src or server/data has changed since the last one, and served from here -- /companion-site/, the page's
own origin, so the tab needs no Expo dev server and a phone loads one minified bundle. The export names its files from
the root (/_expo/..., /assets/...; its app.json sets no baseUrl), and this site has neither, so they are served there.
--companion URL shows another site instead (the Expo dev server's, http://localhost:8081/, to work on the companion);
with no export to be had -- no app installed, no Node, or the export failed -- the tab falls back to this host's 8081.

THE ROMS ARE NOT IN THIS REPOSITORY, AND NEVER LEAVE THIS MACHINE'S NETWORK. They are read from DAEMONS' ROM RELEASE/
(beside this repository: ../DAEMONS, or $DAEMONS_ROOT) at the moment they are asked for -- the newest release each time,
so a release made while this runs is the next one played -- and this server answers only this machine, the private
ranges a LAN uses and the tailnet (100.64.0.0/10, fd7a:115c:a1e0::/48). Anything else is refused before a byte is read.
"""
import argparse, hashlib, http.client, http.server, ipaddress, json, os, re, shutil, signal, socket, subprocess, sys
import threading, time, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))   # through DAEMONS/playground's symlink to the repo
DAEMONS = os.environ.get("DAEMONS_ROOT") or os.path.join(os.path.dirname(ROOT), "DAEMONS")
SITE = os.path.join(ROOT, "site")
RELEASES = os.path.join(DAEMONS, "ROM RELEASE")
NAMES = {"content": "daemonsContent", "context": "daemonsContext"}
TAILNET = [ipaddress.ip_network("100.64.0.0/10"), ipaddress.ip_network("fd7a:115c:a1e0::/48")]
DATA = os.path.join(ROOT, "data")               # gitignored: the browser's saves, and the playground's own companions
COMPANION = os.environ.get("COMPANION_ROOT") or os.path.join(DAEMONS, "companion")
BUILDS = {"content": "daemonsContent", "context": "daemonsContext",
          "content_debug": "daemonsContent_debug", "context_debug": "daemonsContext_debug"}
SAVE_MOST = 256 * 1024                          # a save is 128 KB (mGBA's, 16 bytes more); anything near this is not one


def allowed(host):
    try:
        ip = ipaddress.ip_address(host.split("%")[0])
    except ValueError:
        return False
    if getattr(ip, "ipv4_mapped", None):
        ip = ip.ipv4_mapped
    return ip.is_loopback or ip.is_private or any(ip in n for n in TAILNET if n.version == ip.version)


def our_host(host_or_url):
    """A Host or an Origin that is this machine's kind of name -- an address, localhost, .local, .ts.net or a bare name
    -- as the companion's server checks (ourHost): a look-alike name pointed here (DNS rebinding) is refused, and so is
    another site's page asking a tester's browser to post a save or drive the companion."""
    name = (host_or_url or "").strip().lower()
    if not name:
        return True
    if name == "null":
        return False
    try:
        name = urllib.parse.urlsplit(name if "://" in name else "http://" + name).hostname or ""
    except ValueError:
        return False
    if not name:
        return False
    if re.fullmatch(r"[0-9.]+", name) or ":" in name:
        return True
    return name == "localhost" or name.endswith(".local") or name.endswith(".ts.net") or "." not in name


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


def save_path(base):
    return os.path.join(DATA, "saves", base + ".sav")


def save_info(base):
    p = save_path(base)
    if not os.path.isfile(p):
        return {"sha1": None}
    data = open(p, "rb").read()
    return {"sha1": hashlib.sha1(data).hexdigest(), "size": len(data), "at": int(os.path.getmtime(p) * 1000)}


def find_node():
    """Node for the companion's server: its .nvmrc's (24), else 22.13 or later (node:sqlite unflagged), as bindCompanion.sh
    finds it -- the PATH's first, then Homebrew's node@24, then the hub's /opt/node22."""
    want = (open(os.path.join(COMPANION, ".nvmrc")).read().strip().lstrip("v") if os.path.isfile(os.path.join(COMPANION, ".nvmrc")) else "24")
    found = []
    for node in [shutil.which("node"), f"/opt/homebrew/opt/node@{want}/bin/node", f"/usr/local/opt/node@{want}/bin/node",
                 "/opt/node22/bin/node"]:
        if not node or not os.path.isfile(node):
            continue
        try:
            v = subprocess.run([node, "-v"], capture_output=True, text=True, timeout=5).stdout.strip().lstrip("v")
            major, minor = (int(x) for x in v.split(".")[:2])
        except Exception:
            continue
        if str(major) == want:
            return node
        if (major, minor) >= (22, 13):
            found.append(node)
    return found[0] if found else None


class CompanionDown(Exception):
    pass


class Companions:
    """The playground's own companions: daemons-companion's server, one for each build, each on its own port with its own
    database (data/companions/<build>/) and the browser's save of that build (data/saves/) -- started the first time its
    build asks for one, and stopped with this server. One left running by an earlier run is used again if it is ours."""

    def __init__(self, first_port, enabled):
        self.ports = {b: first_port + i for i, b in enumerate(BUILDS)}
        self.enabled, self.procs, self.lock = enabled, {}, threading.Lock()
        self.locks = {b: threading.Lock() for b in BUILDS}
        self.node = find_node() if enabled else None

    def why_not(self):
        """Why the playground cannot run a companion, or None."""
        if not self.enabled:
            return "--no-companion"
        if not os.path.isfile(os.path.join(COMPANION, "server", "src", "main.ts")):
            return f"no daemons-companion at {COMPANION} (DAEMONS' setup.sh links it as DAEMONS/companion)"
        if not os.path.isdir(os.path.join(COMPANION, "server", "node_modules", "tsx")):
            return f"the companion's server has not been installed: npm install in {COMPANION}/server"
        if not self.node:
            return "no Node 24 (or 22.13 or later) for the companion's server: brew install node@24"
        return None

    def home(self, build):
        return os.path.join(DATA, "companions", build)

    def settings(self, build):
        """Its /api/settings (which names its save), or None when nothing answers on its port."""
        try:
            c = http.client.HTTPConnection("127.0.0.1", self.ports[build], timeout=2)
            c.request("GET", "/api/settings")
            r = c.getresponse()
            return json.loads(r.read()) if r.status == 200 else {}
        except (OSError, ValueError):
            return None

    def config(self, build):
        home = self.home(build)
        os.makedirs(home, exist_ok=True)
        os.makedirs(os.path.dirname(save_path(BUILDS[build])), exist_ok=True)
        cfg = {"port": self.ports[build], "host": "127.0.0.1", "database": os.path.join(home, "companion.sqlite"),
               "edition": "CONTEXT" if build.startswith("context") else "CONTENT",
               "savePath": save_path(BUILDS[build]), "artDir": os.path.join(DAEMONS, "gfx", "daemons"),
               "ai": {"enabled": False}, "talk": {"url": None}}
        path = os.path.join(home, "config.json")
        with open(path + ".tmp", "w") as f:
            json.dump(cfg, f, indent=2)
        os.replace(path + ".tmp", path)
        return path

    def port(self, build):
        """Its port, once it answers -- starting it if it is not running."""
        why = self.why_not()
        if why:
            raise CompanionDown(why)
        with self.locks[build]:
            proc, port = self.procs.get(build), self.ports[build]
            if proc and proc.poll() is None:
                return port
            now = self.settings(build)
            if now is not None:
                if now.get("savePath") == save_path(BUILDS[build]):
                    return port                                          # ours, left by an earlier run
                raise CompanionDown(f"port {port} is already another companion's; start the playground with --companion-port")
            config = self.config(build)
            with open(os.path.join(self.home(build), "server.log"), "ab") as log:
                proc = subprocess.Popen(
                    [self.node, "--disable-warning=ExperimentalWarning", "--import", "tsx", "src/main.ts"],
                    cwd=os.path.join(COMPANION, "server"), env={**os.environ, "COMPANION_CONFIG": config},
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            self.procs[build] = proc
            for _ in range(120):
                if proc.poll() is not None:
                    tail = open(os.path.join(self.home(build), "server.log"), errors="replace").read()[-600:]
                    raise CompanionDown(f"the {build} companion stopped as it started: {tail.strip()}")
                if self.settings(build) is not None:
                    print(f"playground: the {build} companion on port {port} (data/companions/{build})")
                    return port
                time.sleep(0.25)
            raise CompanionDown(f"the {build} companion did not answer in 30 s -- see data/companions/{build}/server.log")

    def stop(self, build):
        proc = self.procs.pop(build, None)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(5)
            except subprocess.TimeoutExpired:
                proc.kill()

    def reset(self, build):
        """A companion for a new game: the old one stopped, its database kept aside (the one before it let go)."""
        with self.locks[build]:
            self.stop(build)
            home = self.home(build)
            if os.path.isdir(home):
                shutil.rmtree(home + ".before", ignore_errors=True)
                os.replace(home, home + ".before")

    def stop_all(self):
        for build in list(self.procs):
            self.stop(build)


SITE_EXPORT = os.path.join(DATA, "companion-site")   # the companion's site, exported; .json beside it says from what
SITE_PREFIX = "/companion-site"
SITE_ROOTS = ("/_expo/", "/assets/")                  # what the export names from the root: this site has neither


class CompanionSite:
    """daemons-companion's app as a static site (expo export --platform web) in data/companion-site/, so the COMPANION
    tab needs no Expo dev server. Exported as this starts, and again -- in the background, the old one served meanwhile
    -- when the companion has changed since the last export: its HEAD, or anything uncommitted in what the site is built
    from (app/, and server/src and server/data, which its Metro config reads as well). An export that failed is not
    tried again until the companion changes."""

    WATCHED = ("app", "server/src", "server/data")

    def __init__(self, enabled):
        self.enabled = enabled
        self.node = find_node() if enabled else None
        self.lock, self.building, self.checked, self.failed, self.failed_for = threading.Lock(), False, 0.0, None, None

    def why_not(self):
        """Why the playground cannot export the site, or None."""
        if not self.enabled:
            return "--companion"
        app = os.path.join(COMPANION, "app")
        if not os.path.isfile(os.path.join(app, "app.json")):
            return f"no daemons-companion app at {app} (DAEMONS' setup.sh links the companion as DAEMONS/companion)"
        if not os.path.isfile(os.path.join(app, "node_modules", "expo", "bin", "cli")):
            return f"the companion's app has not been installed: npm install in {app}"
        if not self.node:
            return "no Node 24 (or 22.13 or later) for the companion's app: brew install node@24"
        return None

    def fingerprint(self):
        """{head, digest, dirty}: the companion's HEAD, and the size and time of everything uncommitted that the site is
        built from -- or None when git cannot say."""
        try:
            git = lambda *a: subprocess.run(["git", "--no-optional-locks", "-C", COMPANION, *a], capture_output=True,
                                            timeout=20, check=True).stdout
            head = git("rev-parse", "HEAD").decode().strip()
            status = git("status", "--porcelain", "-z", "--untracked-files=all", "--", *self.WATCHED)
        except (OSError, subprocess.SubprocessError):
            return None
        h, dirty, items = hashlib.sha1(head.encode()), False, iter(status.split(b"\0"))
        for item in items:
            if not item:
                continue
            dirty, path = True, item[3:].decode(errors="replace")
            if item[:1] in (b"R", b"C"):
                next(items, None)                           # a rename's old name follows it
            try:
                st = os.stat(os.path.join(COMPANION, path))
                h.update(f"{item[:2]!r} {path} {st.st_size} {st.st_mtime_ns}\n".encode())
            except OSError:
                h.update(f"{item[:2]!r} {path} gone\n".encode())
        return {"head": head, "digest": h.hexdigest(), "dirty": dirty}

    def stamp(self):
        try:
            with open(SITE_EXPORT + ".json") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def url(self):
        """The export's page, or None while there is none (or --companion names another site). One made before is
        served even when it cannot be made again -- better a companion a little behind than none."""
        if not self.enabled or not os.path.isfile(os.path.join(SITE_EXPORT, "index.html")):
            return None
        return SITE_PREFIX + "/"

    def why(self):
        """None while an export is served; otherwise why not -- "building" while the first one is made."""
        if self.url():
            return None
        if self.building:
            return "building"
        return self.why_not() or self.failed or "not exported yet"

    def ensure(self):
        """Export again, in the background, if the companion has changed since the last export (looked at once every
        30 s at most: the page asks every two minutes, and as the COMPANION tab opens)."""
        if self.why_not():
            return
        with self.lock:
            if self.building or time.time() - self.checked < 30:
                return
            self.checked = time.time()
            now = self.fingerprint()
            if self.url() and (now is None or self.stamp().get("digest") == now["digest"]):
                return                                      # as it was (or not a git checkout: the one there is kept)
            if self.failed and (now and now["digest"]) == self.failed_for:
                return                                      # failed as it is: tried again once it has changed
            self.building = True
        threading.Thread(target=self.build, args=(now,), daemon=True).start()

    def build(self, now):
        head = now["head"] if now else ""
        nxt, started = SITE_EXPORT + ".next", time.time()
        shutil.rmtree(nxt, ignore_errors=True)
        # the site as bindCompanion.sh's own: its default server (127.0.0.1:4730; ?server= names the playground's) and
        # no BUILD, which is the phone's -- whatever this shell was given for the app is not passed on
        env = {k: v for k, v in os.environ.items() if k not in ("EXPO_PUBLIC_DAEMONS_SERVER", "EXPO_PUBLIC_BUILD")}
        env.update(CI="1", EXPO_NO_TELEMETRY="1", PATH=os.path.dirname(self.node) + os.pathsep + env.get("PATH", ""))
        print(f"playground: exporting the companion's site ({head[:7] or 'not a git checkout'}"
              f"{', with what is uncommitted' if now and now['dirty'] else ''}) -- data/companion-site.log")
        try:
            with open(SITE_EXPORT + ".log", "wb") as log:
                r = subprocess.run([self.node, os.path.join("node_modules", "expo", "bin", "cli"), "export",
                                    "--platform", "web", "--output-dir", nxt], cwd=os.path.join(COMPANION, "app"),
                                   env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, timeout=900)
            ok = r.returncode == 0 and os.path.isfile(os.path.join(nxt, "index.html"))
        except (OSError, subprocess.SubprocessError):
            ok = False
        if ok:
            old = SITE_EXPORT + ".old"
            shutil.rmtree(old, ignore_errors=True)
            if os.path.isdir(SITE_EXPORT):
                os.replace(SITE_EXPORT, old)
            os.replace(nxt, SITE_EXPORT)
            shutil.rmtree(old, ignore_errors=True)
            with open(SITE_EXPORT + ".json.tmp", "w") as f:
                json.dump({**(now or {}), "at": time.strftime("%Y-%m-%d %H:%M:%S")}, f, indent=2)
            os.replace(SITE_EXPORT + ".json.tmp", SITE_EXPORT + ".json")
            self.failed = self.failed_for = None
            print(f"playground: the companion's site exported in {time.time() - started:.0f} s: {SITE_PREFIX}/")
        else:
            shutil.rmtree(nxt, ignore_errors=True)
            self.failed, self.failed_for = "the export failed -- see data/companion-site.log", now and now["digest"]
            kept = "the last export is served still" if self.url() else "the COMPANION tab falls back to port 8081"
            print(f"playground: {self.failed}; {kept}")
        self.building = False


# What only the Mac may do, which the companion's server allows any request from this machine -- and through this proxy
# every request is from this machine. So they are refused here: pairing a phone, the network, the Mac's dialogs and
# Finder, the relay's secret, Home Assistant, the AI's door, and the save's path (the playground's, not a tester's).
NOT_THROUGH = {"/api/pair", "/api/pair/code", "/api/pair/phones", "/api/pair/forget", "/api/settings/network",
               "/api/settings/pick", "/api/settings/reveal", "/api/settings/relay", "/api/settings/home"}


class Handler(http.server.SimpleHTTPRequestHandler):
    build, base, companion, companions, site = False, RELEASES, None, None, None
    status = None

    def __init__(self, *a, **k):
        super().__init__(*a, directory=SITE, **k)

    def log_message(self, fmt, *args):
        sys.stderr.write("playground: %s %s\n" % (self.client_address[0], fmt % args))

    def send_response(self, code, message=None):
        self.status = code
        super().send_response(code, message)

    def end_headers(self):
        # the export's bundle and assets are named for what is in them, so a phone fetches each once; the rest is asked
        # again every time (the companion's page names a new bundle after each export)
        named = urllib.parse.urlsplit(self.path).path.startswith(("/_expo/static/", "/assets/"))
        self.send_header("Cache-Control", "max-age=31536000, immutable" if named and self.status in (200, 304)
                         else "no-cache")
        super().end_headers()

    def translate_path(self, path):
        # the companion's site, exported: its page at /companion-site/, and what it names from the root (SITE_ROOTS)
        p = urllib.parse.urlsplit(path).path
        strip = len(SITE_PREFIX) if p == SITE_PREFIX or p.startswith(SITE_PREFIX + "/") else 0 if p.startswith(SITE_ROOTS) else None
        if strip is None:
            return super().translate_path(path)
        self.directory = SITE_EXPORT
        try:
            return super().translate_path(path[strip:] or "/")
        finally:
            self.directory = SITE

    def list_directory(self, path):
        self.send_error(404)                            # a folder of the site's or the export's is not a page
        return None

    def json(self, value, head=False, status=200):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")       # the companion's site reads its errors from another port
        self.end_headers()
        if not head:
            self.wfile.write(body)

    def refused(self):
        """Anything not from this machine's network, or naming a host or a page that is not this machine's."""
        if not allowed(self.client_address[0]):
            self.send_error(403, "this page is for this machine's network only")
        elif not our_host(self.headers.get("Host", "")):
            self.send_error(403, "not an address of this playground's")
        elif self.command not in ("GET", "HEAD") and not our_host(self.headers.get("Origin", "")):
            self.send_error(403, "not from a page of this playground's")
        else:
            return False
        return True

    def do_HEAD(self):
        self.do_GET(head=True)

    def do_OPTIONS(self):
        # the companion's site (another port: another origin) asks before it POSTs JSON to /companion/
        if self.refused():
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST")
        self.send_header("Access-Control-Allow-Headers", "content-type, authorization")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        if self.refused():
            return
        path = urllib.parse.urlparse(self.path).path
        m = re.match(r"^/save/(daemonsCont(?:ent|ext)(?:_debug)?)\.sav$", path)
        if m:
            return self.put_save(m[1])
        m = re.match(r"^/companion-reset/([a-z_]+)$", path)
        if m and m[1] in BUILDS and self.companions:
            self.companions.reset(m[1])
            return self.json({"reset": m[1]})
        if path.startswith("/companion/"):
            return self.proxy()
        self.send_error(404)

    def put_save(self, base):
        """The browser's save of a build, for its companion to read: written whole, or with no body, put aside (a new
        game, not saved yet -- the companion must not go on reading the game before it)."""
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > SAVE_MOST:
            return self.json({"error": "a save is 128 KB"}, status=413)
        data = self.rfile.read(n) if n else b""
        p = save_path(base)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if not data:
            if os.path.isfile(p):
                os.replace(p, os.path.join(os.path.dirname(p), base + ".before-new-game.sav"))
        else:
            with open(p + ".playground-writing", "wb") as f:
                f.write(data)
            os.replace(p + ".playground-writing", p)
        return self.json(save_info(base))

    def proxy(self, head=False):
        """/companion/<build>/<path> -> that build's companion, on this machine. To the companion every request through
        here is this machine's, so what only the Mac may do is refused here (NOT_THROUGH)."""
        m = re.match(r"^/companion/([a-z_]+)(/[^?#]*)?(\?.*)?$", self.path)
        if not m or m[1] not in BUILDS or not self.companions:
            return self.json({"error": "no such companion here"}, head, 404)
        build, sub, query = m[1], m[2] or "/", m[3] or ""
        if sub in NOT_THROUGH or sub.startswith("/ollama") or (self.command == "POST" and sub == "/api/settings"):
            return self.json({"error": "the playground's companion does not do that -- it is done on the companion's own "
                                       "site, on the Mac"}, head, 403)
        try:
            port = self.companions.port(build)
        except CompanionDown as e:
            return self.json({"error": f"the playground's companion is not running: {e}"}, head, 503)
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > 8 * 1024 * 1024:
            return self.json({"error": "too big"}, head, 413)
        body = self.rfile.read(n) if n else None
        headers = {k: self.headers[k] for k in ("Content-Type", "Accept", "Origin") if self.headers.get(k)}
        try:
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=120)
            c.request(self.command, sub + query, body=body, headers=headers)
            r = c.getresponse()
            data = r.read()
        except OSError as e:
            return self.json({"error": f"the playground's companion did not answer: {e}"}, head, 502)
        self.send_response(r.status)
        for k in ("Content-Type", "Access-Control-Allow-Origin", "Access-Control-Allow-Methods",
                  "Access-Control-Allow-Headers"):
            if r.getheader(k):
                self.send_header(k, r.getheader(k))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if not head:
            self.wfile.write(data)

    def do_GET(self, head=False):
        if self.refused():
            return
        path = urllib.parse.urlparse(self.path).path
        if path == "/info.json":
            roms, label = find_roms(self.build, self.base)
            why = self.companions.why_not() if self.companions else "--no-companion"
            if self.site:
                self.site.ensure()                      # made again if the companion has changed since
            return self.json({"release": label, "editions": sorted(roms), "companion": self.companion,
                              "companions": why is None, "companionsWhy": why,
                              "companionSite": self.site and self.site.url(),
                              "companionSiteWhy": self.site.why() if self.site else "--companion"}, head)
        if path.startswith("/companion/"):
            return self.proxy(head)
        m = re.match(r"^/save/(daemonsCont(?:ent|ext)(?:_debug)?)\.(sav|json)$", path)
        if m:
            if m[2] == "json":
                return self.json(save_info(m[1]), head)
            p = save_path(m[1])
            if not os.path.isfile(p):
                return self.json({"error": "no save of that build here yet"}, head, 404)
            data = open(p, "rb").read()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if not head:
                self.wfile.write(data)
            return
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
    ap.add_argument("--companion", help="the COMPANION tab's site (default: the playground's own export of it, made "
                                        "from DAEMONS/companion/app; the page's own host, port 8081, when there is none)")
    ap.add_argument("--releases", default=RELEASES, help="where the releases are (default: ../DAEMONS/ROM RELEASE)")
    ap.add_argument("--no-companion", action="store_true",
                    help="run no companion of the playground's own: the COMPANION tab shows its site's own server")
    ap.add_argument("--companion-port", type=int, default=4731,
                    help="the first of the four companions' ports (CONTENT, CONTEXT, then their DEBUG builds; default 4731)")
    a = ap.parse_args()
    roms, label = find_roms(a.build, a.releases)
    if not roms:
        where = "DAEMONS/engineGba (make -C engineGba firered ...)" if a.build else a.releases + " (DAEMONS tools/romrelease.py)"
        sys.exit(f"playground: no ROMs found in {where}")
    companions = Companions(a.companion_port, not a.no_companion)
    site = CompanionSite(not a.companion)
    Handler.build, Handler.base, Handler.companion, Handler.companions = a.build, a.releases, a.companion, companions
    Handler.site = site
    sys.stdout.reconfigure(line_buffering=True)
    srv = http.server.ThreadingHTTPServer(("0.0.0.0", a.port), Handler)
    print(f"playground: {label} -- {', '.join(sorted(roms))}")
    print(f"playground: http://localhost:{a.port}/")
    name = tailnet_name()
    if name:
        print(f"playground: http://{name}:{a.port}/   (the tailnet: the phone, away from home)")
    print(f"playground: http://{local_name()}:{a.port}/   (this network)")
    why = companions.why_not()
    if why is None:
        print(f"playground: its own companions on ports {a.companion_port}-{a.companion_port + 3}, each started when a game "
              "of its build asks (data/companions/)")
    else:
        print(f"playground: no companion of its own ({why}): the COMPANION tab shows its site's own server")
    why = site.why_not()
    if a.companion:
        print(f"playground: the COMPANION tab's site: {a.companion}")
    elif why and site.url():
        print(f"playground: the COMPANION tab's site is its last export, at {SITE_PREFIX}/ -- not made again ({why})")
    elif why:
        print(f"playground: no export of the companion's site ({why}): the COMPANION tab shows this host's port 8081")
    else:
        print(f"playground: the COMPANION tab's site is its own export, at {SITE_PREFIX}/ (data/companion-site/), made "
              "again whenever daemons-companion has changed")
        site.ensure()
    print("playground: answering this machine, private addresses and the tailnet only. Ctrl-C stops it.")
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        companions.stop_all()


if __name__ == "__main__":
    main()
