"""Minimal Onshape REST client with on-disk GET caching and a call counter.

Keys come from env or ./.env (ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY).
Every real HTTP call is appended to cache/calls.log so we can track the
2500-call budget. GETs are cached by URL; pass fresh=True to bypass.
"""
import base64, hashlib, json, os, sys, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache"
BASE = "https://cad.onshape.com/api/v10"
DID = "44572ee178535fdca6908764"
MAIN_WID = "51b51d701b291c1786e1bd0e"
WID = "cc6b75fe056038bfa83c4cea"  # "cleanup" branch; all edits go here


def _load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip().removeprefix("export ").strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def _auth():
    _load_env()
    a, s = os.environ.get("ONSHAPE_ACCESS_KEY"), os.environ.get("ONSHAPE_SECRET_KEY")
    if not (a and s):
        return None
    return "Basic " + base64.b64encode(f"{a}:{s}".encode()).decode()


def calls_used():
    log = CACHE / "calls.log"
    return len(log.read_text().splitlines()) if log.exists() else 0


def request(method, path, body=None, fresh=False, accept="application/json"):
    url = path if path.startswith("http") else BASE + path
    CACHE.mkdir(exist_ok=True)
    key = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".json")
    if method == "GET" and not fresh and key.exists():
        return json.loads(key.read_text())
    headers = {"Accept": accept, "Content-Type": "application/json"}
    if (auth := _auth()):
        headers["Authorization"] = auth
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with open(CACHE / "calls.log", "a") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {method} {url}\n")
    try:
        with urllib.request.urlopen(req) as r:
            out = json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{e.code} {method} {url}: {e.read().decode()[:500]}")
    if method == "GET":
        key.write_text(json.dumps(out))
    return out


def get(path, **kw):
    return request("GET", path, **kw)


def post(path, body, **kw):
    return request("POST", path, body, **kw)


if __name__ == "__main__":
    print("auth:", "yes" if _auth() else "no", "| calls used:", calls_used())
