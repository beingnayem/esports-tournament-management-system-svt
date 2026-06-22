import unittest
from services.ranking_service import RankingService
from models.player import Player
from models.team import Team
from models.match import Match, MatchStatus, MatchResult


class TestRankingService(unittest.TestCase):

    def _make_team(self, name, tag, wins=0, losses=0, points=0, elo=1000.0):
        t = Team(name=name, tag=tag, region="NA",
                 players=[Player(username=f"{tag}_p")])
        t.wins = wins
        t.losses = losses
        t.points = points
        t.elo = elo
        return t

    def test_get_rankings_points(self):
        svc = RankingService()
        teams = [
            self._make_team("A", "A", points=9),
            self._make_team("B", "B", points=3),
        ]
        rankings = svc.get_rankings(teams, [], "Points")
        self.assertEqual(rankings[0]["team"].name, "A")

    def test_get_rankings_elo(self):
        svc = RankingService()
        teams = [
            self._make_team("A", "A", elo=1100),
            self._make_team("B", "B", elo=1300),
        ]
        rankings = svc.get_rankings(teams, [], "Elo")
        self.assertEqual(rankings[0]["team"].name, "B")

    def test_switch_strategy(self):
        svc = RankingService()
        svc.set_strategy("Win Rate")
        self.assertEqual(svc.current_strategy, "Win Rate")

    def test_available_strategies(self):
        strategies = RankingService.available_strategies()
        self.assertEqual(len(strategies), 4)

    def test_trend_winning(self):
        svc = RankingService()
        t = self._make_team("A", "A")
        matches = []
        for i in range(3):
            m = Match(team1_id=t.id, team2_id="other",
                     status=MatchStatus.COMPLETED,
                     result=MatchResult.TEAM1_WIN)
            matches.append(m)
        trend = svc.get_trend(t, matches)
        self.assertEqual(trend, "↑")

    def test_trend_losing(self):
        svc = RankingService()
        t = self._make_team("A", "A")
        matches = []
        for i in range(3):
            m = Match(team1_id=t.id, team2_id="other",
                     status=MatchStatus.COMPLETED,
                     result=MatchResult.TEAM2_WIN)
            matches.append(m)
        trend = svc.get_trend(t, matches)
        self.assertEqual(trend, "↓")

    def test_trend_neutral(self):
        svc = RankingService()
        t = self._make_team("A", "A")
        trend = svc.get_trend(t, [])
        self.assertEqual(trend, "—")

    def test_radar_stats(self):
        svc = RankingService()
        t = self._make_team("A", "A", wins=5, losses=2, points=15, elo=1200)
        teams = [t]
        stats = svc.get_team_stats_for_radar(t, teams, [])
        self.assertIn("Win Rate", stats)
        self.assertIn("Elo", stats)
        self.assertGreater(stats["Elo"], 0)


if __name__ == "__main__":
    unittest.main()
