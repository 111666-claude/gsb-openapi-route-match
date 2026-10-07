"""把请求匹配到路由模板。"""

from urllib.parse import unquote


class Counter:
    """记录比较次数。"""

    def __init__(self):
        self.scanned = 0


def segments(path):
    return [part for part in unquote(path).split("/") if part != ""]


def _is_param(seg):
    return seg.startswith("{") and seg.endswith("}")


class Router:
    def __init__(self, routes):
        self.routes = routes

    def match(self, method, host, path, counter):
        segs = segments(path)
        best = ""
        best_score = -1
        for route in self.routes:
            counter.scanned += 1
            if route.get("method", "") != method:
                continue
            route_host = route.get("host", "")
            if route_host and route_host != host:
                continue
            rsegs = [part for part in route["path"].split("/") if part != ""]
            if len(rsegs) != len(segs):
                continue
            hit = True
            score = 0
            for i, tmpl in enumerate(rsegs):
                if _is_param(tmpl):
                    continue
                score += 1
                if tmpl != segs[i]:
                    hit = False
                    break
            if hit and score > best_score:
                best_score = score
                best = route["name"]
        return best
