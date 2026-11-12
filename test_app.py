"""Unit and pipeline tests for Oshi-Coord AI MVP."""

import unittest

from catalog import map_hex_to_color_info, select_outfit
from server import process_analyze_request


class TestCatalogAndStyling(unittest.TestCase):
    def test_skeleton_and_gender_filter(self) -> None:
        colors = [
            map_hex_to_color_info("#F8BBD0"),
            map_hex_to_color_info("#E1BEE7"),
            map_hex_to_color_info("#FFFFFF"),
        ]
        for gender in ("women", "men"):
            for skeleton in ("straight", "wave", "natural"):
                res = select_outfit(
                    extracted_colors=colors,
                    vibe="sweet_girly",
                    skeleton_type=skeleton,
                    temp_c=15.0,
                    weather_condition="晴れ",
                    budget_yen=15000,
                    gender=gender,
                    affiliate_id=None,
                )
                self.assertEqual(res["gender"], gender)
                self.assertEqual(len(res["items"]), 5)
                cats = [it["category"] for it in res["items"]]
                self.assertEqual(cats, ["tops", "bottoms", "outer", "shoes", "accessories"])
                for item in res["items"]:
                    self.assertIn(skeleton, item["skeleton_good"])
                    self.assertIn(gender, item.get("gender", ["women"]))
                    self.assertTrue(item["matched_color_hex"].startswith("#"))
                    self.assertTrue(item["zozotown_url"].startswith("https://zozo.jp/search/?p_keyv="))
                    self.assertIn(f"sex={gender}", item["zozotown_url"])
                    self.assertNotIn("p_gtype=", item["zozotown_url"])
                    self.assertNotIn("aff_id=", item["zozotown_url"])
                    self.assertTrue(item["shein_url"].startswith("https://jp.shein.com/pdsearch/"))
                    self.assertNotIn("aff_id=", item["shein_url"])

        # With explicit affiliate_id
        aff_res = select_outfit(
            extracted_colors=colors,
            vibe="sweet_girly",
            skeleton_type="wave",
            temp_c=20.0,
            weather_condition="晴れ",
            budget_yen=15000,
            gender="women",
            affiliate_id="test_aff",
        )
        self.assertIn("aff_id=test_aff", aff_res["items"][0]["zozotown_url"])
        self.assertIn("aff_id=test_aff", aff_res["items"][0]["shein_url"])

    def test_weather_outer_toggle(self) -> None:
        colors = [map_hex_to_color_info("#181820")]
        cold_res = select_outfit(colors, "cool_mode", "straight", 12.0, "くもり", 20000)
        warm_res = select_outfit(colors, "cool_mode", "straight", 26.0, "晴れ", 20000)
        self.assertTrue(cold_res["need_outer"])
        self.assertTrue(any(it["category"] == "outer" for it in cold_res["items"]))
        self.assertFalse(warm_res["need_outer"])
        self.assertFalse(any(it["category"] == "outer" for it in warm_res["items"]))


class TestAnalyzePipeline(unittest.TestCase):
    def test_process_analyze_request(self) -> None:
        data = process_analyze_request(
            {
                "dominant_hexes": ["#7B2CBF", "#181824", "#4CC9F0"],
                "oshi_hint": "サイバー系",
                "target_date": "2026-11-15",
                "location": "東京",
                "skeleton_type": "natural",
                "budget_yen": 12000,
            }
        )
        self.assertEqual(len(data["vision"]["colors"]), 3)
        self.assertEqual(data["weather"]["location"], "東京")
        self.assertEqual(data["recommendation"]["skeleton_rule"]["label"], "骨格ナチュラル")
        self.assertGreaterEqual(len(data["recommendation"]["items"]), 3)
        self.assertEqual(len(data["ec_showcase"]["zozotown"]), 3)
        self.assertEqual(len(data["ec_showcase"]["shein"]), 3)

    def test_manual_override_and_low_budgets(self) -> None:
        data = process_analyze_request(
            {
                "override_colors": ["#FF0000", "#000000", "#FFFFFF"],
                "override_vibe": "sweet_girly",
                "target_date": "2026-11-15",
                "location": "東京",
                "skeleton_type": "wave",
                "budget_yen": 2000,
            }
        )
        self.assertEqual(data["vision"]["source"], "manual_edit")
        self.assertEqual(data["vision"]["vibe"], "sweet_girly")
        self.assertEqual(data["vision"]["colors"][0]["id"], "red")

        unlimited = process_analyze_request(
            {
                "dominant_hexes": ["#000000", "#FFFFFF", "#333333"],
                "target_date": "2026-11-15",
                "location": "東京",
                "skeleton_type": "straight",
                "budget_yen": 0,
            }
        )
        self.assertTrue(unlimited["recommendation"]["within_budget"])


if __name__ == "__main__":
    unittest.main()
