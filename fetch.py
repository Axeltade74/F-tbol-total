#!/usr/bin/env python3
"""FÚTBOL TOTAL · actualizador automático. Solo librería estándar.
Genera docs/data.json con resultados (API-Football), noticias (Google News RSS) y fotos libres (Wikipedia/Commons)."""
import json, os, sys, re, datetime as dt, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs", "data.json")
PHOTOS = os.path.join(ROOT, "docs", "photos.json")
UA = {"User-Agent": "FutbolTotal/1.0 (periodismo deportivo)"}

PLAYERS = [("Lionel Messi", "Lionel_Messi"), ("Cristiano Ronaldo", "Cristiano_Ronaldo"),
  ("Kylian Mbappé", "Kylian_Mbappé"), ("Neymar Jr.", "Neymar"), ("Lamine Yamal", "Lamine_Yamal"),
  ("Erling Haaland", "Erling_Haaland"), ("Julián Álvarez", "Julián_Álvarez"),
  ("Vinícius Júnior", "Vinícius_Júnior"), ("Mohamed Salah", "Mohamed_Salah"),
  ("Lautaro Martínez", "Lautaro_Martínez")]

FEEDS = {  # categoría -> consulta de Google News
  "Fútbol argentino": "fútbol argentino Liga Profesional",
  "Fútbol internacional": "fútbol internacional",
  "Champions League": "Champions League",
  "Copa Libertadores": "Copa Libertadores",
  "Selecciones nacionales": "selección argentina fútbol",
  "Mercado de pases": "mercado de pases fútbol fichajes",
  "Entrevistas y análisis": "fútbol entrevista análisis",
}
LEAGUES = {2: "Champions League", 13: "Copa Libertadores", 128: "Fútbol argentino", 39: "Premier League",
  140: "LaLiga", 135: "Serie A", 78: "Bundesliga", 61: "Ligue 1", 1: "Mundial", 11: "Copa Sudamericana"}

def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def parse_rss(xml_bytes, cat, limit=8):
    out = []
    for it in ET.fromstring(xml_bytes).iter("item"):
        title = (it.findtext("title") or "").strip()
        src = (it.findtext("source") or "").strip()
        if src and title.endswith(" - " + src):
            title = title[: -len(" - " + src)]
        try: ts = int(parsedate_to_datetime(it.findtext("pubDate")).timestamp() * 1000)
        except Exception: ts = 0
        link = (it.findtext("link") or "").strip()
        if title and link.startswith("https://"):
            out.append({"t": title, "src": src or "Fuente", "url": link, "c": cat, "ts": ts})
        if len(out) >= limit: break
    return out

def news():
    items = []
    for cat, q in FEEDS.items():
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
            {"q": q + " when:2d", "hl": "es-419", "gl": "AR", "ceid": "AR:es-419"})
        try: items += parse_rss(get(url), cat)
        except Exception as e: print("RSS falló", cat, e, file=sys.stderr)
    seen, uniq = set(), []
    for n in sorted(items, key=lambda n: -n["ts"]):
        k = re.sub(r"\W+", "", n["t"].lower())[:60]
        if k not in seen: seen.add(k); uniq.append(n)
    return uniq[:60]

def matches():
    key = os.environ.get("API_FOOTBALL_KEY")
    if not key: print("Sin API_FOOTBALL_KEY: se omiten resultados", file=sys.stderr); return []
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    data = json.loads(get("https://v3.football.api-sports.io/fixtures?date=" + today,
                          {"x-apisports-key": key, **UA}))
    out = []
    for f in data.get("response", []):
        if f["league"]["id"] not in LEAGUES: continue
        st = f["fixture"]["status"]
        live = st["short"] in ("1H", "2H", "HT", "ET", "BT", "P", "LIVE")
        done = st["short"] in ("FT", "AET", "PEN")
        out.append({"id": f["fixture"]["id"], "lg": LEAGUES[f["league"]["id"]],
          "a": f["teams"]["home"]["name"], "b": f["teams"]["away"]["name"],
          "sa": f["goals"]["home"], "sb": f["goals"]["away"],
          "st": "live" if live else "fin" if done else "prox",
          "min": (str(st.get("elapsed") or "") + "’") if live else "FIN" if done else "",
          "ts": int(f["fixture"]["timestamp"]) * 1000})
    return sorted(out, key=lambda m: ({"live": 0, "prox": 1, "fin": 2}[m["st"]], m["ts"]))

def photos():
    cache = json.load(open(PHOTOS, encoding="utf-8")) if os.path.exists(PHOTOS) else {}
    for name, title in PLAYERS:
        if name in cache: continue
        try:
            q = urllib.parse.urlencode({"action": "query", "format": "json", "titles": title,
                "prop": "pageimages", "piprop": "name|thumbnail", "pithumbsize": 600, "redirects": 1})
            pg = next(iter(json.loads(get("https://es.wikipedia.org/w/api.php?" + q))["query"]["pages"].values()))
            fn, th = pg.get("pageimage"), pg.get("thumbnail", {}).get("source")
            if not fn or not th: continue
            q2 = urllib.parse.urlencode({"action": "query", "format": "json", "titles": "File:" + fn,
                "prop": "imageinfo", "iiprop": "extmetadata"})
            ii = next(iter(json.loads(get("https://commons.wikimedia.org/w/api.php?" + q2))["query"]["pages"].values()))
            md = ii.get("imageinfo", [{}])[0].get("extmetadata", {})
            lic = md.get("LicenseShortName", {}).get("value", "")
            if not lic or "fair" in lic.lower(): continue  # solo licencias libres
            art = re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "Wikimedia Commons"))[:80]
            cache[name] = {"img": th, "credit": art, "license": lic,
                           "page": "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(fn)}
        except Exception as e: print("Foto falló", name, e, file=sys.stderr)
    json.dump(cache, open(PHOTOS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return cache

def demo():
    now = int(dt.datetime.now().timestamp() * 1000)
    return {"news": [{"t": "Titular de prueba %d" % i, "src": "Demo", "url": "https://example.com", "c": c, "ts": now - i * 600000}
            for i, c in enumerate(list(FEEDS) * 2)],
            "matches": [{"id": 1, "lg": "Champions League", "a": "Equipo A", "b": "Equipo B", "sa": 1, "sb": 0, "st": "live", "min": "67’", "ts": now}],
            "photos": {}}

if __name__ == "__main__":
    d = demo() if "--demo" in sys.argv else {"news": news(), "matches": matches(), "photos": photos()}
    d["updated"] = int(dt.datetime.now().timestamp() * 1000)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(d, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print("OK:", len(d["news"]), "noticias,", len(d["matches"]), "partidos,", len(d["photos"]), "fotos")
