#!/usr/bin/env python3
"""
Unit Test Suite for Event Relevance ML Personalization and Ranking Pipeline.
"""

import unittest
from predict_event_relevance import rank_events


class TestEventRelevance(unittest.TestCase):

    def setUp(self):
        self.sample_events = [
            {
                "name": "Tokyo International Anime Fair & Exhibition",
                "city": "Tokyo",
                "country": "Japan",
                "venue": "Tokyo Big Sight, Odaiba",
                "start_date": "2026-11-12",
                "end_date": "2026-11-15",
                "category": "anime",
                "description": "Premier international exhibition showcasing anime previews, VR gaming booths, and manga creators.",
                "source_url": "https://www.gotokyo.org/anime-fair-2026",
                "source_name": "GoTokyo Official",
            },
            {
                "name": "Tsukiji Outer Market Culinary & Sake Festival",
                "city": "Tokyo",
                "country": "Japan",
                "venue": "Tsukiji Outer Market, Chuo City",
                "start_date": "2026-11-11",
                "end_date": "2026-11-14",
                "category": "food",
                "description": "Authentic street food tastings, seasonal autumn seafood, and artisanal sake pairings.",
                "source_url": "https://www.gotokyo.org/tsukiji-autumn-2026",
                "source_name": "Tokyo Tourism Bureau",
            },
            {
                "name": "Meiji Jingu Autumn Grand Shinto Festival",
                "city": "Tokyo",
                "country": "Japan",
                "venue": "Meiji Shrine, Shibuya",
                "start_date": "2026-11-10",
                "end_date": "2026-11-12",
                "category": "culture",
                "description": "Traditional archery on horseback (Yabusame), classical court dances, and noh theatre.",
                "source_url": "https://www.meijijingu.or.jp/autumn-matsuri",
                "source_name": "Meiji Jingu Shrine",
            },
            {
                "name": "Osaka Street Takoyaki Extravaganza",
                "city": "Osaka",  # Different city!
                "country": "Japan",
                "venue": "Dotonbori Plaza, Osaka",
                "start_date": "2026-11-12",
                "end_date": "2026-11-14",
                "category": "food",
                "description": "Massive street food event in Osaka celebrating takoyaki and okonomiyaki.",
                "source_url": "https://osaka-info.jp/takoyaki-2026",
                "source_name": "Osaka Tourism",
            },
            {
                "name": "Tokyo Spring Blossom Festival",
                "city": "Tokyo",
                "country": "Japan",
                "venue": "Ueno Park, Tokyo",
                "start_date": "2027-03-25",  # Outside trip dates!
                "end_date": "2027-03-30",
                "category": "culture",
                "description": "Spring hanami cherry blossom celebration in Ueno Park.",
                "source_url": "https://www.gotokyo.org/ueno-sakura",
                "source_name": "Tokyo Tourism",
            },
        ]

    def test_personalization_ranking_differences(self):
        """User A (Anime/Tech) vs User B (Food/Culture) should rank different events #1."""
        profile_anime = {
            "city": "Tokyo",
            "country": "Japan",
            "start_date": "2026-11-10",
            "end_date": "2026-11-17",
            "interests": "Anime, technology, gaming",
        }
        ranked_a = rank_events(self.sample_events, profile_anime)
        self.assertEqual(ranked_a[0]["name"], "Tokyo International Anime Fair & Exhibition")
        self.assertGreaterEqual(ranked_a[0]["event_relevance_score"], 80)

        profile_food = {
            "city": "Tokyo",
            "country": "Japan",
            "start_date": "2026-11-10",
            "end_date": "2026-11-17",
            "interests": "Food, traditional culture, culinary tastings",
        }
        ranked_b = rank_events(self.sample_events, profile_food)
        # For User B, Food or Meiji Shinto Festival must rank above Anime Fair
        top_names = [ranked_b[0]["name"], ranked_b[1]["name"]]
        self.assertIn("Tsukiji Outer Market Culinary & Sake Festival", top_names)
        self.assertIn("Meiji Jingu Autumn Grand Shinto Festival", top_names)
        # Anime Fair should rank lower for User B
        self.assertLess(ranked_b[2]["event_relevance_score"], ranked_b[0]["event_relevance_score"])

    def test_locality_filter_penalizes_different_city(self):
        """Osaka event for a Tokyo trip must be heavily penalized (< 45)."""
        profile = {
            "city": "Tokyo",
            "country": "Japan",
            "start_date": "2026-11-10",
            "end_date": "2026-11-17",
            "interests": "Food, dining",
        }
        ranked = rank_events(self.sample_events, profile)
        osaka_event = next(e for e in ranked if "Osaka" in e["name"])
        tokyo_food = next(e for e in ranked if "Tsukiji" in e["name"])

        self.assertLess(osaka_event["event_relevance_score"], 45)
        self.assertGreater(tokyo_food["event_relevance_score"], osaka_event["event_relevance_score"])

    def test_date_overlap_penalizes_outside_trip(self):
        """Event in March 2027 for a November 2026 trip must be heavily penalized (< 45)."""
        profile = {
            "city": "Tokyo",
            "country": "Japan",
            "start_date": "2026-11-10",
            "end_date": "2026-11-17",
            "interests": "Culture, festivals",
        }
        ranked = rank_events(self.sample_events, profile)
        spring_event = next(e for e in ranked if "Spring Blossom" in e["name"])
        autumn_shrine = next(e for e in ranked if "Meiji Jingu" in e["name"])

        self.assertLess(spring_event["event_relevance_score"], 45)
        self.assertGreater(autumn_shrine["event_relevance_score"], spring_event["event_relevance_score"])


if __name__ == "__main__":
    unittest.main()
