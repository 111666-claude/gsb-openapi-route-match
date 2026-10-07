"""固定场景，用来复现题面里的锚点。"""

import json

from . import core


def _line(obj):
    print(json.dumps(obj, ensure_ascii=False))


def route(name, path, method="GET", host=""):
    return {"name": name, "path": path, "method": method, "host": host}


def run(name):
    if name == "priority":
        router = core.Router([route("P", "/a/{x}/c"), route("Q", "/a/b/{y}")])
        _line({"hit": router.match("GET", "", "/a/b/c", core.Counter())})
        return 0
    if name == "host":
        router = core.Router([route("H", "/a", host="*.example.com")])
        _line({"hit": router.match("GET", "x.example.com", "/a", core.Counter())})
        return 0
    if name == "decode":
        router = core.Router([route("D", "/a/{x}"), route("D2", "/a/{x}/{y}")])
        _line({"hit": router.match("GET", "", "/a/p%2Fq", core.Counter())})
        return 0
    if name == "methods":
        router = core.Router([{"name": "M", "path": "/a", "methods": ["GET", "POST"]}])
        _line({"hit": router.match("POST", "", "/a", core.Counter())})
        return 0
    if name == "overlay":
        router = core.Router([route("old", "/a"), route("new", "/a")])
        _line({"hit": router.match("GET", "", "/a", core.Counter())})
        return 0
    if name == "work":
        routes = [route("h%04d" % i, "/r%04d" % i) for i in range(800)]
        router = core.Router(routes)
        counter = core.Counter()
        for i in range(800):
            router.match("GET", "", "/r%04d" % i, counter)
        _line({"routes": 800, "scanned": counter.scanned})
        return 0
    raise SystemExit("未知场景：" + name)
