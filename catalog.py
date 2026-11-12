"""
Fashion catalog, skeleton-type filtering, color/vibe matching,
weather-aware layering, and affiliate link generation for Oshi-Coord AI.
"""

from __future__ import annotations

import math
import os
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple


# Color palette reference for RGB -> color family & Japanese label mapping
COLOR_PALETTE: List[Dict[str, Any]] = [
    {"id": "black", "name": "ブラック", "rgb": (24, 24, 28)},
    {"id": "white", "name": "ホワイト", "rgb": (245, 245, 247)},
    {"id": "ivory", "name": "アイボリー", "rgb": (242, 235, 220)},
    {"id": "gray", "name": "グレー", "rgb": (138, 142, 150)},
    {"id": "beige", "name": "ベージュ", "rgb": (210, 185, 155)},
    {"id": "brown", "name": "ブラウン", "rgb": (115, 75, 50)},
    {"id": "navy", "name": "ネイビー", "rgb": (30, 48, 88)},
    {"id": "blue", "name": "ブルー", "rgb": (58, 125, 215)},
    {"id": "sax", "name": "サックスブルー", "rgb": (145, 195, 235)},
    {"id": "red", "name": "レッド", "rgb": (205, 45, 60)},
    {"id": "pink", "name": "ピンク", "rgb": (240, 155, 185)},
    {"id": "purple", "name": "パープル", "rgb": (145, 95, 200)},
    {"id": "lavender", "name": "ラベンダー", "rgb": (195, 170, 235)},
    {"id": "green", "name": "グリーン", "rgb": (45, 135, 85)},
    {"id": "mint", "name": "ミント", "rgb": (145, 220, 195)},
    {"id": "yellow", "name": "イエロー", "rgb": (240, 205, 65)},
    {"id": "orange", "name": "オレンジ", "rgb": (235, 125, 50)},
]

# Skeleton type rules (骨格診断フィルター定義)
SKELETON_RULES: Dict[str, Dict[str, Any]] = {
    "straight": {
        "label": "骨格ストレート",
        "good_traits": ["Iラインシルエット", "ジャストサイズ", "ハリのある素材", "Vネック・スクエアネック"],
        "excluded_traits": ["過度なフリル・ギャザー", "極端なオーバーサイズ", "ペラペラした薄手シフォン"],
        "description": "立体的でメリハリのあるボディラインを活かす、シンプルでクラス感のあるジャストサイズ・Iライン中心に選定。",
    },
    "wave": {
        "label": "骨格ウェーブ",
        "good_traits": ["ハイウエスト", "シフォン・レース・モヘア", "コンパクトなトップス", "Xライン・Aライン"],
        "excluded_traits": ["重たいマキシ丈・厚手レザー", "ローウエスト", "硬すぎるオーバーサイズ"],
        "description": "華奢な上半身を華やかに見せ、重心を上げるハイウエスト＆柔らかな揺れ感素材を中心に選定。",
    },
    "natural": {
        "label": "骨格ナチュラル",
        "good_traits": ["オーバーサイズ・ビッグシルエット", "リネン・デニム・ざっくりニット", "マキシ丈・ワイドパンツ", "ラフな抜け感"],
        "excluded_traits": ["タイトすぎるミニ丈", "ぴたっとしたリブニット", "甘すぎる小花柄"],
        "description": "フレーム感のあるスタイリッシュな骨格を活かす、ゆったりとしたリラックスシルエット＆天然・風合い素材を選定。",
    },
}

VIBE_LABELS: Dict[str, str] = {
    "cool_mode": "クール・モード",
    "sweet_girly": "甘め・ガーリー",
    "street_casual": "ストリート・カジュアル",
    "elegant_classic": "上品・フェミニン",
    "subculture_cyber": "サブカル・サイバー",
}

# Curated MVP item catalog (SHEIN / ZOZOTOWN)
CATALOG_ITEMS: List[Dict[str, Any]] = [
    # --- TOPS ---
    {
        "id": "top-01",
        "name": "スクエアネック ハリ感リブニットトップス",
        "category": "tops",
        "category_label": "トップス",
        "ec_platform": "ZOZOTOWN",
        "price": 3490,
        "colors": ["black", "white", "navy", "red", "purple"],
        "vibes": ["cool_mode", "elegant_classic"],
        "materials": ["ハイゲージニット", "レーヨン混"],
        "skeleton_good": ["straight"],
        "skeleton_note": "デコルテをすっきり見せるスクエアネック＆ジャスト丈で着痩せ効果抜群。",
        "temp_min": 10,
        "temp_max": 24,
        "search_keyword": "スクエアネック リブニット",
    },
    {
        "id": "top-02",
        "name": "シアーリボン タイ付きシフォンブラウス",
        "category": "tops",
        "category_label": "トップス",
        "ec_platform": "SHEIN",
        "price": 1850,
        "colors": ["white", "ivory", "pink", "lavender", "sax", "black"],
        "vibes": ["sweet_girly", "elegant_classic"],
        "materials": ["シフォン", "オーガンジー"],
        "skeleton_good": ["wave"],
        "skeleton_note": "軽やかな透け感と胸元のリボンが華奢な上半身を華やかに演出。",
        "temp_min": 14,
        "temp_max": 28,
        "search_keyword": "リボン シフォン ブラウス",
    },
    {
        "id": "top-03",
        "name": "オーバーサイズ グラフィックロゴスウェット",
        "category": "tops",
        "category_label": "トップス",
        "gender": ["women", "men"],
        "ec_platform": "SHEIN",
        "price": 2180,
        "colors": ["black", "gray", "white", "navy", "green", "purple"],
        "vibes": ["street_casual", "subculture_cyber", "cool_mode"],
        "materials": ["裏毛コットン", "スウェット"],
        "skeleton_good": ["natural"],
        "skeleton_note": "ドロップショルダーとゆったり身幅が骨格ナチュラルのフレーム感にマッチ。",
        "temp_min": 8,
        "temp_max": 22,
        "search_keyword": "オーバーサイズ ロゴ スウェット",
    },
    {
        "id": "top-04",
        "name": "Vネック ベーシックコットンシャツ",
        "category": "tops",
        "category_label": "トップス",
        "gender": ["women", "men"],
        "ec_platform": "ZOZOTOWN",
        "price": 3960,
        "colors": ["white", "sax", "beige", "navy", "black"],
        "vibes": ["cool_mode", "elegant_classic", "street_casual"],
        "materials": ["コットンポプリン", "タイプライター"],
        "skeleton_good": ["straight", "natural"],
        "skeleton_note": "程よいハリ感と縦ラインを強調する襟元で、きちんと感と推し色を両立。",
        "temp_min": 15,
        "temp_max": 30,
        "search_keyword": "ベーシック ハリ感 シャツ",
    },
    {
        "id": "top-05",
        "name": "クロップド丈 モヘアタッチカーディガン",
        "category": "tops",
        "category_label": "トップス",
        "ec_platform": "SHEIN",
        "price": 2290,
        "colors": ["pink", "lavender", "ivory", "mint", "yellow", "blue"],
        "vibes": ["sweet_girly", "subculture_cyber"],
        "materials": ["モヘア風ニット", "ふわふわシャギー"],
        "skeleton_good": ["wave"],
        "skeleton_note": "ショート丈でウエスト位置を高く見せ、脚長効果を引き出します。",
        "temp_min": 8,
        "temp_max": 20,
        "search_keyword": "クロップド モヘア カーディガン",
    },
    {
        "id": "top-06",
        "name": "ダメージ風 ルーズシルエットニット",
        "category": "tops",
        "category_label": "トップス",
        "ec_platform": "ZOZOTOWN",
        "price": 4400,
        "colors": ["black", "red", "purple", "green", "orange", "gray"],
        "vibes": ["subculture_cyber", "street_casual", "cool_mode"],
        "materials": ["ざっくりローゲージニット"],
        "skeleton_good": ["natural"],
        "skeleton_note": "凹凸のあるざっくり編み地とルーズ感が重心を下げてこなれた印象に。",
        "temp_min": 5,
        "temp_max": 18,
        "search_keyword": "ルーズ ローゲージ ニット",
    },
    {
        "id": "top-07",
        "name": "サテンパイピング 半袖コンパクトポロ",
        "category": "tops",
        "category_label": "トップス",
        "ec_platform": "SHEIN",
        "price": 1580,
        "colors": ["white", "black", "navy", "pink", "mint", "yellow"],
        "vibes": ["street_casual", "sweet_girly", "cool_mode"],
        "materials": ["スムースコットン", "サテン"],
        "skeleton_good": ["straight", "wave"],
        "skeleton_note": "すっきりした肩周りと適度な厚みで夏〜初秋まで快適に着こなせます。",
        "temp_min": 21,
        "temp_max": 36,
        "search_keyword": "コンパクト ポロシャツ",
    },

    # --- BOTTOMS ---
    {
        "id": "bot-01",
        "name": "センタープレス ハイウエストストレートスラックス",
        "category": "bottoms",
        "category_label": "ボトムス",
        "gender": ["women", "men"],
        "ec_platform": "ZOZOTOWN",
        "price": 4290,
        "colors": ["black", "ivory", "beige", "navy", "gray", "brown"],
        "vibes": ["cool_mode", "elegant_classic"],
        "materials": ["ツイル", "ポリエステル混"],
        "skeleton_good": ["straight"],
        "skeleton_note": "センタープレスがIラインを強調し、腰回りをすっきり見せる美脚パンツ。",
        "temp_min": 5,
        "temp_max": 30,
        "search_keyword": "センタープレス ストレートスラックス",
    },
    {
        "id": "bot-02",
        "name": "ハイウエスト チュールプリーツロングスカート",
        "category": "bottoms",
        "category_label": "ボトムス",
        "ec_platform": "SHEIN",
        "price": 2150,
        "colors": ["black", "ivory", "pink", "lavender", "sax", "gray"],
        "vibes": ["sweet_girly", "elegant_classic"],
        "materials": ["チュール", "シフォン"],
        "skeleton_good": ["wave"],
        "skeleton_note": "柔らかな揺れ感とハイウエスト切替で、骨格ウェーブの曲線美を最大限に引き立てます。",
        "temp_min": 10,
        "temp_max": 30,
        "search_keyword": "ハイウエスト チュールプリーツスカート",
    },
    {
        "id": "bot-03",
        "name": "ワイドレッグ カーゴデニムパンツ",
        "category": "bottoms",
        "category_label": "ボトムス",
        "gender": ["women", "men"],
        "ec_platform": "SHEIN",
        "price": 2890,
        "colors": ["blue", "sax", "black", "gray", "beige"],
        "vibes": ["street_casual", "subculture_cyber", "cool_mode"],
        "materials": ["ウォッシュドデニム", "コットンツイル"],
        "skeleton_good": ["natural"],
        "skeleton_note": "ボリュームのあるワイドシルエットが骨感をカバーし、今っぽいストリート感を演出。",
        "temp_min": 5,
        "temp_max": 30,
        "search_keyword": "ワイド カーゴデニム",
    },
    {
        "id": "bot-04",
        "name": "ハイウエスト マーメイドフレアスカート",
        "category": "bottoms",
        "category_label": "ボトムス",
        "ec_platform": "ZOZOTOWN",
        "price": 3850,
        "colors": ["black", "brown", "ivory", "navy", "red", "purple"],
        "vibes": ["elegant_classic", "sweet_girly", "cool_mode"],
        "materials": ["落ち感サテン", "ストレッチツイル"],
        "skeleton_good": ["wave", "straight"],
        "skeleton_note": "腰回りにフィットしつつ裾に向かって広がるラインがバランス良く決まります。",
        "temp_min": 8,
        "temp_max": 28,
        "search_keyword": "マーメイドスカート",
    },
    {
        "id": "bot-05",
        "name": "プリーツ ミニスカート（インナーパンツ付き）",
        "category": "bottoms",
        "category_label": "ボトムス",
        "ec_platform": "SHEIN",
        "price": 1680,
        "colors": ["black", "gray", "navy", "pink", "red", "white"],
        "vibes": ["sweet_girly", "subculture_cyber", "street_casual"],
        "materials": ["TRツイル", "プリーツ"],
        "skeleton_good": ["wave", "straight"],
        "skeleton_note": "膝上丈で重心を上げ、推し活・ライブ参戦にも動きやすいインナーパンツ仕様。",
        "temp_min": 14,
        "temp_max": 35,
        "search_keyword": "プリーツ ミニスカート",
    },
    {
        "id": "bot-06",
        "name": "リネンブレンド マキシフレアスカート",
        "category": "bottoms",
        "category_label": "ボトムス",
        "ec_platform": "ZOZOTOWN",
        "price": 4180,
        "colors": ["beige", "ivory", "green", "mint", "orange", "black"],
        "vibes": ["elegant_classic", "street_casual"],
        "materials": ["リネン混", "ナチュラルコットン"],
        "skeleton_good": ["natural"],
        "skeleton_note": "たっぷりとしたマキシ丈とドライな風合いが骨格ナチュラルの得意領域。",
        "temp_min": 15,
        "temp_max": 35,
        "search_keyword": "リネン マキシフレアスカート",
    },

    # --- OUTERWEAR ---
    {
        "id": "out-01",
        "name": "テーラード ミドル丈ダブルジャケット",
        "category": "outer",
        "category_label": "アウター",
        "ec_platform": "ZOZOTOWN",
        "price": 5940,
        "colors": ["black", "navy", "beige", "brown", "gray"],
        "vibes": ["cool_mode", "elegant_classic"],
        "materials": ["スーツ地", "ハリ感ツイル"],
        "skeleton_good": ["straight"],
        "skeleton_note": "かっちりとした肩線と直線的なラペルが骨格ストレートの魅力を最大化。",
        "temp_min": 8,
        "temp_max": 19,
        "search_keyword": "テーラード ダブルジャケット",
    },
    {
        "id": "out-02",
        "name": "ショート丈 フェイクファーノーカラージャケット",
        "category": "outer",
        "category_label": "アウター",
        "ec_platform": "SHEIN",
        "price": 3480,
        "colors": ["ivory", "white", "pink", "lavender", "black"],
        "vibes": ["sweet_girly", "elegant_classic"],
        "materials": ["フェイクファー", "ボア"],
        "skeleton_good": ["wave"],
        "skeleton_note": "視線を上に集めるショート丈×ふわふわ素材で着膨れせずスタイルアップ。",
        "temp_min": -2,
        "temp_max": 16,
        "search_keyword": "ショート丈 ノーカラー ファージャケット",
    },
    {
        "id": "out-03",
        "name": "オーバーサイズ スタンドカラーブルゾン（撥水）",
        "category": "outer",
        "category_label": "アウター",
        "gender": ["women", "men"],
        "ec_platform": "SHEIN",
        "price": 3290,
        "colors": ["black", "beige", "green", "navy", "purple"],
        "vibes": ["street_casual", "subculture_cyber", "cool_mode"],
        "materials": ["ナイロンタフタ", "撥水ポリエステル"],
        "skeleton_good": ["natural", "straight"],
        "skeleton_note": "風を通しにくく雨の日も安心な撥水素材。ラフに羽織れるサイズ感。",
        "temp_min": 5,
        "temp_max": 19,
        "search_keyword": "オーバーサイズ スタンドカラー ブルゾン",
    },
    {
        "id": "out-04",
        "name": "ビッグシルエット ウールタッチチェスターコート",
        "category": "outer",
        "category_label": "アウター",
        "gender": ["women", "men"],
        "ec_platform": "ZOZOTOWN",
        "price": 6930,
        "colors": ["black", "brown", "beige", "navy", "gray"],
        "vibes": ["cool_mode", "elegant_classic", "street_casual"],
        "materials": ["メルトン", "ウールタッチ"],
        "skeleton_good": ["natural", "straight"],
        "skeleton_note": "真冬〜肌寒い日に対応。縦長シルエットで大人っぽくまとまります。",
        "temp_min": -5,
        "temp_max": 13,
        "search_keyword": "チェスターコート",
    },

    # --- SHOES ---
    {
        "id": "acc-01",
        "name": "スクエアトゥ ポインテッドショートブーツ",
        "category": "shoes",
        "category_label": "シューズ",
        "gender": ["women"],
        "ec_platform": "ZOZOTOWN",
        "price": 3990,
        "colors": ["black", "ivory", "brown"],
        "vibes": ["cool_mode", "elegant_classic", "sweet_girly"],
        "materials": ["エコレザー"],
        "skeleton_good": ["straight", "wave"],
        "skeleton_note": "足首をすっきり見せ、全体のコーデをスマートに引き締める万能ブーツ。",
        "temp_min": -5,
        "temp_max": 23,
        "search_keyword": "スクエアトゥ ショートブーツ",
    },
    {
        "id": "acc-02",
        "name": "厚底 トラックソールスニーカー",
        "category": "shoes",
        "category_label": "シューズ",
        "gender": ["women", "men"],
        "ec_platform": "SHEIN",
        "price": 2650,
        "colors": ["white", "black", "purple", "pink", "blue"],
        "vibes": ["street_casual", "subculture_cyber", "sweet_girly"],
        "materials": ["メッシュ", "合成皮革"],
        "skeleton_good": ["natural", "wave", "straight"],
        "skeleton_note": "足元に程よいボリュームを出しつつ歩きやすさも確保。ライブ遠征にも最適。",
        "temp_min": -5,
        "temp_max": 36,
        "search_keyword": "厚底 スニーカー",
    },
    {
        "id": "men-shoe-01",
        "name": "クリーン レザータッチローファー",
        "category": "shoes",
        "category_label": "シューズ",
        "gender": ["men", "women"],
        "ec_platform": "ZOZOTOWN",
        "price": 4400,
        "colors": ["black", "brown", "navy", "ivory"],
        "vibes": ["cool_mode", "elegant_classic"],
        "materials": ["シンセティックレザー"],
        "skeleton_good": ["straight", "wave", "natural"],
        "skeleton_note": "きれいめにもカジュアルにも合わせやすく、足元を上品にまとめる定番シューズ。",
        "temp_min": -5,
        "temp_max": 35,
        "search_keyword": "コインローファー",
    },

    # --- ACCESSORIES ---
    {
        "id": "acc-03",
        "name": "推し色チェーン ミニショルダーバッグ",
        "category": "accessories",
        "category_label": "小物",
        "gender": ["women"],
        "ec_platform": "SHEIN",
        "price": 1280,
        "colors": ["black", "white", "pink", "lavender", "red", "blue", "yellow", "green", "orange"],
        "vibes": ["sweet_girly", "cool_mode", "subculture_cyber", "elegant_classic"],
        "materials": ["キルティングPU", "メタルチェーン"],
        "skeleton_good": ["straight", "wave", "natural"],
        "skeleton_note": "コーデに「推しカラー」をピンポイントで差し込める万能アイテム。",
        "temp_min": -10,
        "temp_max": 40,
        "search_keyword": "ミニ ショルダーバッグ",
    },
    # --- MEN'S DEDICATED ITEMS ---
    {
        "id": "men-top-01",
        "name": "ドレープ サテンオープンカラーシャツ",
        "category": "tops",
        "category_label": "トップス",
        "gender": ["men"],
        "ec_platform": "ZOZOTOWN",
        "price": 3980,
        "colors": ["black", "white", "navy", "purple", "sax", "lavender", "pink"],
        "vibes": ["cool_mode", "sweet_girly", "elegant_classic", "subculture_cyber"],
        "materials": ["落ち感サテン", "とろみポリ"],
        "skeleton_good": ["wave", "straight"],
        "skeleton_note": "柔らかなドレープ感と程よい開きで、華奢見えしやすい骨格ウェーブの男性にも好相性。",
        "temp_min": 15,
        "temp_max": 32,
        "search_keyword": "オープンカラー サテンシャツ",
    },
    {
        "id": "men-top-02",
        "name": "ジャストフィット ハイゲージクルーネックニット",
        "category": "tops",
        "category_label": "トップス",
        "gender": ["men"],
        "ec_platform": "ZOZOTOWN",
        "price": 3850,
        "colors": ["black", "white", "navy", "red", "green", "beige"],
        "vibes": ["cool_mode", "elegant_classic"],
        "materials": ["ハイゲージニット", "コットン混"],
        "skeleton_good": ["straight", "wave"],
        "skeleton_note": "装飾を抑えたクリーンな表面感とジャストサイズで、上半身をすっきり見せます。",
        "temp_min": 8,
        "temp_max": 22,
        "search_keyword": "ハイゲージ クルーネックニット",
    },
    {
        "id": "men-bot-01",
        "name": "テーパード クリーンチノパンツ",
        "category": "bottoms",
        "category_label": "ボトムス",
        "gender": ["men"],
        "ec_platform": "ZOZOTOWN",
        "price": 4100,
        "colors": ["black", "beige", "navy", "gray", "ivory", "brown"],
        "vibes": ["cool_mode", "elegant_classic", "street_casual", "sweet_girly"],
        "materials": ["ストレッチツイル", "コットン"],
        "skeleton_good": ["wave", "straight"],
        "skeleton_note": "足首に向かって細くなるテーパードラインが脚をすっきり長く見せます。",
        "temp_min": 5,
        "temp_max": 32,
        "search_keyword": "テーパード チノパンツ",
    },
    {
        "id": "men-out-01",
        "name": "ショート丈 スエードタッチジップブルゾン",
        "category": "outer",
        "category_label": "アウター",
        "gender": ["men"],
        "ec_platform": "ZOZOTOWN",
        "price": 5490,
        "colors": ["black", "beige", "brown", "navy", "gray"],
        "vibes": ["cool_mode", "elegant_classic", "sweet_girly"],
        "materials": ["フェイクスエード", "ツイル"],
        "skeleton_good": ["wave", "straight"],
        "skeleton_note": "コンパクトなショート丈で重心を上げ、スタイルアップを狙えるメンズアウター。",
        "temp_min": 6,
        "temp_max": 19,
        "search_keyword": "ショート丈 ジップブルゾン",
    },
    {
        "id": "men-acc-01",
        "name": "推し色アクセント クロスボディショルダーバッグ",
        "category": "accessories",
        "category_label": "小物",
        "gender": ["men"],
        "ec_platform": "ZOZOTOWN",
        "price": 2480,
        "colors": ["black", "white", "purple", "red", "blue", "green", "yellow", "orange"],
        "vibes": ["cool_mode", "street_casual", "subculture_cyber", "elegant_classic"],
        "materials": ["コーデュラナイロン", "PUレザー"],
        "skeleton_good": ["straight", "wave", "natural"],
        "skeleton_note": "スマホやペンライトも入る実用サイズで、推しカラーをさりげなく取り入れられます。",
        "temp_min": -10,
        "temp_max": 40,
        "search_keyword": "クロスボディ ショルダーバッグ",
    },
]


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert #RRGGBB string to (R, G, B) tuple."""
    cleaned = hex_color.strip().lstrip("#")
    if len(cleaned) != 6:
        return (128, 128, 128)
    try:
        return (int(cleaned[0:2], 16), int(cleaned[2:4], 16), int(cleaned[4:6], 16))
    except ValueError:
        return (128, 128, 128)


def map_hex_to_color_info(hex_color: str) -> Dict[str, str]:
    """Map an arbitrary hex color to the nearest named palette color."""
    r1, g1, b1 = hex_to_rgb(hex_color)
    best = COLOR_PALETTE[0]
    best_dist = float("inf")
    for c in COLOR_PALETTE:
        r2, g2, b2 = c["rgb"]
        dist = math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)
        if dist < best_dist:
            best_dist = dist
            best = c
    return {"hex": hex_color, "id": best["id"], "name": best["name"]}


def infer_vibe_and_materials(
    colors: List[Dict[str, str]],
    hint_text: str = "",
) -> Tuple[str, List[str]]:
    """Infer fashion vibe and recommended materials from dominant colors when Vision API is not used."""
    color_ids = [c["id"] for c in colors]
    hint_lower = hint_text.lower()

    if any(k in hint_lower for k in ["サイバー", "cyber", "ネオン", "地雷", "サブカル"]):
        return "subculture_cyber", ["エコレザー", "メッシュ", "シルバーパーツ"]
    if any(k in hint_lower for k in ["ガーリー", "姫", "sweet", "量産"]):
        return "sweet_girly", ["シフォン", "チュール", "リボン"]
    if any(k in hint_lower for k in ["ストリート", "casual", "スポーティ"]):
        return "street_casual", ["デニム", "裏毛コットン", "ナイロン"]

    if any(c in color_ids for c in ["pink", "lavender", "mint"]):
        return "sweet_girly", ["シフォン", "チュール", "モヘア風ニット"]
    if any(c in color_ids for c in ["purple", "red"]) and "black" in color_ids:
        return "subculture_cyber", ["エコレザー", "レース", "厚手ツイル"]
    if any(c in color_ids for c in ["black", "navy", "gray"]) and not any(
        c in color_ids for c in ["pink", "yellow", "orange"]
    ):
        return "cool_mode", ["ハリ感ツイル", "ハイゲージニット", "サテン"]
    if any(c in color_ids for c in ["beige", "ivory", "brown", "sax"]):
        return "elegant_classic", ["落ち感サテン", "コットンポプリン", "リネン混"]
    return "street_casual", ["ウォッシュドデニム", "コットン", "ナイロンタフタ"]


def build_affiliate_url(
    platform: str,
    keyword: str,
    color_name: str,
    gender: str = "women",
    affiliate_id: Optional[str] = None,
) -> str:
    """Generate a purchase-ready EC search URL (with optional affiliate tracking parameters)."""
    aff = (affiliate_id or os.environ.get("OSHI_AFFILIATE_ID") or "").strip()
    gender_label = "メンズ" if gender == "men" else "レディース"

    if platform.upper() == "SHEIN":
        full_query = f"{gender_label} {color_name} {keyword}".strip()
        encoded_path = urllib.parse.quote(full_query)
        base_url = f"https://jp.shein.com/pdsearch/{encoded_path}/"
        if aff:
            return f"{base_url}?aff_id={urllib.parse.quote_plus(aff)}&utm_source=oshi_coord_ai"
        return base_url

    # ZOZOTOWN search URL uses Shift_JIS (cp932) for p_keyv and sex=men/women for gender
    # Use concise keyword (last token if multi-word) + color so results always hit
    short_kw = keyword.split()[-1] if keyword else ""
    zozo_text = f"{color_name} {short_kw}".strip()
    zozo_query = urllib.parse.quote_plus(zozo_text, encoding="cp932", errors="replace")
    sex_param = "men" if gender == "men" else "women"
    base_url = f"https://zozo.jp/search/?p_keyv={zozo_query}&sex={sex_param}"
    if aff:
        return f"{base_url}&utm_source=oshi_coord_ai&aff_id={urllib.parse.quote_plus(aff)}"
    return base_url


def select_outfit(
    extracted_colors: List[Dict[str, str]],
    vibe: str,
    skeleton_type: str,
    temp_c: float,
    weather_condition: str,
    budget_yen: int,
    gender: str = "women",
    affiliate_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Filter & rank catalog items by:
    1. Buyer gender (women / men)
    2. Skeleton type (strict exclusion of incompatible items)
    3. Temperature / Weather (decides whether outer is needed)
    4. Color & Vibe match from the uploaded Oshi image
    5. Budget limit (greedy optimization + fallback to affordable items)
    """
    if skeleton_type not in SKELETON_RULES:
        skeleton_type = "wave"
    if gender not in ("women", "men"):
        gender = "women"

    need_outer = temp_c <= 19.0 or ("雨" in weather_condition and temp_c <= 22.0)
    target_categories = ["tops", "bottoms"]
    if need_outer:
        target_categories.append("outer")
    target_categories.extend(["shoes", "accessories"])

    target_color_ids = [c["id"] for c in extracted_colors]
    primary_color_name = extracted_colors[0]["name"] if extracted_colors else "ブラック"

    gender_pool = [it for it in CATALOG_ITEMS if gender in it.get("gender", ["women"])]
    excluded_count = sum(1 for it in gender_pool if skeleton_type not in it["skeleton_good"])

    def score_item(item: Dict[str, Any]) -> float:
        score = 0.0
        # Color match (weighted by primary/secondary/accent)
        for idx, cid in enumerate(target_color_ids):
            if cid in item["colors"]:
                score += (3 - idx) * 12.0
        # Vibe match
        if vibe in item["vibes"]:
            score += 18.0
        # Temperature fit
        if item["temp_min"] <= temp_c <= item["temp_max"]:
            score += 15.0
        else:
            dist = min(abs(temp_c - item["temp_min"]), abs(temp_c - item["temp_max"]))
            score -= dist * 1.5
        # Rain bonus for water-repellent outer
        if "雨" in weather_condition and "撥水" in item["name"]:
            score += 15.0
        return score

    selected: List[Dict[str, Any]] = []
    remaining_budget = budget_yen if budget_yen > 0 else 999999

    # First pass: pick highest-scoring skeleton-compatible item per category, respecting budget
    for idx, cat in enumerate(target_categories):
        candidates = [
            it for it in gender_pool
            if it["category"] == cat and skeleton_type in it["skeleton_good"]
        ]
        # Reserve minimal budget for remaining categories
        categories_left = len(target_categories) - idx - 1
        per_item_floor = min(1500, max(800, remaining_budget // max(categories_left + 1, 1)))
        reserve = categories_left * per_item_floor
        affordable = [it for it in candidates if it["price"] <= max(remaining_budget - reserve, per_item_floor)]
        if affordable:
            ranked = sorted(affordable, key=score_item, reverse=True)
        else:
            ranked = sorted(candidates, key=lambda x: (x["price"], -score_item(x)))
        if not ranked:
            continue
        chosen = dict(ranked[0])
        # Pick best matching color from extracted colors
        matched_color = primary_color_name
        matched_color_hex = extracted_colors[0]["hex"] if extracted_colors else "#181820"
        for c in extracted_colors:
            if c["id"] in chosen["colors"]:
                matched_color = c["name"]
                matched_color_hex = c["hex"]
                break
        chosen["matched_color"] = matched_color
        chosen["matched_color_hex"] = matched_color_hex
        chosen["shein_url"] = build_affiliate_url(
            "SHEIN",
            chosen["search_keyword"],
            matched_color,
            gender=gender,
            affiliate_id=affiliate_id,
        )
        chosen["zozotown_url"] = build_affiliate_url(
            "ZOZOTOWN",
            chosen["search_keyword"],
            matched_color,
            gender=gender,
            affiliate_id=affiliate_id,
        )
        chosen["affiliate_url"] = (
            chosen["shein_url"] if chosen["ec_platform"] == "SHEIN" else chosen["zozotown_url"]
        )
        selected.append(chosen)
        remaining_budget -= chosen["price"]

    total_price = sum(it["price"] for it in selected)
    within_budget = True if budget_yen <= 0 else total_price <= budget_yen

    return {
        "items": selected,
        "total_price": total_price,
        "within_budget": within_budget,
        "need_outer": need_outer,
        "gender": gender,
        "excluded_by_skeleton_count": excluded_count,
        "skeleton_rule": SKELETON_RULES[skeleton_type],
    }
