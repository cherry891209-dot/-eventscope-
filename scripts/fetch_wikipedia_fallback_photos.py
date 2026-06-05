from __future__ import annotations

import json
import argparse
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
USER_AGENT = "EventScopeEducationalImageCollector/1.0 (local classroom project; contact: user-local)"
ENWIKI_API = "https://en.wikipedia.org/w/api.php"


WIKI_PAGE_FALLBACKS = {
    "us_china_trade_war_2018": ["China-United States trade war", "Donald Trump", "Xi Jinping"],
    "argentina_default_2001": "1998-2002 Argentine great depression",
    "red_sea_shipping_2024": "Red Sea crisis",
    "flash_crash_2010": "2010 flash crash",
    "asian_financial_crisis_1997": "1997 Asian financial crisis",
    "russian_default_1998": "1998 Russian financial crisis",
    "turkey_lira_2018": "2018 Turkish currency and debt crisis",
    "uk_gilt_crisis_2022": "September 2022 United Kingdom mini-budget",
    "boj_ycc_abandon_2024": "Bank of Japan",
    "pboc_devaluation_2015": "Renminbi",
    "rbi_covid_cuts_2020": "Reserve Bank of India",
    "boj_negative_rates_2016": "Bank of Japan",
    "boc_property_support_2023": "Chinese property sector crisis (2020-present)",
    "ecb_qe_2015": "Quantitative easing",
    "opec_cut_2022": "OPEC",
    "gold_record_2020": "Gold bar",
    "wheat_crisis_2022": "2022 food crises",
    "uranium_rally_2023": "Uranium",
    "copper_rally_2021": "Copper",
    "bitcoin_crash_2018": "Bitcoin",
    "ftx_collapse_2022": ["Bankruptcy of FTX", "FTX", "Sam Bankman-Fried"],
    "chatgpt_launch_2022": "ChatGPT",
    "nvidia_earnings_2023": "Nvidia",
    "google_deepmind_2016": ["AlphaGo versus Lee Sedol", "Lee Sedol", "Google DeepMind"],
    "eu_ai_act_2024": "Artificial Intelligence Act",
    "crowdstrike_outage_2024": "2024 CrowdStrike-related IT outages",
    "taiwan_earthquake_2024": "2024 Hualien earthquake",
    "indian_ocean_tsunami_2004": "2004 Indian Ocean earthquake and tsunami",
    "iceland_ash_2010": "2010 eruptions of Eyjafjallajokull",
    "thailand_floods_2011": "2011 Thailand floods",
    "panama_drought_2023": "Panama Canal",
    "taiwan_chip_drought_2021": ["2020-2021 Taiwan drought", "Sun Moon Lake", "Shimen Dam"],
    "taiwan_cb_hike_2022": "Central Bank of the Republic of China (Taiwan)",
    "taiwan_power_grid_2022": ["Taiwan Power Company", "Taichung Power Plant", "Electricity sector in Taiwan"],
    "taiwan_election_2024": "2024 Taiwanese presidential election",
    "tsmc_arizona_delay_2023": ["TSMC", "Taiwan Semiconductor Manufacturing Company"],
    "taiwan_covid_wave_2021": ["COVID-19 pandemic in Taiwan", "COVID-19 pandemic", "Surgical mask"],
    "auto_chip_shortage_2021": ["2020-2023 global chip shortage", "Semiconductor", "Automotive industry"],
    "pelosi_taiwan_visit_2022": "2022 visit by Nancy Pelosi to Taiwan",
    "taiwan_ai_server_boom_2024": "Data center",
}


def api_json(params: dict, timeout: float = 20) -> dict:
    url = ENWIKI_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extmetadata_value(info: dict, key: str) -> str:
    return (info.get("extmetadata", {}).get(key, {}) or {}).get("value", "")


def page_image_info(page_title: str) -> tuple[str, dict] | None:
    page_payload = api_json(
        {
            "action": "query",
            "format": "json",
            "titles": page_title,
            "prop": "pageimages",
            "piprop": "name",
            "redirects": 1,
        }
    )
    pages = page_payload.get("query", {}).get("pages", {})
    page = next(iter(pages.values()), {})
    image_name = page.get("pageimage")
    if not image_name:
        return None

    file_title = "File:" + image_name
    file_payload = api_json(
        {
            "action": "query",
            "format": "json",
            "titles": file_title,
            "prop": "imageinfo",
            "iiprop": "url|mime|size|extmetadata",
            "iiurlwidth": 1400,
            "redirects": 1,
        }
    )
    file_pages = file_payload.get("query", {}).get("pages", {})
    file_page = next(iter(file_pages.values()), {})
    info = (file_page.get("imageinfo") or [{}])[0]
    if not info:
        return None
    return file_title, info


def download(url: str, path: Path, timeout: float = 30) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        path.write_bytes(resp.read())


def verify_image(path: Path) -> tuple[int, int]:
    with Image.open(path) as img:
        img.verify()
    with Image.open(path) as img:
        return img.size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sleep", type=float, default=1.5)
    parser.add_argument("--only-missing", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in manifest}
    events_by_id = {event["id"]: event for event in HISTORICAL_EVENTS}

    for event_id, page_titles in WIKI_PAGE_FALLBACKS.items():
        item = by_id.get(event_id, {})
        if item.get("status") in {"downloaded", "existing"}:
            print(f"existing {event_id}", flush=True)
            continue
        if args.only_missing and item.get("status") != "missing":
            continue

        event = events_by_id[event_id]
        out_path = OUT_DIR / f"{event_id}.jpg"
        if isinstance(page_titles, str):
            page_titles = [page_titles]

        try:
            last_error = None
            page_title = page_titles[0]
            result = None
            for candidate_page in page_titles:
                page_title = candidate_page
                try:
                    result = page_image_info(candidate_page)
                    if result:
                        break
                    last_error = f"No page image on {candidate_page}"
                except Exception as exc:
                    last_error = str(exc)
                    if "429" in str(exc):
                        raise
                time.sleep(args.sleep)
            if not result:
                raise RuntimeError(last_error or f"No page image on {page_title}")
            file_title, info = result
            url = info.get("thumburl") or info.get("url")
            if not url:
                raise RuntimeError(f"No image URL on {file_title}")
            tmp = OUT_DIR / f".{event_id}.wiki"
            download(url, tmp)
            width, height = verify_image(tmp)
            tmp.replace(out_path)

            file_name = file_title.replace("File:", "")
            by_id[event_id] = {
                "id": event_id,
                "name_zh": event["name_zh"],
                "name_en": event.get("name_en", ""),
                "date": event["date"],
                "category": event["category"],
                "file": str(out_path.relative_to(ROOT)),
                "source_page": "https://en.wikipedia.org/wiki/"
                + urllib.parse.quote(page_title.replace(" ", "_")),
                "commons_title": file_title,
                "license": extmetadata_value(info, "LicenseShortName")
                or extmetadata_value(info, "UsageTerms"),
                "artist": extmetadata_value(info, "Artist"),
                "credit": extmetadata_value(info, "Credit"),
                "description": extmetadata_value(info, "ImageDescription"),
                "query": f"wikipedia:{page_title}",
                "status": "downloaded",
                "size": [width, height],
            }
            print(f"downloaded {event_id}", flush=True)
        except Exception as exc:
            item.update(
                {
                    "id": event_id,
                    "name_zh": event["name_zh"],
                    "name_en": event.get("name_en", ""),
                    "date": event["date"],
                    "category": event["category"],
                    "status": "missing",
                    "fallback_page": page_title,
                    "fallback_error": str(exc),
                }
            )
            by_id[event_id] = item
            print(f"missing {event_id}: {exc}", flush=True)
        time.sleep(args.sleep)

    updated = [by_id[event["id"]] for event in HISTORICAL_EVENTS]
    MANIFEST_PATH.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
    done = sum(1 for item in updated if item.get("status") in {"downloaded", "existing"})
    print(f"done images={done}/{len(updated)} manifest={MANIFEST_PATH}", flush=True)


if __name__ == "__main__":
    main()
