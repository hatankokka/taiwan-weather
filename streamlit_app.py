from __future__ import annotations

import asyncio
import html
import json
import math
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


APP_DIR = Path(__file__).parent
GEOJSON_PATH = APP_DIR / "data" / "twCounty1982.json"
COMPONENT_DIR = APP_DIR / "components" / "interactive_map"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
interactive_map_component = components.declare_component("interactive_map", path=str(COMPONENT_DIR))

REGIONS = [
    {"id": "all", "label": "全域", "color": "#d6c38a"},
    {"id": "台北州", "label": "台北州", "color": "#78a6b8"},
    {"id": "新竹州", "label": "新竹州", "color": "#d2a65f"},
    {"id": "台中州", "label": "台中州", "color": "#8fb56f"},
    {"id": "台南州", "label": "台南州", "color": "#c88d6c"},
    {"id": "高雄州", "label": "高雄州", "color": "#c96b66"},
    {"id": "花蓮港庁", "label": "花蓮港庁", "color": "#7aa58c"},
    {"id": "台東庁", "label": "台東庁", "color": "#9c86b8"},
    {"id": "澎湖庁", "label": "澎湖庁", "color": "#9aa2a9"},
]

COUNTY_TO_REGION = {
    "台北市": "台北州",
    "台北縣": "台北州",
    "基隆市": "台北州",
    "宜蘭縣": "台北州",
    "桃園縣": "新竹州",
    "新竹縣": "新竹州",
    "新竹市": "新竹州",
    "苗栗縣": "新竹州",
    "台中市": "台中州",
    "台中縣": "台中州",
    "彰化縣": "台中州",
    "南投縣": "台中州",
    "雲林縣": "台南州",
    "嘉義縣": "台南州",
    "嘉義市": "台南州",
    "台南縣": "台南州",
    "台南市": "台南州",
    "高雄縣": "高雄州",
    "高雄市": "高雄州",
    "屏東縣": "高雄州",
    "花蓮縣": "花蓮港庁",
    "台東縣": "台東庁",
    "澎湖縣": "澎湖庁",
}

PLACES = [
    {"id": "taihoku", "historical": "台北", "reading": "たいほく", "current": "台北", "region": "台北州", "lat": 25.0330, "lon": 121.5654, "main": True},
    {"id": "kiirun", "historical": "基隆", "reading": "きいるん", "current": "基隆", "region": "台北州", "lat": 25.1283, "lon": 121.7419, "main": True},
    {"id": "tansui", "historical": "淡水", "reading": "たんすい", "current": "淡水", "region": "台北州", "lat": 25.1679, "lon": 121.4452, "main": False},
    {"id": "giran", "historical": "宜蘭", "reading": "ぎらん", "current": "宜蘭", "region": "台北州", "lat": 24.7591, "lon": 121.7538, "main": True},
    {"id": "rato", "historical": "羅東", "reading": "らとう", "current": "羅東", "region": "台北州", "lat": 24.6769, "lon": 121.7707, "main": False},
    {"id": "suo", "historical": "蘇澳", "reading": "すおう", "current": "蘇澳", "region": "台北州", "lat": 24.5967, "lon": 121.8524, "main": False},
    {"id": "nanao", "historical": "南澳", "reading": "なんおう", "current": "南澳", "region": "台北州", "lat": 24.4667, "lon": 121.8000, "main": False},
    {"id": "shinchiku", "historical": "新竹", "reading": "しんちく", "current": "新竹", "region": "新竹州", "lat": 24.8138, "lon": 120.9675, "main": True},
    {"id": "toen", "historical": "桃園", "reading": "とうえん", "current": "桃園", "region": "新竹州", "lat": 24.9937, "lon": 121.3009, "main": True},
    {"id": "chureki", "historical": "中壢", "reading": "ちゅうれき", "current": "中壢", "region": "新竹州", "lat": 24.9536, "lon": 121.2257, "main": False},
    {"id": "taikei", "historical": "大溪", "reading": "たいけい", "current": "大溪", "region": "新竹州", "lat": 24.8837, "lon": 121.2904, "main": False},
    {"id": "chikuto", "historical": "竹東", "reading": "ちくとう", "current": "竹東", "region": "新竹州", "lat": 24.7360, "lon": 121.0910, "main": False},
    {"id": "chikunan", "historical": "竹南", "reading": "ちくなん", "current": "竹南", "region": "新竹州", "lat": 24.6868, "lon": 120.8726, "main": False},
    {"id": "tofun", "historical": "頭分", "reading": "とうふん", "current": "頭份", "region": "新竹州", "lat": 24.6873, "lon": 120.9026, "main": False},
    {"id": "byoritsu", "historical": "苗栗", "reading": "びょうりつ", "current": "苗栗", "region": "新竹州", "lat": 24.5602, "lon": 120.8214, "main": True},
    {"id": "taiko", "historical": "大湖", "reading": "たいこ", "current": "大湖", "region": "新竹州", "lat": 24.4225, "lon": 120.8677, "main": False},
    {"id": "taichu", "historical": "台中", "reading": "たいちゅう", "current": "台中", "region": "台中州", "lat": 24.1477, "lon": 120.6736, "main": True},
    {"id": "shoka", "historical": "彰化", "reading": "しょうか", "current": "彰化", "region": "台中州", "lat": 24.0809, "lon": 120.5389, "main": True},
    {"id": "nanto", "historical": "南投", "reading": "なんとう", "current": "南投", "region": "台中州", "lat": 23.9162, "lon": 120.6853, "main": True},
    {"id": "hori", "historical": "埔里", "reading": "ほり", "current": "埔里", "region": "台中州", "lat": 23.9640, "lon": 120.9719, "main": False},
    {"id": "niitakayama", "historical": "新高山", "reading": "にいたかやま", "current": "玉山", "region": "台中州", "lat": 23.4700, "lon": 120.9573, "elevation": 3952, "main": False},
    {"id": "tsugitakayama", "historical": "次高山", "reading": "つぎたかやま", "current": "雪山", "region": "台中州", "lat": 24.3833, "lon": 121.2333, "elevation": 3886, "main": False},
    {"id": "kagi", "historical": "嘉義", "reading": "かぎ", "current": "嘉義", "region": "台南州", "lat": 23.4801, "lon": 120.4491, "main": True},
    {"id": "toroku", "historical": "斗六", "reading": "とろく", "current": "斗六", "region": "台南州", "lat": 23.7078, "lon": 120.5433, "main": False},
    {"id": "tainan", "historical": "台南", "reading": "たいなん", "current": "台南", "region": "台南州", "lat": 22.9999, "lon": 120.2269, "main": True},
    {"id": "shinei", "historical": "新営", "reading": "しんえい", "current": "新營", "region": "台南州", "lat": 23.3075, "lon": 120.3128, "main": False},
    {"id": "takao", "historical": "高雄", "reading": "たかお", "current": "高雄", "region": "高雄州", "lat": 22.6273, "lon": 120.3014, "main": True},
    {"id": "okayama", "historical": "岡山", "reading": "おかやま", "current": "岡山", "region": "高雄州", "lat": 22.7935, "lon": 120.2958, "main": False},
    {"id": "hozan", "historical": "鳳山", "reading": "ほうざん", "current": "鳳山", "region": "高雄州", "lat": 22.6266, "lon": 120.3613, "main": False},
    {"id": "heito", "historical": "屏東", "reading": "へいとう", "current": "屏東", "region": "高雄州", "lat": 22.6761, "lon": 120.4942, "main": True},
    {"id": "choshu", "historical": "潮州", "reading": "ちょうしゅう", "current": "潮州", "region": "高雄州", "lat": 22.5510, "lon": 120.5380, "main": False},
    {"id": "toko", "historical": "東港", "reading": "とうこう", "current": "東港", "region": "高雄州", "lat": 22.4665, "lon": 120.4547, "main": False},
    {"id": "riukiu", "historical": "琉球", "reading": "りゅうきゅう", "current": "小琉球", "region": "高雄州", "lat": 22.3386, "lon": 120.3693, "main": False},
    {"id": "koshun", "historical": "恒春", "reading": "こうしゅん", "current": "恆春", "region": "高雄州", "lat": 22.0039, "lon": 120.7440, "main": True},
    {"id": "kizan", "historical": "旗山", "reading": "きざん", "current": "旗山", "region": "高雄州", "lat": 22.8845, "lon": 120.4839, "main": False},
    {"id": "karenko", "historical": "花蓮港", "reading": "かれんこう", "current": "花蓮", "region": "花蓮港庁", "lat": 23.9872, "lon": 121.6015, "main": True},
    {"id": "taroko", "historical": "太魯閣", "reading": "たろこ", "current": "太魯閣", "region": "花蓮港庁", "lat": 24.1610, "lon": 121.6210, "elevation": 60, "main": False},
    {"id": "horin", "historical": "鳳林", "reading": "ほうりん", "current": "鳳林", "region": "花蓮港庁", "lat": 23.7460, "lon": 121.4532, "main": False},
    {"id": "mizuho", "historical": "瑞穂", "reading": "みずほ", "current": "瑞穗", "region": "花蓮港庁", "lat": 23.4969, "lon": 121.3769, "main": False},
    {"id": "tamazato", "historical": "玉里", "reading": "たまざと", "current": "玉里", "region": "花蓮港庁", "lat": 23.3328, "lon": 121.3157, "main": True},
    {"id": "tomisato", "historical": "富里", "reading": "とみさと", "current": "富里", "region": "花蓮港庁", "lat": 23.1790, "lon": 121.2496, "main": False},
    {"id": "taito", "historical": "台東", "reading": "たいとう", "current": "台東", "region": "台東庁", "lat": 22.7583, "lon": 121.1444, "main": True},
    {"id": "kanzan", "historical": "関山", "reading": "かんざん", "current": "關山", "region": "台東庁", "lat": 23.0475, "lon": 121.1619, "main": False},
    {"id": "shinko", "historical": "新港", "reading": "しんこう", "current": "成功", "region": "台東庁", "lat": 23.1001, "lon": 121.3775, "main": True},
    {"id": "kashoto", "historical": "火焼島", "reading": "かしょうとう", "current": "緑島", "region": "台東庁", "lat": 22.6604, "lon": 121.4916, "main": False},
    {"id": "kotosho", "historical": "紅頭嶼", "reading": "こうとうしょ", "current": "蘭嶼", "region": "台東庁", "lat": 22.0569, "lon": 121.5505, "main": False},
    {"id": "mako", "historical": "馬公", "reading": "まこう", "current": "馬公", "region": "澎湖庁", "lat": 23.5655, "lon": 119.5863, "main": True},
    {"id": "hakusha", "historical": "白沙", "reading": "はくしゃ", "current": "白沙", "region": "澎湖庁", "lat": 23.6535, "lon": 119.5988, "main": False},
    {"id": "moan", "historical": "望安", "reading": "もうあん", "current": "望安", "region": "澎湖庁", "lat": 23.3590, "lon": 119.5005, "main": False},
    {"id": "shichibi", "historical": "七美", "reading": "しちび", "current": "七美", "region": "澎湖庁", "lat": 23.2085, "lon": 119.4295, "main": True},
]

OVERVIEW_PLACE_IDS = {"taihoku", "shinchiku", "taichu", "niitakayama", "tainan", "takao", "karenko", "taito", "mako"}

ROMAJI_PLACE_NAMES = {
    "taihoku": "Taihoku", "kiirun": "Kiirun", "tansui": "Tansui", "giran": "Giran", "rato": "Rato", "suo": "Suo", "nanao": "Nanao",
    "shinchiku": "Shinchiku", "toen": "Toen", "chureki": "Chureki", "taikei": "Taikei", "chikuto": "Chikuto", "chikunan": "Chikunan", "tofun": "Tofun", "byoritsu": "Byoritsu", "taiko": "Taiko",
    "taichu": "Taichu", "shoka": "Shoka", "nanto": "Nanto", "hori": "Hori", "niitakayama": "Mt. Niitaka", "tsugitakayama": "Tsugitakayama",
    "kagi": "Kagi", "toroku": "Toroku", "tainan": "Tainan", "shinei": "Shinei",
    "takao": "Takao", "okayama": "Okayama", "hozan": "Hozan", "heito": "Heito", "choshu": "Choshu", "toko": "Toko", "riukiu": "Riukyu", "koshun": "Koshun", "kizan": "Kizan",
    "karenko": "Karenko", "taroko": "Taroko", "horin": "Horin", "mizuho": "Mizuho", "tamazato": "Tamazato", "tomisato": "Tomisato",
    "taito": "Taito", "kanzan": "Kanzan", "shinko": "Shinko", "kashoto": "Kashoto", "kotosho": "Kotosho",
    "mako": "Mako", "hakusha": "Hakusha", "moan": "Moan", "shichibi": "Shichibi",
}

ROMAJI_REGION_NAMES = {
    "all": "All",
    "台北州": "Taihoku Pref.",
    "新竹州": "Shinchiku Pref.",
    "台中州": "Taichu Pref.",
    "台南州": "Tainan Pref.",
    "高雄州": "Takao Pref.",
    "花蓮港庁": "Karenko Pref.",
    "台東庁": "Taito Pref.",
    "澎湖庁": "Hoko Pref.",
}

LANGUAGES = {
    "ja": "日本語",
    "zh": "華語",
    "en": "English",
    "nl": "Nederlands",
}

SPEECH_VOICES = {
    "ja": [("ja-JP-KeitaNeural", "Keita / 男声"), ("ja-JP-NanamiNeural", "Nanami / 女声")],
    "zh": [("zh-TW-YunJheNeural", "YunJhe / 男聲"), ("zh-TW-HsiaoChenNeural", "HsiaoChen / 女聲"), ("zh-TW-HsiaoYuNeural", "HsiaoYu / 女聲")],
    "en": [("en-US-AndrewNeural", "Andrew / male"), ("en-US-AvaNeural", "Ava / female"), ("en-US-EmmaNeural", "Emma / female"), ("en-US-BrianNeural", "Brian / male"), ("en-US-JennyNeural", "Jenny / female")],
    "nl": [("nl-NL-MaartenNeural", "Maarten / man"), ("nl-NL-ColetteNeural", "Colette / vrouw"), ("nl-NL-FennaNeural", "Fenna / vrouw")],
}

WEATHER_CODE_JA = {
    0: "快晴", 1: "晴れ", 2: "薄曇り", 3: "曇り", 45: "霧", 48: "霧氷霧",
    51: "霧雨", 53: "霧雨", 55: "強い霧雨", 56: "着氷性霧雨", 57: "強い着氷性霧雨",
    61: "小雨", 63: "雨", 65: "強い雨", 66: "着氷性雨", 67: "強い着氷性雨",
    71: "小雪", 73: "雪", 75: "強い雪", 77: "雪粒",
    80: "にわか雨", 81: "にわか雨", 82: "強いにわか雨",
    85: "にわか雪", 86: "強いにわか雪", 95: "雷雨", 96: "雷雨・雹", 99: "強い雷雨・雹",
}

WEATHER_KIND_TEXT = {
    "ja": {"clear": "晴れ", "partly": "薄曇り", "cloudy": "曇り", "fog": "霧", "drizzle": "霧雨", "rain": "雨", "snow": "雪", "thunder": "雷雨", "unknown": "天気不明"},
    "zh": {"clear": "晴朗", "partly": "晴時多雲", "cloudy": "陰天", "fog": "霧", "drizzle": "毛毛雨", "rain": "雨", "snow": "雪", "thunder": "雷雨", "unknown": "天氣不明"},
    "en": {"clear": "Clear", "partly": "Partly cloudy", "cloudy": "Cloudy", "fog": "Fog", "drizzle": "Drizzle", "rain": "Rain", "snow": "Snow", "thunder": "Thunderstorm", "unknown": "Weather unknown"},
    "nl": {"clear": "Helder", "partly": "Half bewolkt", "cloudy": "Bewolkt", "fog": "Mist", "drizzle": "Motregen", "rain": "Regen", "snow": "Sneeuw", "thunder": "Onweer", "unknown": "Weer onbekend"},
}

WIND_DIRECTIONS = {
    "ja": ["北", "北北東", "北東", "東北東", "東", "東南東", "南東", "南南東", "南", "南南西", "南西", "西南西", "西", "西北西", "北西", "北北西"],
    "zh": ["北", "北北東", "東北", "東北東", "東", "東南東", "東南", "南南東", "南", "南南西", "西南", "西南西", "西", "西北西", "西北", "北北西"],
    "en": ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"],
    "nl": ["N", "NNO", "NO", "ONO", "O", "OZO", "ZO", "ZZO", "Z", "ZZW", "ZW", "WZW", "W", "WNW", "NW", "NNW"],
}

UI = {
    "ja": {
        "title": "日本統治時代の台湾地名で現在の天気を見てみよう！",
        "subtitle": "台湾・澎湖 歴史地名天気",
        "region": "地域", "place": "地点", "map_mode": "地図表示", "voice": "声",
        "weather": "天気", "temperature": "気温", "precipitation": "降水",
        "today": "けふ", "current_name": "現在名", "bulletin": "読み上げ原稿",
        "speak": "音声生成", "download": "MP3保存", "forecast": "週間予報",
    },
    "zh": {
        "title": "用日治時期的臺灣地名來看看現在的天氣！",
        "subtitle": "臺灣・澎湖 歷史地名天氣",
        "region": "地域", "place": "地點", "map_mode": "地圖顯示", "voice": "聲音",
        "weather": "天氣", "temperature": "氣溫", "precipitation": "降雨",
        "today": "今日", "current_name": "現今名稱", "bulletin": "朗讀稿",
        "speak": "產生語音", "download": "儲存MP3", "forecast": "一週預報",
    },
    "en": {
        "title": "Check current weather using Japanese-era Formosa place names.",
        "subtitle": "Formosa and Hoko Historical Place-Name Weather",
        "region": "Region", "place": "Place", "map_mode": "Map display", "voice": "Voice",
        "weather": "Weather", "temperature": "Temp.", "precipitation": "Rain",
        "today": "Today", "current_name": "Present-day name", "bulletin": "Speech Draft",
        "speak": "Create audio", "download": "Save MP3", "forecast": "Weekly forecast",
    },
    "nl": {
        "title": "Bekijk het actuele weer met plaatsnamen van Formosa uit de Japanse tijd.",
        "subtitle": "Formosa en Hoko historisch plaatsnamenweer",
        "region": "Regio", "place": "Plaats", "map_mode": "Kaartweergave", "voice": "Stem",
        "weather": "Weer", "temperature": "Temp.", "precipitation": "Neerslag",
        "today": "Vandaag", "current_name": "Naam vandaag", "bulletin": "Voorleestekst",
        "speak": "Audio maken", "download": "MP3 opslaan", "forecast": "Weekverwachting",
    },
}


def main() -> None:
    st.set_page_config(page_title="台湾・澎湖 歴史地名天気", page_icon="☂", layout="wide")
    inject_css()
    query_defaults = query_state()

    with st.sidebar:
        language_ids = list(LANGUAGES.keys())
        lang = st.radio(
            "Language",
            language_ids,
            index=language_ids.index(query_defaults["lang"]),
            format_func=lambda key: LANGUAGES[key],
            horizontal=True,
        )
        ui = UI[lang]
        region_ids = [r["id"] for r in REGIONS]
        region = st.selectbox(
            ui["region"],
            region_ids,
            index=region_ids.index(query_defaults["region"]),
            format_func=lambda rid: region_display_name(rid, lang),
        )
        mode_ids = ["weather", "temperature", "precipitation"]
        mode = st.radio(
            ui["map_mode"],
            mode_ids,
            index=mode_ids.index(query_defaults["mode"]),
            format_func=lambda key: ui[key],
            horizontal=True,
        )
        voice_options = SPEECH_VOICES[lang]
        voice = st.selectbox(ui["voice"], [v[0] for v in voice_options], format_func=lambda key: dict(voice_options)[key])

    current_mode = mode or "weather"
    visible_places = places_for_region(region)
    selected_place_id = query_defaults.get("place")
    if selected_place_id and selected_place_id not in {place["id"] for place in visible_places}:
        selected_place_id = ""
    weather = fetch_weather(tuple(place["id"] for place in visible_places))
    selected_place = place_picker(ui, lang, visible_places, selected_place_id)
    sync_query_params(lang, region, current_mode, selected_place["id"])
    selected_weather = weather.get(selected_place["id"], {})

    st.markdown(f"<h1>{html.escape(ui['title'])}</h1>", unsafe_allow_html=True)
    st.caption(ui["subtitle"])

    left, right = st.columns([1.45, 1], gap="large")
    with left:
        map_event = interactive_map_component(
            html=render_map(region, current_mode, lang, weather),
            height=690,
            default=None,
            key=f"interactive-map-{lang}-{region}-{current_mode}",
        )
        if isinstance(map_event, dict):
            next_lang = map_event.get("lang") if map_event.get("lang") in LANGUAGES else lang
            region_ids = {item["id"] for item in REGIONS}
            next_region = map_event.get("region") if map_event.get("region") in region_ids else region
            mode_ids = {"weather", "temperature", "precipitation"}
            next_mode = map_event.get("mode") if map_event.get("mode") in mode_ids else current_mode
            place_ids = {place["id"] for place in PLACES}
            next_place = map_event.get("place") if map_event.get("place") in place_ids else ""
            if sync_query_params(next_lang, next_region, next_mode, next_place):
                st.rerun()

    with right:
        render_place_detail(selected_place, selected_weather, lang, ui)

    bulletin_text, speech_text = build_bulletin(lang, region, selected_place, selected_weather, weather)
    st.subheader(ui["bulletin"])
    edited_bulletin = st.text_area(ui["bulletin"], value=bulletin_text, height=210, label_visibility="collapsed")

    c1, c2 = st.columns([1, 1])
    if c1.button(ui["speak"], width="stretch"):
        spoken = speech_text if edited_bulletin.strip() == bulletin_text.strip() else edited_bulletin
        mp3 = create_tts_mp3(spoken, voice)
        st.audio(mp3, format="audio/mp3")
        c2.download_button(ui["download"], mp3, file_name=f"weather-{lang}-{safe_filename(place_display_name(selected_place, lang))}.mp3", mime="audio/mpeg", width="stretch")

    with st.expander("Open Source / Open Data"):
        st.write("地図形状はg0v/twgeojson由来のGeoJSON、気象データはOpen-Meteo Forecast APIを使用しています。")


def query_state() -> dict:
    params = st.query_params
    language_ids = set(LANGUAGES.keys())
    region_ids = {region["id"] for region in REGIONS}
    mode_ids = {"weather", "temperature", "precipitation"}
    place_ids = {place["id"] for place in PLACES}
    lang = params.get("lang", "ja")
    region = params.get("region", "all")
    mode = params.get("mode", "weather")
    place = params.get("place", "")
    return {
        "lang": lang if lang in language_ids else "ja",
        "region": region if region in region_ids else "all",
        "mode": mode if mode in mode_ids else "weather",
        "place": place if place in place_ids else "",
    }


def sync_query_params(lang: str, region: str, mode: str, place_id: str) -> bool:
    desired = {"lang": lang, "region": region, "mode": mode, "place": place_id}
    current = {key: st.query_params.get(key, "") for key in desired}
    if current != desired:
        st.query_params.update(desired)
        return True
    return False


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
          background:
            linear-gradient(90deg, rgba(91,55,33,.10) 1px, transparent 1px),
            linear-gradient(rgba(91,55,33,.08) 1px, transparent 1px),
            linear-gradient(135deg, #efe5cf, #d9c7a6 42%, #b88969);
          background-size: 42px 24px, 42px 24px, auto;
        }
        h1 { color: #3e2417; letter-spacing: 0; font-size: clamp(1.55rem, 3vw, 2.25rem); }
        h1, h2, h3,
        [data-testid="stMarkdownContainer"],
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stCaptionContainer"],
        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"],
        [data-testid="stWidgetLabel"] {
          color: #2f241c !important;
        }
        [data-testid="stSidebar"] { background: #f2ead8; }
        [data-testid="stSidebar"] * {
          color: #3c281b;
        }
        [data-baseweb="select"] *,
        [data-testid="stTextArea"] textarea {
          color: inherit;
        }
        .metric-card {
          border: 1px solid rgba(84,55,36,.22);
          background: rgba(255,250,238,.86);
          border-radius: 8px;
          padding: 14px;
          margin-bottom: 10px;
          box-shadow: 0 8px 22px rgba(45,28,18,.08);
        }
        .metric-card .name { font-size: 1.35rem; font-weight: 800; color: #3b271c; }
        .metric-card .sub { color: #6f5948; margin-bottom: 8px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=3600)
def load_geojson() -> dict:
    with GEOJSON_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    for feature in data["features"]:
        feature["historical_region"] = COUNTY_TO_REGION.get(feature.get("properties", {}).get("name"))
    data["features"] = [feature for feature in data["features"] if feature.get("historical_region")]
    return data


@st.cache_data(ttl=900, show_spinner=False)
def fetch_weather(place_ids: tuple[str, ...]) -> dict:
    selected = [place_by_id(pid) for pid in place_ids]
    if not selected:
        return {}
    params = {
        "latitude": ",".join(str(place["lat"]) for place in selected),
        "longitude": ",".join(str(place["lon"]) for place in selected),
        "current": ",".join([
            "temperature_2m", "relative_humidity_2m", "apparent_temperature", "precipitation",
            "weather_code", "pressure_msl", "wind_speed_10m", "wind_direction_10m",
        ]),
        "daily": ",".join(["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_probability_max"]),
        "timezone": "Asia/Taipei",
        "wind_speed_unit": "ms",
        "forecast_days": "7",
    }
    url = OPEN_METEO_URL + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))
    rows = data if isinstance(data, list) else [data]
    return {place["id"]: row for place, row in zip(selected, rows)}


def places_for_region(region: str) -> list[dict]:
    if region == "all":
        return [place for place in PLACES if place["id"] in OVERVIEW_PLACE_IDS]
    return [place for place in PLACES if place["region"] == region]


def place_picker(ui: dict, lang: str, places: list[dict], selected_place_id: str = "") -> dict:
    options = places or PLACES
    ids = [place["id"] for place in options]
    index = ids.index(selected_place_id) if selected_place_id in ids else 0
    return st.sidebar.selectbox(ui["place"], options, index=index, format_func=lambda place: place_display_name(place, lang))


def render_place_detail(place: dict, weather: dict, lang: str, ui: dict) -> None:
    current = weather.get("current", {})
    daily = weather.get("daily", {})
    code = current.get("weather_code")
    temp = current.get("temperature_2m")
    min_temp = first(daily.get("temperature_2m_min"))
    max_temp = first(daily.get("temperature_2m_max"))
    rain = first(daily.get("precipitation_probability_max"))
    wind_speed = current.get("wind_speed_10m")
    wind_dir = current.get("wind_direction_10m")
    pressure = current.get("pressure_msl")

    st.markdown(
        f"""
        <div class="metric-card">
          <div class="name">{html.escape(place_display_name(place, lang))}</div>
          <div class="sub">{html.escape(ui["current_name"])}: {html.escape(current_place_name(place, lang))} / {html.escape(region_display_name(place["region"], lang))}</div>
          <div style="font-size:2.1rem;font-weight:800;color:#0f7585;">{weather_icon(code)} {html.escape(weather_text(code, lang))}</div>
          <div style="font-size:1.35rem;">{format_temp_range(min_temp, max_temp, lang)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns(3)
    col1.metric(ui["temperature"], format_temperature(temp, lang))
    col2.metric(ui["precipitation"], "--" if rain is None else f"{round(rain)}%")
    col3.metric("hPa", "--" if pressure is None else f"{round(pressure)}")
    st.write(f"**{wind_direction(wind_dir, lang)}** / 風力 {wind_force(wind_speed)} / {format_wind_speed(wind_speed)}")

    forecast_rows = forecast_table(daily, lang)
    if forecast_rows:
        st.subheader(ui["forecast"])
        st.dataframe(forecast_rows, hide_index=True, width="stretch")


def render_map(region: str, mode: str, lang: str, weather: dict) -> str:
    geojson = load_geojson()
    features = geojson["features"]
    shown_features = features if region == "all" else [f for f in features if f["historical_region"] == region]
    shown_places = places_for_region(region)
    bounds = bounds_for_features(shown_features)
    bounds = extend_bounds_with_places(bounds, shown_places)
    project = make_projector(bounds)
    region_colors = {r["id"]: r["color"] for r in REGIONS}
    paths = []
    for feature in features:
        historical_region = feature["historical_region"]
        visible = region == "all" or historical_region == region
        color = region_colors.get(historical_region, "#d6c38a")
        opacity = "0.82" if visible else "0.18"
        path = f'<path class="region-shape" d="{feature_path(feature, project)}" fill="{color}" fill-opacity="{opacity}" stroke="#eadfca" stroke-width="1"><title>{html.escape(feature["properties"]["name"])} / {html.escape(region_display_name(historical_region, lang))}</title></path>'
        if region == "all":
            href = html.escape(map_href(lang, historical_region, mode))
            path = f'<a class="map-link" href="{href}">{path}</a>'
        paths.append(path)

    labels = []
    for place in shown_places:
        x, y = project(place["lon"], place["lat"])
        value = marker_value(place, weather.get(place["id"], {}), mode, lang)
        label = place_display_name(place, lang)
        is_weather_mode = mode == "weather"
        width = max(70 if is_weather_mode else 64, min(132, 9 * max(len(label), len(value)) + 22))
        height = 46 if is_weather_mode else 40
        label_y = y - 17 if is_weather_mode else y - 16
        value_y = y + 5 if is_weather_mode else y - 2
        value_size = 22 if is_weather_mode else 13
        href = html.escape(map_href(lang, region, mode, place["id"]))
        labels.append(
            f"""
            <a class="map-link marker-link" href="{href}">
            <g>
              <circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#5a5748" opacity=".75" />
              <rect x="{x + 7:.1f}" y="{y - 34:.1f}" width="{width}" height="{height}" rx="7" fill="#fffdf4" opacity=".95" />
              <text x="{x + 12:.1f}" y="{label_y:.1f}" font-size="13" font-weight="700" fill="#2f2924">{html.escape(label)}</text>
              <text x="{x + 12:.1f}" y="{value_y:.1f}" font-size="{value_size}" font-weight="800" fill="#0f7585">{html.escape(value)}</text>
            </g>
            </a>
            """
        )

    region_labels = []
    if region == "all":
        for item in REGIONS:
            if item["id"] == "all":
                continue
            center = bounds_center(bounds_for_features([f for f in features if f["historical_region"] == item["id"]]))
            x, y = project(center[0], center[1])
            href = html.escape(map_href(lang, item["id"], mode))
            region_labels.append(f'<a class="map-link" href="{href}"><text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-size="24" font-weight="900" fill="#5d4a39" stroke="#fff4df" stroke-width="3" paint-order="stroke">{html.escape(region_display_name(item["id"], lang))}</text></a>')

    reset_label = {"ja": "初期", "zh": "重置", "en": "Reset", "nl": "Begin"}.get(lang, "Reset")
    title = "けふの台湾" if lang == "ja" else region_display_name(region, lang)

    return f"""
    <div id="weather-map-root" style="background:#eee7d5;border:1px solid #d4c4aa;border-radius:8px;overflow:hidden;position:relative;">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;padding:9px 12px;background:#f2ead8;border-bottom:1px solid #d4c4aa;font-weight:800;color:#3c281b;">
        <span>{html.escape(title)}</span>
        <span style="font-weight:500;color:#7f6b58;">g0v/twgeojson CC0</span>
      </div>
      <div class="map-controls" aria-label="map controls">
        <button id="zoom-in" type="button" aria-label="zoom in">+</button>
        <button id="zoom-out" type="button" aria-label="zoom out">-</button>
        <button id="zoom-reset" type="button" aria-label="reset">{html.escape(reset_label)}</button>
      </div>
      <svg id="weather-map-svg" viewBox="0 0 900 620" preserveAspectRatio="xMidYMid meet" style="display:block;width:100%;height:620px;background:#e3e1d1;touch-action:none;cursor:grab;">
        <defs>
          <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
            <path d="M 32 0 L 0 0 0 32" fill="none" stroke="#cfc9b6" stroke-width="1" opacity=".55"/>
          </pattern>
        </defs>
        <rect width="900" height="620" fill="url(#grid)"/>
        {''.join(paths)}
        {''.join(region_labels)}
        {''.join(labels)}
      </svg>
      <style>
        .map-controls {{
          position:absolute;
          right:12px;
          top:52px;
          display:flex;
          gap:6px;
          padding:7px;
          background:rgba(255,253,244,.92);
          border:1px solid rgba(84,55,36,.16);
          border-radius:8px;
          box-shadow:0 6px 18px rgba(45,28,18,.14);
          z-index:3;
        }}
        .map-controls button {{
          min-width:32px;
          height:30px;
          border:1px solid #d7cbb7;
          border-radius:6px;
          background:#fffdf8;
          color:#2f2924;
          font:700 14px system-ui, -apple-system, Segoe UI, sans-serif;
          cursor:pointer;
        }}
        .map-controls button:hover {{ background:#f2ead8; }}
        .map-link, .marker-link {{ cursor:pointer; text-decoration:none; }}
        .map-link:hover .region-shape {{ stroke:#473420; stroke-width:2; }}
        .marker-link:hover rect {{ stroke:#473420; stroke-width:1.5; }}
        #weather-map-svg.dragging {{ cursor:grabbing; }}
      </style>
    </div>
    """


def map_href(lang: str, region: str, mode: str, place_id: str = "") -> str:
    params = {"lang": lang, "region": region, "mode": mode}
    if place_id:
        params["place"] = place_id
    return "?" + urllib.parse.urlencode(params)


def feature_path(feature: dict, project) -> str:
    parts = []
    geom = feature["geometry"]
    polygons = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for polygon in polygons:
        for ring in polygon:
            projected = [project(point[0], point[1]) for point in ring]
            if not projected:
                continue
            start = projected[0]
            rest = " ".join(f"L{x:.1f},{y:.1f}" for x, y in projected[1:])
            parts.append(f"M{start[0]:.1f},{start[1]:.1f} {rest} Z")
    return " ".join(parts)


def bounds_for_features(features: list[dict]) -> tuple[float, float, float, float]:
    lons: list[float] = []
    lats: list[float] = []
    for feature in features:
        geom = feature["geometry"]
        polygons = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for polygon in polygons:
            for ring in polygon:
                for point in ring:
                    lon, lat = point[0], point[1]
                    lons.append(lon)
                    lats.append(lat)
    if not lons:
        return (119.2, 21.8, 122.2, 25.4)
    return (min(lons), min(lats), max(lons), max(lats))


def extend_bounds_with_places(bounds: tuple[float, float, float, float], places: list[dict]) -> tuple[float, float, float, float]:
    min_lon, min_lat, max_lon, max_lat = bounds
    for place in places:
        min_lon = min(min_lon, place["lon"])
        max_lon = max(max_lon, place["lon"])
        min_lat = min(min_lat, place["lat"])
        max_lat = max(max_lat, place["lat"])
    return (min_lon, min_lat, max_lon, max_lat)


def bounds_center(bounds: tuple[float, float, float, float]) -> tuple[float, float]:
    return ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)


def make_projector(bounds: tuple[float, float, float, float]):
    min_lon, min_lat, max_lon, max_lat = bounds
    pad = 42
    width = 900
    height = 620
    lon_span = max(max_lon - min_lon, 0.1)
    lat_span = max(max_lat - min_lat, 0.1)
    scale = min((width - pad * 2) / lon_span, (height - pad * 2) / lat_span)
    x_extra = (width - lon_span * scale) / 2
    y_extra = (height - lat_span * scale) / 2

    def project(lon: float, lat: float) -> tuple[float, float]:
        return (x_extra + (lon - min_lon) * scale, y_extra + (max_lat - lat) * scale)

    return project


def marker_value(place: dict, weather: dict, mode: str, lang: str) -> str:
    current = weather.get("current", {})
    daily = weather.get("daily", {})
    if mode == "temperature":
        return format_temp_range(first(daily.get("temperature_2m_min")), first(daily.get("temperature_2m_max")), lang)
    if mode == "precipitation":
        rain = first(daily.get("precipitation_probability_max"))
        return "--" if rain is None else f"{round(rain)}%"
    return weather_icon(current.get("weather_code"))


def build_bulletin(lang: str, region: str, selected_place: dict, selected_weather: dict, all_weather: dict) -> tuple[str, str]:
    rows = [(selected_place, selected_weather)] if selected_weather.get("current") else []
    if not rows:
        return ("天気データを取得すると、読み上げ原稿を作成します。", "天気データを取得すると、読み上げ原稿を作成します。")
    time_text = weather_time_text(selected_weather.get("current", {}).get("time"), lang)
    if lang == "zh":
        lines = [f"本站發布的{time_text}天氣通報。", f"{place_display_name(selected_place, lang)}目前天氣如下。", ""]
        speech = list(lines)
        for place, weather in rows:
            line = chinese_bulletin_line(place, weather)
            lines.append(line)
            speech.append(line)
        lines += ["", "以上。"]
        speech += ["", "以上。"]
    elif lang == "en":
        lines = [f"Weather bulletin issued by this site at {time_text}.", f"Current weather for {place_display_name(selected_place, lang)}:", ""]
        speech = [f"Weather bulletin issued by this site at {time_text}.", f"The current weather for {place_display_name(selected_place, lang)} is as follows.", ""]
        for place, weather in rows:
            lines.append(english_bulletin_line(place, weather, False))
            speech.append(english_bulletin_line(place, weather, True))
        lines += ["", "End of bulletin."]
        speech += ["", "End of bulletin."]
    elif lang == "nl":
        lines = [f"Weerbericht uitgegeven door deze site om {time_text}.", f"Actueel weer voor {place_display_name(selected_place, lang)}:", ""]
        speech = [f"Weerbericht uitgegeven door deze site om {time_text}.", f"Het actuele weer voor {place_display_name(selected_place, lang)} is als volgt.", ""]
        for place, weather in rows:
            lines.append(dutch_bulletin_line(place, weather, False))
            speech.append(dutch_bulletin_line(place, weather, True))
        lines += ["", "Einde van het bericht."]
        speech += ["", "Einde van het bericht."]
    else:
        lines = [f"本サイト発表の{time_text}の気象通報です。", f"{selected_place['historical']}（{selected_place['reading']}）のけふの天気は、", ""]
        speech = [f"ほんさいとはっぴょうの、{weather_time_speech(selected_weather.get('current', {}).get('time'))}の、きしょうつうほうです。", f"{selected_place['reading']}の、げんざいのてんきは、", ""]
        for place, weather in rows:
            lines.append(japanese_bulletin_line(place, weather, False))
            speech.append(japanese_bulletin_line(place, weather, True))
        lines += ["", "以上です。"]
        speech += ["", "いじょうです。"]
    return ("\n".join(lines), "\n".join(speech))


def japanese_bulletin_line(place: dict, weather: dict, speech: bool) -> str:
    current = weather.get("current", {})
    force = wind_force(current.get("wind_speed_10m"))
    temp = current.get("temperature_2m")
    if speech:
        return f"{place['reading']}は、{wind_direction_speech(current.get('wind_direction_10m'))}のかぜ、ふうりょく{force}、{weather_text_speech(current.get('weather_code'))}、{pressure_speech(current.get('pressure_msl'), 'ja')}、{round_or_unknown(temp)}ど。"
    return f"{place['historical']}（{place['reading']}）は、{wind_direction(current.get('wind_direction_10m'), 'ja')}の風、風力{force}、{weather_text(current.get('weather_code'), 'ja')}、{format_pressure_full(current.get('pressure_msl'))}、{format_temperature(temp, 'ja')}。"


def chinese_bulletin_line(place: dict, weather: dict) -> str:
    current = weather.get("current", {})
    return f"{place_display_name(place, 'zh')}，{wind_direction(current.get('wind_direction_10m'), 'zh')}風，風力{wind_force(current.get('wind_speed_10m'))}，{weather_text(current.get('weather_code'), 'zh')}，{pressure_speech(current.get('pressure_msl'), 'zh')}，{format_temperature(current.get('temperature_2m'), 'zh')}。"


def english_bulletin_line(place: dict, weather: dict, speech: bool) -> str:
    current = weather.get("current", {})
    if speech:
        return f"{place_display_name(place, 'en')}. Wind, {wind_direction_speech(current.get('wind_direction_10m'), 'en')}. Wind force, {wind_force(current.get('wind_speed_10m'))}. Weather, {weather_text(current.get('weather_code'), 'en')}. Pressure, {pressure_speech(current.get('pressure_msl'), 'en')}. Temperature, {format_temperature_speech(current.get('temperature_2m'), 'en')}."
    return f"{place_display_name(place, 'en')}: {wind_direction(current.get('wind_direction_10m'), 'en')}, wind force {wind_force(current.get('wind_speed_10m'))}, {weather_text(current.get('weather_code'), 'en')}, {format_pressure_full(current.get('pressure_msl'))}, {format_temperature_speech(current.get('temperature_2m'), 'en')}."


def dutch_bulletin_line(place: dict, weather: dict, speech: bool) -> str:
    current = weather.get("current", {})
    if speech:
        return f"{place_display_name(place, 'nl')}. Wind, {wind_direction_speech(current.get('wind_direction_10m'), 'nl')}. Windkracht, {wind_force(current.get('wind_speed_10m'))}. Weer, {weather_text(current.get('weather_code'), 'nl')}. Luchtdruk, {pressure_speech(current.get('pressure_msl'), 'nl')}. Temperatuur, {format_temperature_speech(current.get('temperature_2m'), 'nl')}."
    return f"{place_display_name(place, 'nl')}: {wind_direction(current.get('wind_direction_10m'), 'nl')}, windkracht {wind_force(current.get('wind_speed_10m'))}, {weather_text(current.get('weather_code'), 'nl')}, {format_pressure_full(current.get('pressure_msl'))}, {format_temperature_speech(current.get('temperature_2m'), 'nl')}."


@st.cache_data(ttl=3600, show_spinner=False)
def create_tts_mp3(text: str, voice: str) -> bytes:
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError("edge-tts がインストールされていません。requirements.txt を入れてください。") from exc

    async def run() -> bytes:
        communicate = edge_tts.Communicate(text, voice)
        with tempfile.TemporaryDirectory(prefix="taiwan-weather-tts-") as temp_dir:
            path = Path(temp_dir) / "speech.mp3"
            await communicate.save(str(path))
            return path.read_bytes()

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(run())
    finally:
        loop.close()


def forecast_table(daily: dict, lang: str) -> list[dict]:
    dates = daily.get("time") or []
    rows = []
    for idx, date in enumerate(dates):
        rows.append({
            "日付": date,
            "天気": f"{weather_icon(value_at(daily.get('weather_code'), idx))} {weather_text(value_at(daily.get('weather_code'), idx), lang)}",
            "気温": format_temp_range(value_at(daily.get("temperature_2m_min"), idx), value_at(daily.get("temperature_2m_max"), idx), lang),
            "降水": "--" if value_at(daily.get("precipitation_probability_max"), idx) is None else f"{round(value_at(daily.get('precipitation_probability_max'), idx))}%",
        })
    return rows


def place_by_id(place_id: str) -> dict:
    return next(place for place in PLACES if place["id"] == place_id)


def first(values):
    if isinstance(values, list) and values:
        return values[0]
    return None


def value_at(values, index):
    if isinstance(values, list) and index < len(values):
        return values[index]
    return None


def weather_kind(code) -> str:
    try:
        value = int(code)
    except (TypeError, ValueError):
        return "unknown"
    if value in (0, 1):
        return "clear"
    if value == 2:
        return "partly"
    if value == 3:
        return "cloudy"
    if value in (45, 48):
        return "fog"
    if value in (51, 53, 55, 56, 57):
        return "drizzle"
    if value in (61, 63, 65, 66, 67, 80, 81, 82):
        return "rain"
    if value in (71, 73, 75, 77, 85, 86):
        return "snow"
    if value in (95, 96, 99):
        return "thunder"
    return "unknown"


def weather_text(code, lang: str) -> str:
    if lang == "ja":
        try:
            return WEATHER_CODE_JA.get(int(code), "天気不明")
        except (TypeError, ValueError):
            return "天気不明"
    return WEATHER_KIND_TEXT[lang][weather_kind(code)]


def weather_text_speech(code) -> str:
    reading = {
        "clear": "はれ",
        "partly": "うすぐもり",
        "cloudy": "くもり",
        "fog": "きり",
        "drizzle": "きりさめ",
        "rain": "あめ",
        "snow": "ゆき",
        "thunder": "らいう",
        "unknown": "てんきふめい",
    }
    return reading[weather_kind(code)]


def weather_icon(code) -> str:
    return {"clear": "☀", "partly": "⛅", "cloudy": "☁", "fog": "≋", "drizzle": "☂", "rain": "☔", "snow": "❄", "thunder": "⚡", "unknown": "？"}[weather_kind(code)]


def wind_direction(degrees, lang: str) -> str:
    if degrees is None:
        return "不明"
    index = round(float(degrees) / 22.5) % 16
    return WIND_DIRECTIONS[lang][index]


def wind_direction_speech(degrees, lang: str = "ja") -> str:
    if degrees is None:
        return "ふめい" if lang == "ja" else "unknown"
    index = round(float(degrees) / 22.5) % 16
    if lang == "ja":
        readings = ["きた", "ほくほくとう", "ほくとう", "とうほくとう", "ひがし", "とうなんとう", "なんとう", "なんなんとう", "みなみ", "なんなんせい", "なんせい", "せいなんせい", "にし", "せいほくせい", "ほくせい", "ほくほくせい"]
        return readings[index]
    if lang == "nl":
        readings = ["noord", "noordnoordoost", "noordoost", "oostnoordoost", "oost", "oostzuidoost", "zuidoost", "zuidzuidoost", "zuid", "zuidzuidwest", "zuidwest", "westzuidwest", "west", "westnoordwest", "noordwest", "noordnoordwest"]
        return f"{readings[index]}, {round(float(degrees))} graden"
    readings = ["north", "north-northeast", "northeast", "east-northeast", "east", "east-southeast", "southeast", "south-southeast", "south", "south-southwest", "southwest", "west-southwest", "west", "west-northwest", "northwest", "north-northwest"]
    return f"{readings[index]}, {round(float(degrees))} degrees"


def wind_force(speed) -> int:
    if speed is None:
        return 0
    thresholds = [0.2, 1.5, 3.3, 5.4, 7.9, 10.7, 13.8, 17.1, 20.7, 24.4, 28.4, 32.6]
    value = float(speed)
    for index, threshold in enumerate(thresholds):
        if value <= threshold:
            return index
    return 12


def format_wind_speed(speed) -> str:
    if speed is None:
        return "--"
    return f"{round(float(speed), 1)} m/s"


def format_temperature(value, lang: str) -> str:
    if value is None:
        return "--"
    temp = float(value)
    if lang == "en":
        return f"{round(temp * 9 / 5 + 32)}℉"
    return f"{round(temp)}℃"


def format_temperature_speech(value, lang: str) -> str:
    if value is None:
        return "temperature unknown"
    if lang == "en":
        return f"{round(float(value) * 9 / 5 + 32)} degrees Fahrenheit"
    if lang == "nl":
        return f"{round(float(value))} graden Celsius"
    return f"攝氏{round(float(value))}度"


def format_temp_range(min_value, max_value, lang: str) -> str:
    if min_value is None or max_value is None:
        return "--"
    if lang == "en":
        return f"{round(float(min_value) * 9 / 5 + 32)}-{round(float(max_value) * 9 / 5 + 32)}℉"
    return f"{round(float(min_value))}-{round(float(max_value))}℃"


def format_pressure_full(value) -> str:
    if value is None:
        return "気圧不明"
    return f"{round(float(value))} hPa"


def pressure_speech(value, lang: str) -> str:
    if value is None:
        return {"ja": "きあつふめい", "zh": "氣壓不明", "nl": "luchtdruk onbekend"}.get(lang, "pressure unknown")
    pressure = round(float(value))
    if lang == "ja":
        return f"{pressure}へくとぱすかる"
    if lang == "zh":
        return f"{pressure}百帕"
    if lang == "nl":
        return f"{pressure} hectopascal"
    return f"{pressure} hectopascals"


def round_or_unknown(value) -> str:
    return "ふめい" if value is None else str(round(float(value)))


def weather_time_text(value: str | None, lang: str) -> str:
    if not value:
        return "時刻不明"
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return value
    historical_year = dt.year - 1911
    if lang == "ja":
        return f"大正{historical_year}年{dt.month}月{dt.day}日{dt.hour}時{dt.minute:02d}分"
    if lang == "zh":
        return f"民國{historical_year}年{dt.month}月{dt.day}日{dt.hour}時{dt.minute:02d}分"
    return dt.strftime("%Y-%m-%d %H:%M")


def weather_time_speech(value: str | None) -> str:
    if not value:
        return "じこくふめい"
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return value
    return f"たいしょう{dt.year - 1911}ねん{dt.month}がつ{dt.day}にち{dt.hour}じ{dt.minute}ふん"


def region_display_name(region_id: str, lang: str) -> str:
    if region_id == "all":
        return {"ja": "全域", "zh": "全域", "en": "All", "nl": "Alle"}[lang]
    if lang == "zh":
        return to_display_chinese(region_id)
    if lang in ("en", "nl"):
        return ROMAJI_REGION_NAMES.get(region_id, region_id)
    return region_id


def place_display_name(place: dict, lang: str) -> str:
    if lang == "zh":
        return to_display_chinese(place["historical"])
    if lang in ("en", "nl"):
        return ROMAJI_PLACE_NAMES.get(place["id"], place["reading"])
    return place["historical"]


def current_place_name(place: dict, lang: str) -> str:
    if lang == "ja":
        return place["current"]
    return to_display_chinese(place["current"])


def to_display_chinese(value: str) -> str:
    return (
        str(value)
        .replace("台湾", "臺灣")
        .replace("台", "臺")
        .replace("庁", "廳")
        .replace("営", "營")
        .replace("恒", "恆")
        .replace("穂", "穗")
        .replace("焼", "燒")
    )


def safe_filename(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in value)[:48] or "weather"


if __name__ == "__main__":
    main()
