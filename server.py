"""
Oshi-Coord AI - MVP Prototype Backend Server
Zero-dependency Python 3 HTTP server providing:
- Static Web App hosting (/static)
- POST /api/analyze: Vision (Gemini API / Local Canvas fallback)
                   + Weather (OpenWeatherMap API / Seasonal-Regional simulation fallback)
                   + Skeleton Filter & Affiliate Outfit Selection
"""

from __future__ import annotations

import concurrent.futures
import datetime
import hashlib
import http.server
import json
import os
import re
import socketserver
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from catalog import (
    VIBE_LABELS,
    infer_vibe_and_materials,
    map_hex_to_color_info,
    select_outfit,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

CITY_CLIMATE_BASE: Dict[str, Dict[str, Any]] = {
    "東京": {"query": "Tokyo,JP", "offset": 0.0, "lat": 35.6762, "lon": 139.6503},
    "大阪": {"query": "Osaka,JP", "offset": 0.5, "lat": 34.6937, "lon": 135.5023},
    "名古屋": {"query": "Nagoya,JP", "offset": 0.2, "lat": 35.1815, "lon": 136.9066},
    "福岡": {"query": "Fukuoka,JP", "offset": 1.5, "lat": 33.5902, "lon": 130.4017},
    "札幌": {"query": "Sapporo,JP", "offset": -7.5, "lat": 43.0618, "lon": 141.3545},
    "仙台": {"query": "Sendai,JP", "offset": -3.5, "lat": 38.2682, "lon": 140.8694},
    "横浜": {"query": "Yokohama,JP", "offset": 0.0, "lat": 35.4437, "lon": 139.6380},
    "京都": {"query": "Kyoto,JP", "offset": 0.0, "lat": 35.0116, "lon": 135.7681},
    "沖縄": {"query": "Naha,JP", "offset": 8.0, "lat": 26.2124, "lon": 127.6809},
    "ソウル": {"query": "Seoul,KR", "offset": -3.0, "lat": 37.5665, "lon": 126.9780},
    "台北": {"query": "Taipei,TW", "offset": 7.0, "lat": 25.0330, "lon": 121.5654},
}


def _wmo_code_to_ja(code: int) -> str:
    """Map WMO weather code from Open-Meteo to Japanese description."""
    if code == 0:
        return "快晴"
    if code in (1, 2):
        return "晴れ"
    if code == 3:
        return "くもり"
    if code in (45, 48):
        return "霧"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "雨"
    if code in (71, 73, 75, 77, 85, 86):
        return "雪"
    if code in (95, 96, 99):
        return "雷雨"
    return "くもり"


def _fetch_open_meteo(
    location: str,
    target_date_str: str,
    city_info: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Fetch real weather forecast from Open-Meteo (free, no API key required)."""
    lat = city_info.get("lat")
    lon = city_info.get("lon")
    if lat is None or lon is None:
        try:
            geo_q = urllib.parse.quote(location)
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={geo_q}&count=1&language=ja"
            with urllib.request.urlopen(urllib.request.Request(geo_url), timeout=5) as resp:
                geo_data = json.loads(resp.read().decode("utf-8"))
            results = geo_data.get("results") or []
            if not results:
                return None
            lat = results[0]["latitude"]
            lon = results[0]["longitude"]
        except Exception:
            return None

    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min"
            f"&timezone=Asia%2FTokyo&forecast_days=14"
        )
        with urllib.request.urlopen(urllib.request.Request(url), timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        if not dates:
            return None

        idx = dates.index(target_date_str) if target_date_str in dates else min(1, len(dates) - 1)
        temp_max = round(float(daily["temperature_2m_max"][idx]), 1)
        temp_min = round(float(daily["temperature_2m_min"][idx]), 1)
        # Daytime representative temperature
        temp_c = round((temp_max * 0.65) + (temp_min * 0.35), 1)
        wmo = int(daily["weather_code"][idx])
        condition = _wmo_code_to_ja(wmo)

        return _build_weather_result(
            location=location,
            target_date=dates[idx],
            temp_c=temp_c,
            temp_min=temp_min,
            temp_max=temp_max,
            condition=condition,
            source="open-meteo",
        )
    except Exception:
        return None

# Monthly average daytime/mean temperatures for Tokyo (baseline)
MONTHLY_TOKYO_TEMP: Dict[int, float] = {
    1: 6.0, 2: 7.0, 3: 10.5, 4: 15.5, 5: 20.0, 6: 23.0,
    7: 27.5, 8: 29.0, 9: 25.0, 10: 19.0, 11: 14.0, 12: 8.5,
}


def fetch_weather(
    location: str,
    target_date_str: str,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch weather from OpenWeatherMap API if key is set, else simulate realistically."""
    key = (api_key or os.environ.get("OPENWEATHER_API_KEY") or "").strip()
    city_info = CITY_CLIMATE_BASE.get(location, {"query": location, "offset": 0.0})

    try:
        target_dt = datetime.date.fromisoformat(target_date_str)
    except ValueError:
        target_dt = datetime.date.today() + datetime.timedelta(days=1)
        target_date_str = target_dt.isoformat()

    if key:
        try:
            q = urllib.parse.quote(city_info["query"])
            url = f"https://api.openweathermap.org/data/2.5/forecast?q={q}&appid={key}&units=metric&lang=ja"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            forecasts = data.get("list", [])
            # Find forecast closest to target_date 12:00
            day_items = [f for f in forecasts if f.get("dt_txt", "").startswith(target_date_str)]
            chosen = None
            if day_items:
                chosen = min(
                    day_items,
                    key=lambda f: abs(int(f["dt_txt"][11:13]) - 12),
                )
            elif forecasts:
                chosen = forecasts[min(len(forecasts) - 1, 8)]

            if chosen:
                temp_c = round(float(chosen["main"]["temp"]), 1)
                temp_min = round(float(chosen["main"].get("temp_min", temp_c - 3)), 1)
                temp_max = round(float(chosen["main"].get("temp_max", temp_c + 3)), 1)
                condition = chosen["weather"][0]["description"]
                return _build_weather_result(
                    location=location,
                    target_date=target_date_str,
                    temp_c=temp_c,
                    temp_min=temp_min,
                    temp_max=temp_max,
                    condition=condition,
                    source="openweathermap",
                )
        except Exception:
            pass

    # Try free keyless Open-Meteo real forecast
    open_meteo_res = _fetch_open_meteo(location, target_date_str, city_info)
    if open_meteo_res is not None:
        return open_meteo_res

    # Deterministic simulation fallback based on month, location, and date hash
    base_temp = MONTHLY_TOKYO_TEMP.get(target_dt.month, 16.0) + city_info["offset"]
    seed_bytes = hashlib.sha256(f"{location}:{target_date_str}".encode("utf-8")).digest()
    temp_jitter = ((seed_bytes[0] % 7) - 3) * 0.8
    temp_c = round(base_temp + temp_jitter, 1)
    temp_min = round(temp_c - 4.0, 1)
    temp_max = round(temp_c + 3.5, 1)

    weather_roll = seed_bytes[1] % 10
    if weather_roll < 5:
        condition = "晴れ"
    elif weather_roll < 8:
        condition = "くもり"
    else:
        condition = "小雨"

    return _build_weather_result(
        location=location,
        target_date=target_date_str,
        temp_c=temp_c,
        temp_min=temp_min,
        temp_max=temp_max,
        condition=condition,
        source="simulation",
    )


def _build_weather_result(
    location: str,
    target_date: str,
    temp_c: float,
    temp_min: float,
    temp_max: float,
    condition: str,
    source: str,
) -> Dict[str, Any]:
    need_outer = temp_c <= 19.0 or ("雨" in condition and temp_c <= 22.0)
    if temp_c <= 10:
        advice = "しっかり防寒が必要な気温です。コートや厚手ニットを含めた4点セットを提案します。"
    elif temp_c <= 19:
        advice = "朝晩の冷え込みに備えて羽織れるアウターが必須。脱ぎ着しやすい構成を提案します。"
    elif "雨" in condition:
        advice = "雨予報のため、撥水・汚れにくい素材や足元を意識したコーデを提案します。"
    else:
        advice = "過ごしやすい〜暖かい気温のため、アウターなしの軽やかな3点セットを提案します。"

    return {
        "location": location,
        "target_date": target_date,
        "temp_c": temp_c,
        "temp_min": temp_min,
        "temp_max": temp_max,
        "condition": condition,
        "need_outer": need_outer,
        "advice": advice,
        "source": source,
    }


def analyze_vision(
    image_base64: Optional[str],
    dominant_hexes: List[str],
    oshi_hint: str,
    api_key: Optional[str] = None,
    override_colors: Optional[List[str]] = None,
    override_vibe: Optional[str] = None,
) -> Dict[str, Any]:
    """Analyze uploaded image via Gemini Vision API if key is provided, else use client Canvas colors + rules."""
    if override_colors:
        safe_hexes = [hx for hx in override_colors if isinstance(hx, str) and hx.startswith("#")][:3]
        if safe_hexes:
            colors = [map_hex_to_color_info(hx) for hx in safe_hexes]
            inferred_vibe, materials = infer_vibe_and_materials(colors, oshi_hint)
            vibe = override_vibe if override_vibe in VIBE_LABELS else inferred_vibe
            return {
                "colors": colors,
                "materials": materials,
                "vibe": vibe,
                "vibe_label": VIBE_LABELS[vibe],
                "source": "manual_edit",
            }

    key = (api_key or os.environ.get("GEMINI_API_KEY") or "").strip()

    if key and image_base64:
        try:
            mime_type = "image/jpeg"
            b64_data = image_base64
            if "," in image_base64 and image_base64.startswith("data:"):
                header, b64_data = image_base64.split(",", 1)
                if ";" in header:
                    mime_type = header.replace("data:", "").split(";")[0]

            prompt = (
                "あなたはプロのファッションスタイリストです。アップロードされた画像（推しキャラクターや概念画像）から、"
                "バウンドコーデ（概念コーデ）を作るための要素を抽出し、必ず以下のJSON形式のみで返してください。\n"
                '{"hex_colors": ["#RRGGBB", "#RRGGBB", "#RRGGBB"], '
                '"materials": ["素材1", "素材2"], '
                '"vibe": "cool_mode | sweet_girly | street_casual | elegant_classic | subculture_cyber のいずれか1つ"}\n'
                f"補足ヒント: {oshi_hint or 'なし'}"
            )
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": mime_type, "data": b64_data}},
                        ]
                    }
                ],
                "generationConfig": {"response_mime_type": "application/json"},
            }
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(text)
            hex_list = parsed.get("hex_colors", [])[:3]
            if hex_list:
                colors = [map_hex_to_color_info(hx) for hx in hex_list]
                vibe = parsed.get("vibe", "cool_mode")
                if vibe not in VIBE_LABELS:
                    vibe = "cool_mode"
                materials = parsed.get("materials", ["シフォン", "ツイル"])[:3]
                return {
                    "colors": colors,
                    "materials": materials,
                    "vibe": vibe,
                    "vibe_label": VIBE_LABELS[vibe],
                    "source": "gemini_vision",
                }
        except Exception:
            pass

    # Local fallback using Canvas-extracted dominant hexes
    safe_hexes = [hx for hx in (dominant_hexes or []) if isinstance(hx, str) and hx.startswith("#")][:3]
    if not safe_hexes:
        safe_hexes = ["#2B2D42", "#8D99AE", "#EF233C"]

    colors = [map_hex_to_color_info(hx) for hx in safe_hexes]
    vibe, materials = infer_vibe_and_materials(colors, oshi_hint)

    return {
        "colors": colors,
        "materials": materials,
        "vibe": vibe,
        "vibe_label": VIBE_LABELS[vibe],
        "source": "local_canvas",
    }


def _fetch_html(url: str, timeout: float = 3.5) -> str:
    """Fetch HTML with a browser-like User-Agent."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        # Try cp932 / utf-8 gracefully
        for enc in ("utf-8", "cp932"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="replace")


def _scrape_zozo_first_item(search_url: str) -> Optional[Dict[str, str]]:
    """Extract the first product image, title, price, and URL from ZOZOTOWN search HTML."""
    try:
        html = _fetch_html(search_url)
        img_match = re.search(r'(?:src|data-src)="(https://c\.imgz\.jp/[^"]+\.(?:jpg|jpeg|png|webp))"', html)
        link_match = re.search(r'href="(/shop/[^"]+/goods/\d+/[^"]*)"', html)
        if not img_match:
            return None
        img_url = img_match.group(1)
        product_url = f"https://zozo.jp{link_match.group(1)}" if link_match else search_url
        return {"image_url": img_url, "product_url": product_url}
    except Exception:
        return None


def _scrape_shein_first_item(search_url: str) -> Optional[Dict[str, str]]:
    """Extract the first product image and URL from SHEIN search HTML if accessible."""
    try:
        html = _fetch_html(search_url)
        img_match = re.search(
            r'(?:src|data-src)="(https://img\.ltwebstatic\.com/[^"]+\.(?:jpg|jpeg|png|webp))"',
            html,
        )
        if not img_match:
            return None
        return {"image_url": img_match.group(1), "product_url": search_url}
    except Exception:
        return None


def fetch_ec_showcase(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Build 3 ZOZOTOWN picks + 3 SHEIN picks (= 6 items total) with live site product photos
    when reachable, falling back cleanly to styled preview cards.
    """
    core_items = items[:3]
    zozo_picks: List[Dict[str, Any]] = []
    shein_picks: List[Dict[str, Any]] = []

    def _build_pick(item: Dict[str, Any], platform: str) -> Dict[str, Any]:
        search_url = item["zozotown_url"] if platform == "ZOZOTOWN" else item["shein_url"]
        scraped = (
            _scrape_zozo_first_item(search_url)
            if platform == "ZOZOTOWN"
            else _scrape_shein_first_item(search_url)
        )
        return {
            "platform": platform,
            "category": item["category"],
            "category_label": item["category_label"],
            "title": item["name"],
            "matched_color": item["matched_color"],
            "matched_color_hex": item.get("matched_color_hex", "#333745"),
            "price": item["price"],
            "image_url": scraped["image_url"] if scraped else None,
            "url": scraped["product_url"] if scraped else search_url,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        zozo_futures = [executor.submit(_build_pick, it, "ZOZOTOWN") for it in core_items]
        shein_futures = [executor.submit(_build_pick, it, "SHEIN") for it in core_items]
        for fut in zozo_futures:
            zozo_picks.append(fut.result())
        for fut in shein_futures:
            shein_picks.append(fut.result())

    return {"zozotown": zozo_picks, "shein": shein_picks}


def process_analyze_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Run the full analysis pipeline for an /api/analyze JSON payload."""
    location = (data.get("location") or "東京").strip()
    target_date = (
        data.get("target_date") or (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    ).strip()
    skeleton_type = (data.get("skeleton_type") or "wave").strip()
    gender = (data.get("gender") or "women").strip()
    raw_budget = data.get("budget_yen")
    budget_yen = int(raw_budget) if raw_budget is not None else 10000
    oshi_hint = (data.get("oshi_hint") or "").strip()

    vision = analyze_vision(
        image_base64=data.get("image_base64"),
        dominant_hexes=data.get("dominant_hexes") or [],
        oshi_hint=oshi_hint,
        api_key=data.get("gemini_api_key"),
        override_colors=data.get("override_colors"),
        override_vibe=data.get("override_vibe"),
    )
    weather = fetch_weather(
        location=location,
        target_date_str=target_date,
        api_key=data.get("openweather_api_key"),
    )
    recommendation = select_outfit(
        extracted_colors=vision["colors"],
        vibe=vision["vibe"],
        skeleton_type=skeleton_type,
        temp_c=weather["temp_c"],
        weather_condition=weather["condition"],
        budget_yen=budget_yen,
        gender=gender,
        affiliate_id=data.get("affiliate_id"),
    )
    ec_showcase = fetch_ec_showcase(recommendation["items"])

    return {
        "vision": vision,
        "weather": weather,
        "recommendation": recommendation,
        "ec_showcase": ec_showcase,
    }


class OshiCoordHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP Request Handler serving static files and JSON API endpoints."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _send_json(self, status_code: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._send_json(200, {"status": "ok", "app": "Oshi-Coord AI MVP"})
            return
        if self.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/api/analyze":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            data = json.loads(raw_body.decode("utf-8"))
        except Exception as exc:
            self._send_json(400, {"error": f"Invalid JSON payload: {exc}"})
            return

        result = process_analyze_request(data)
        self._send_json(200, result)


class ReusableTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


def run_server(port: int = 8000) -> None:
    with ReusableTCPServer(("127.0.0.1", port), OshiCoordHandler) as httpd:
        print(f"Oshi-Coord AI MVP server running at http://127.0.0.1:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    run_server(port)
