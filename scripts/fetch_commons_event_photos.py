from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.events_db import HISTORICAL_EVENTS


OUT_DIR = ROOT / "assets" / "event_real_photos"
MANIFEST_PATH = OUT_DIR / "manifest.json"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "EventScopeEducationalImageCollector/1.0 (local classroom project; contact: user-local)"


QUERY_OVERRIDES = {
    "9_11_2001": ["September 11 attacks World Trade Center"],
    "iraq_war_2003": ["2003 invasion of Iraq"],
    "brexit_2016": ["Brexit referendum"],
    "us_china_trade_war_2018": ["China United States trade war tariffs"],
    "russia_ukraine_2022": ["2022 Russian invasion of Ukraine"],
    "israel_hamas_2023": ["2023 Israel Hamas war"],
    "argentina_default_2001": ["Argentine great depression bank protest"],
    "arab_spring_2011": ["Arab Spring protest"],
    "crimea_2014": ["Annexation of Crimea 2014"],
    "suez_blockage_2021": ["Ever Given Suez Canal 2021"],
    "red_sea_shipping_2024": ["Red Sea crisis 2024 shipping"],
    "taiwan_strait_tension_2022": ["2022 Taiwan military exercises"],
    "dotcom_crash_2000": ["NASDAQ dot-com bubble"],
    "lehman_2008": ["Lehman Brothers headquarters 2008"],
    "eurozone_crisis_2010": ["Greek government debt crisis protest"],
    "china_stock_crash_2015": ["Shanghai Stock Exchange stock market"],
    "covid_crash_2020": ["COVID-19 pandemic empty street stock exchange"],
    "svb_collapse_2023": ["Silicon Valley Bank collapse"],
    "flash_crash_2010": ["New York Stock Exchange trading floor"],
    "asian_financial_crisis_1997": ["Asian financial crisis Thailand baht"],
    "russian_default_1998": ["1998 Russian financial crisis"],
    "turkey_lira_2018": ["Turkish lira currency"],
    "uk_gilt_crisis_2022": ["Bank of England London"],
    "credit_suisse_2023": ["Credit Suisse headquarters Zurich"],
    "mexico_tequila_1994": ["Mexican peso crisis"],
    "fed_qe1_2008": ["Federal Reserve building Washington DC"],
    "taper_tantrum_2013": ["Federal Reserve Ben Bernanke 2013"],
    "fed_hike_cycle_2022": ["Federal Reserve Jerome Powell 2022"],
    "fed_hike_jun_2022": ["Federal Reserve building Eccles"],
    "ecb_negative_rates_2014": ["European Central Bank Frankfurt"],
    "boj_ycc_abandon_2024": ["Bank of Japan Tokyo"],
    "fed_pivot_2024": ["Federal Reserve Board building"],
    "snb_franc_shock_2015": ["Swiss National Bank building"],
    "pboc_devaluation_2015": ["People's Bank of China building"],
    "rbi_covid_cuts_2020": ["Reserve Bank of India Mumbai"],
    "boj_negative_rates_2016": ["Bank of Japan headquarters"],
    "boc_property_support_2023": ["People's Bank of China Beijing"],
    "ecb_qe_2015": ["European Central Bank headquarters"],
    "oil_crisis_2008": ["oil pumpjack crude oil"],
    "oil_negative_2020": ["Cushing Oklahoma oil storage tanks"],
    "opec_cut_2022": ["OPEC headquarters Vienna"],
    "gold_record_2020": ["gold bars"],
    "wheat_crisis_2022": ["wheat field Ukraine grain"],
    "nickel_short_squeeze_2022": ["nickel metal LME"],
    "lng_europe_2022": ["LNG tanker Europe"],
    "cocoa_record_2024": ["cocoa beans Ghana"],
    "uranium_rally_2023": ["uranium ore"],
    "india_rice_ban_2023": ["rice market India"],
    "copper_rally_2021": ["copper cathodes"],
    "bitcoin_crash_2018": ["Bitcoin cryptocurrency"],
    "ftx_collapse_2022": ["FTX logo arena"],
    "chatgpt_launch_2022": ["OpenAI San Francisco office"],
    "nvidia_earnings_2023": ["Nvidia headquarters Santa Clara"],
    "deepseek_shock_2025": ["artificial intelligence data center"],
    "google_deepmind_2016": ["Lee Sedol AlphaGo"],
    "cambridge_analytica_2018": ["Cambridge Analytica Facebook"],
    "tsmc_capex_boom_2021": ["TSMC Fab"],
    "meta_crash_2022": ["Meta headquarters Menlo Park"],
    "eu_ai_act_2024": ["European Parliament hemicycle"],
    "crowdstrike_outage_2024": ["airport blue screen outage"],
    "japan_earthquake_2011": ["2011 Tohoku earthquake tsunami"],
    "hurricane_katrina_2005": ["Hurricane Katrina New Orleans flooding"],
    "covid_who_pandemic_2020": ["World Health Organization headquarters COVID-19"],
    "taiwan_earthquake_2024": ["2024 Hualien earthquake"],
    "indian_ocean_tsunami_2004": ["2004 Indian Ocean tsunami"],
    "iceland_ash_2010": ["Eyjafjallajokull eruption 2010"],
    "thailand_floods_2011": ["2011 Thailand floods"],
    "turkey_syria_quake_2023": ["2023 Turkey Syria earthquake"],
    "panama_drought_2023": ["Panama Canal drought"],
    "australia_bushfires_2020": ["2019 2020 Australian bushfires"],
    "taiwan_921_quake_1999": ["1999 Jiji earthquake Taiwan"],
    "taiwan_sars_2003": ["Taiwan SARS 2003 hospital"],
    "morakot_2009": ["Typhoon Morakot Taiwan"],
    "sunflower_movement_2014": ["Sunflower Movement Taiwan"],
    "taiwan_chip_drought_2021": ["Taiwan drought 2021 reservoir"],
    "taiwan_cb_hike_2022": ["Central Bank of the Republic of China Taiwan"],
    "taiwan_power_grid_2022": ["Taiwan power outage Taipower"],
    "taiwan_election_2024": ["2024 Taiwan presidential election"],
    "tsmc_arizona_delay_2023": ["TSMC Arizona fab"],
    "taiwan_property_credit_2023": ["Taipei residential buildings"],
    "taiwan_election_2016": ["2016 Taiwan presidential election"],
    "china_tour_ban_2019": ["Chinese tourists Taiwan"],
    "taiwan_covid_wave_2021": ["Taiwan COVID-19 level 3 alert"],
    "auto_chip_shortage_2021": ["automotive semiconductor shortage"],
    "pelosi_taiwan_visit_2022": ["Nancy Pelosi Taiwan 2022"],
    "taiwan_ai_server_boom_2024": ["AI server factory Taiwan"],
}


def slugify_filename(name: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_")
    return stem[:120] or "image"


def request_json(params: dict, timeout: float) -> dict:
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(
        COMMONS_API,
        data=data,
        headers={"User-Agent": USER_AGENT},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_commons(query: str, limit: int, timeout: float) -> list[dict]:
    payload = request_json(
        {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrnamespace": 6,
            "gsrsearch": query,
            "gsrlimit": limit,
            "prop": "imageinfo",
            "iiprop": "url|mime|size|extmetadata",
            "iiurlwidth": 1400,
        },
        timeout=timeout,
    )
    pages = payload.get("query", {}).get("pages", {})
    results = []
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        if not info:
            continue
        mime = info.get("mime", "")
        if not mime.startswith("image/") or mime == "image/svg+xml":
            continue
        if info.get("width", 0) < 500 or info.get("height", 0) < 350:
            continue
        results.append({"title": page.get("title", ""), "imageinfo": info})
    return sorted(results, key=score_candidate, reverse=True)


def score_candidate(candidate: dict) -> int:
    title = candidate["title"].lower()
    info = candidate["imageinfo"]
    score = min(info.get("width", 0), 3000) + min(info.get("height", 0), 2000)
    good_words = ["photo", "photograph", "building", "crisis", "earthquake", "flood", "protest", "headquarters"]
    bad_words = ["map", "diagram", "chart", "graph", "logo", "seal", "icon", "svg", "poster"]
    score += sum(350 for word in good_words if word in title)
    score -= sum(900 for word in bad_words if word in title)
    return score


def event_queries(event: dict) -> list[str]:
    queries = list(QUERY_OVERRIDES.get(event["id"], []))
    if event.get("name_en"):
        queries.append(event["name_en"])
    queries.append(f"{event.get('name_en', '')} {event['date'][:4]} photograph")
    queries.append(event["name_zh"])
    return [q.strip() for q in queries if q.strip()]


def extmetadata_value(info: dict, key: str) -> str:
    return (info.get("extmetadata", {}).get(key, {}) or {}).get("value", "")


def download(url: str, path: Path, timeout: float) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        path.write_bytes(resp.read())


def verify_image(path: Path) -> tuple[int, int]:
    with Image.open(path) as img:
        img.verify()
    with Image.open(path) as img:
        return img.size


def load_manifest() -> list[dict]:
    if not MANIFEST_PATH.exists():
        return []
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.25)
    parser.add_argument("--query-timeout", type=float, default=8)
    parser.add_argument("--download-timeout", type=float, default=20)
    parser.add_argument("--search-limit", type=int, default=8)
    parser.add_argument("--missing-only", action="store_true")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    previous = {item["id"]: item for item in load_manifest() if item.get("id")}
    events = HISTORICAL_EVENTS[: args.limit] if args.limit else HISTORICAL_EVENTS
    if args.missing_only:
        events = [event for event in events if previous.get(event["id"], {}).get("status") == "missing"]
    manifest = []

    for event in events:
        out_path = OUT_DIR / f"{event['id']}.jpg"
        if out_path.exists() and not args.overwrite:
            try:
                width, height = verify_image(out_path)
                item = previous.get(event["id"], {})
                item.update(
                    {
                        "id": event["id"],
                        "name_zh": event["name_zh"],
                        "name_en": event.get("name_en", ""),
                        "date": event["date"],
                        "category": event["category"],
                        "file": str(out_path.relative_to(ROOT)),
                        "status": "existing",
                        "size": [width, height],
                    }
                )
                manifest.append(item)
                print(f"existing {event['id']}", flush=True)
                continue
            except Exception:
                out_path.unlink(missing_ok=True)

        saved = None
        errors = []
        for query in event_queries(event):
            try:
                candidates = search_commons(query, limit=args.search_limit, timeout=args.query_timeout)
            except Exception as exc:
                errors.append(f"{query}: {exc}")
                continue

            for candidate in candidates:
                info = candidate["imageinfo"]
                url = info.get("thumburl") or info.get("url")
                if not url:
                    continue
                temp_path = OUT_DIR / f".{event['id']}.download"
                try:
                    download(url, temp_path, timeout=args.download_timeout)
                    width, height = verify_image(temp_path)
                    temp_path.replace(out_path)
                    page_title = candidate["title"].replace("File:", "")
                    saved = {
                        "id": event["id"],
                        "name_zh": event["name_zh"],
                        "name_en": event.get("name_en", ""),
                        "date": event["date"],
                        "category": event["category"],
                        "file": str(out_path.relative_to(ROOT)),
                        "source_page": "https://commons.wikimedia.org/wiki/File:"
                        + urllib.parse.quote(page_title.replace(" ", "_")),
                        "commons_title": candidate["title"],
                        "license": extmetadata_value(info, "LicenseShortName")
                        or extmetadata_value(info, "UsageTerms"),
                        "artist": extmetadata_value(info, "Artist"),
                        "credit": extmetadata_value(info, "Credit"),
                        "description": extmetadata_value(info, "ImageDescription"),
                        "query": query,
                        "status": "downloaded",
                        "size": [width, height],
                    }
                    break
                except Exception as exc:
                    errors.append(f"{candidate['title']}: {exc}")
                    temp_path.unlink(missing_ok=True)
            if saved:
                break
            time.sleep(args.sleep)

        if saved:
            manifest.append(saved)
            print(f"downloaded {event['id']}", flush=True)
        else:
            manifest.append(
                {
                    "id": event["id"],
                    "name_zh": event["name_zh"],
                    "name_en": event.get("name_en", ""),
                    "date": event["date"],
                    "category": event["category"],
                    "status": "missing",
                    "queries": event_queries(event),
                    "errors": errors[-5:],
                }
            )
            print(f"missing {event['id']}", flush=True)

    if args.limit or args.missing_only:
        handled_ids = {item.get("id") for item in manifest}
        for event in HISTORICAL_EVENTS:
            if event["id"] in handled_ids:
                continue
            if event["id"] in previous:
                manifest.append(previous[event["id"]])

    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    total = len(manifest)
    done = sum(1 for item in manifest if item.get("status") in {"downloaded", "existing"})
    print(f"done images={done}/{total} manifest={MANIFEST_PATH}", flush=True)


if __name__ == "__main__":
    main()
