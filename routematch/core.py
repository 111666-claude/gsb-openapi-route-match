"""把请求匹配到路由模板。"""

from urllib.parse import unquote

_LITERAL = 2
_PARAM = 1
_WILDCARD = 0


class Counter:
    """记录比较次数。"""

    def __init__(self):
        self.scanned = 0


def segments(path):
    """先按 / 分段、丢掉空段，再对每段单独做百分号解码。"""
    return [unquote(part) for part in path.split("/") if part != ""]


def _is_param(seg):
    return seg.startswith("{") and seg.endswith("}")


def _is_wildcard(seg):
    return _is_param(seg) and seg[1:-1].endswith("...")


def _parse_template(path):
    raw = [part for part in path.split("/") if part != ""]
    template = []
    for i, seg in enumerate(raw):
        if _is_wildcard(seg):
            if i != len(raw) - 1:
                raise ValueError("通配段必须是模板最后一段：" + path)
            template.append((_WILDCARD, seg))
        elif _is_param(seg):
            template.append((_PARAM, seg))
        else:
            template.append((_LITERAL, seg))
    return template


def _methods_of(route):
    methods = route.get("methods")
    if methods:
        return frozenset(methods)
    method = route.get("method")
    if method:
        return frozenset([method])
    return frozenset()


def _host_matches(route_host, host):
    if not route_host or route_host == "*":
        return True
    if route_host.startswith("*."):
        suffix = route_host[1:]
        return len(host) > len(suffix) and host.endswith(suffix)
    return route_host == host


def _segments_match(template, segs):
    wildcard = bool(template) and template[-1][0] == _WILDCARD
    fixed = template[:-1] if wildcard else template
    if wildcard:
        if len(segs) < len(template):
            return False
    elif len(segs) != len(template):
        return False
    for (kind, value), seg in zip(fixed, segs):
        if kind == _LITERAL and value != seg:
            return False
    return True


class _Entry:
    def __init__(self, route, order):
        self.name = route["name"]
        self.methods = _methods_of(route)
        self.host = route.get("host", "")
        self.template = _parse_template(route["path"])
        self.rank = tuple(kind for kind, _ in self.template)
        self.order = order


class Router:
    def __init__(self, routes):
        deduped = {}
        for route in routes:
            key = (_methods_of(route), _parse_template_key(route["path"]))
            deduped[key] = route
        self._index = {}
        self._fallback = []
        for order, route in enumerate(deduped.values()):
            entry = _Entry(route, order)
            first = None
            if entry.template and entry.template[0][0] == _LITERAL:
                first = entry.template[0][1]
            if not entry.methods:
                self._fallback.append(entry)
                continue
            for method in entry.methods:
                buckets = self._index.setdefault(method, {})
                buckets.setdefault(first, []).append(entry)

    def match(self, method, host, path, counter):
        segs = segments(path)
        candidates = []
        buckets = self._index.get(method)
        if buckets:
            if segs:
                candidates.extend(buckets.get(segs[0], ()))
            candidates.extend(buckets.get(None, ()))
        candidates.extend(self._fallback)
        best = None
        best_key = None
        for entry in candidates:
            counter.scanned += 1
            if not _host_matches(entry.host, host):
                continue
            if not _segments_match(entry.template, segs):
                continue
            key = (entry.rank, -entry.order)
            if best_key is None or key > best_key:
                best_key = key
                best = entry
        return best.name if best else ""


def _parse_template_key(path):
    return tuple(part for part in path.split("/") if part != "")
