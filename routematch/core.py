"""把请求匹配到路由模板。"""

from urllib.parse import unquote

LITERAL, PARAM, WILD = 2, 1, 0


class Counter:
    """记录比较次数。"""

    def __init__(self):
        self.scanned = 0


def segments(path):
    # 先按 / 分段、丢掉空段，再逐段解码：%2F 不会产生新分段。
    return [unquote(part) for part in path.split("/") if part != ""]


def _route_methods(route):
    methods = route.get("methods")
    if methods is not None:
        return list(methods)
    if "method" in route:
        return [route["method"]]
    return []


def _classify(seg):
    if seg.startswith("{") and seg.endswith("}"):
        inner = seg[1:-1]
        if inner.endswith("..."):
            return WILD
        return PARAM
    return LITERAL


def _host_match(template, host):
    if not template or template == "*":
        return True
    if template.startswith("*."):
        suffix = template[1:]
        return len(host) > len(suffix) and host.endswith(suffix)
    return template == host


def _better(candidate, best):
    """逐段从左到右比较，第一个不同的段决定胜负。"""
    for a, b in zip(candidate, best):
        if a != b:
            return a > b
    return False


class Router:
    def __init__(self, routes):
        # 覆盖：方法集合与路径模板相同的重复注册，后者覆盖前者。
        deduped = {}
        order = []
        for route in routes:
            key = (frozenset(_route_methods(route)), route["path"])
            if key not in deduped:
                order.append(key)
            deduped[key] = route

        entries = []
        for key in order:
            route = deduped[key]
            tpl = [part for part in route["path"].split("/") if part != ""]
            kinds = [_classify(seg) for seg in tpl]
            wild = bool(tpl) and kinds[-1] == WILD
            entries.append({
                "route": route,
                "tpl": tpl,
                "kinds": kinds,
                "wild": wild,
            })

        # 按方法集合与首段字面建索引：lit / param / wild 三个桶。
        self._lit = {}
        self._param = {}
        self._wild = {}
        for entry in entries:
            methods = _route_methods(entry["route"])
            first = entry["tpl"][0] if entry["tpl"] else ""
            first_kind = entry["kinds"][0] if entry["tpl"] else LITERAL
            for method in methods:
                if first_kind == LITERAL:
                    self._lit.setdefault(method, {}).setdefault(first, []).append(entry)
                elif first_kind == PARAM:
                    self._param.setdefault(method, []).append(entry)
                else:
                    self._wild.setdefault(method, []).append(entry)

    def _match_path(self, entry, segs):
        tpl, kinds, wild = entry["tpl"], entry["kinds"], entry["wild"]
        if wild:
            if len(segs) < len(tpl):
                return None
        elif len(segs) != len(tpl):
            return None
        aligned = []
        for i, seg in enumerate(segs):
            if wild and i >= len(tpl) - 1:
                kind, literal = WILD, None
            else:
                kind, literal = kinds[i], tpl[i]
            if kind == LITERAL and seg != literal:
                return None
            aligned.append(kind)
        return aligned

    def match(self, method, host, path, counter):
        segs = segments(path)
        first = segs[0] if segs else ""
        buckets = [
            self._lit.get(method, {}).get(first, []),
            self._param.get(method, []),
            self._wild.get(method, []),
        ]
        best_name = ""
        best_kinds = None
        for bucket in buckets:
            for entry in bucket:
                counter.scanned += 1
                if not _host_match(entry["route"].get("host", ""), host):
                    continue
                aligned = self._match_path(entry, segs)
                if aligned is None:
                    continue
                if best_kinds is None or _better(aligned, best_kinds):
                    best_kinds = aligned
                    best_name = entry["route"]["name"]
        return best_name
