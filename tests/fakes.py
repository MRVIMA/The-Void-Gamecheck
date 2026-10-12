"""Fake responses for every source: tests never contact the real sites."""

import httpx

GAMES = {
    100: {"name": "Native Quest", "linux": True, "tier": "gold", "deck": 3},
    200: {"name": "Proton Saga", "linux": False, "tier": "platinum", "deck": 3},
    300: {"name": "Rough Edges", "linux": False, "tier": "bronze", "deck": 1},
    400: {"name": "Deck Only", "linux": False, "tier": None, "deck": 2},
    500: {"name": "Mystery Game", "linux": False, "tier": None, "deck": 0},
}


def handler(calls):
    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        path, q = request.url.path, request.url.params
        if path == "/api/storesearch/":
            term = q["term"].lower()
            items = [{"type": "app", "id": i, "name": g["name"],
                      "platforms": {"windows": True, "mac": False, "linux": g["linux"]}}
                     for i, g in GAMES.items() if term in g["name"].lower()]
            return httpx.Response(200, json={"total": len(items), "items": items})
        if path == "/api/appdetails":
            i = int(q["appids"])
            g = GAMES.get(i)
            if g is None:
                return httpx.Response(200, json={str(i): {"success": False}})
            return httpx.Response(200, json={str(i): {"success": True, "data": {
                "name": g["name"], "type": "game",
                "platforms": {"windows": True, "linux": g["linux"]},
                "linux_requirements": {"minimum": "<strong>OS:</strong> Ubuntu 22.04<br>"}
                if g["linux"] else []}}})
        if path.startswith("/api/v1/reports/summaries/"):
            i = int(path.rsplit("/", 1)[1].split(".")[0])
            tier = GAMES.get(i, {}).get("tier")
            if tier is None:
                return httpx.Response(404)
            return httpx.Response(200, json={"tier": tier, "trendingTier": tier,
                                             "confidence": "good", "total": 42, "score": 0.7})
        if path == "/saleaction/ajaxgetdeckappcompatibilityreport":
            i = int(q["nAppID"])
            return httpx.Response(200, json={"success": 1, "results": {
                "appid": i, "resolved_category": GAMES.get(i, {}).get("deck", 0)}})
        if path == "/api/games":
            name = q["search"].lower()
            res = [{"name": g["name"], "slug": g["name"].lower().replace(" ", "-"),
                    "steamid": i} for i, g in GAMES.items() if g["name"].lower() == name
                   and i in (100, 200)]
            return httpx.Response(200, json={"count": len(res), "results": res})
        if path.startswith("/api/games/"):
            slug = path.rsplit("/", 1)[1]
            return httpx.Response(200, json={"name": slug, "slug": slug, "installers": [
                {"runner": "steam", "version": "Proton"}, {"runner": "wine", "version": "GOG"}]})
        return httpx.Response(404)
    return respond
