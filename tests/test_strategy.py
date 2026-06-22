import unittest
from patterns.strategy import (
    PointsStrategy, WinRateStrategy, EloStrategy,
    HeadToHeadStrategy, RankingContext,
)
from models.team import Team
from models.player import Player
from models.match import Match, MatchResult, MatchStatus


class StrategyTestBase(unittest.TestCase):

    def _make_team(self, name, tag, wins=0, losses=0, draws=0,
                   points=0, elo=1000.0):
        t = Team(name=name, tag=tag, region="NA",
                 players=[Player(username=f"{tag}_player")])
        t.wins = wins
        t.losses = losses
        t.draws = draws
        t.points = points
        t.elo = elo
        return t

    def _make_match(self, t1_id, t2_id, result=MatchResult.TEAM1_WIN):
        m = Match(team1_id=t1_id, team2_id=t2_id,
                  status=MatchStatus.COMPLETED, result=result)
        return m


class TestPointsStrategy(StrategyTestBase):
    def test_ranks_by_points(self):
        teams = [
            self._make_team("A", "A", points=9),
            self._make_team("B", "B", points=6),
            self._make_team("C", "C", points=12),
        ]
        result = PointsStrategy().rank(teams, [])
        self.assertEqual(result[0]["team"].name, "C")
        self.assertEqual(result[0]["rank"], 1)

    def test_tiebreak_by_gd(self):
        t1 = self._make_team("A", "A", points=6, wins=3, losses=1)
        t2 = self._make_team("B", "B", points=6, wins=2, losses=0)
        result = PointsStrategy().rank([t1, t2], [])
        self.assertEqual(result[0]["team"].name, "A")


class TestWinRateStrategy(StrategyTestBase):
    def test_ranks_by_win_rate(self):
        teams = [
            self._make_team("A", "A", wins=8, losses=2),
            self._make_team("B", "B", wins=5, losses=5),
            self._make_team("C", "C", wins=9, losses=1),
        ]
        result = WinRateStrategy().rank(teams, [])
        self.assertEqual(result[0]["team"].name, "C")
        self.assertAlmostEqual(result[0]["win_rate"], 90.0)

    def test_no_matches(self):
        teams = [self._make_team("A", "A")]
        result = WinRateStrategy().rank(teams, [])
        self.assertEqual(result[0]["win_rate"], 0.0)


class TestEloStrategy(StrategyTestBase):
    def test_ranks_by_elo(self):
        teams = [
            self._make_team("A", "A", elo=1200),
            self._make_team("B", "B", elo=1500),
            self._make_team("C", "C", elo=1100),
        ]
        result = EloStrategy().rank(teams, [])
        self.assertEqual(result[0]["team"].name, "B")

    def test_calculate_new_elo(self):
        new_w, new_l = EloStrategy.calculate_new_elo(1000, 1000)
        self.assertGreater(new_w, 1000)
        self.assertLess(new_l, 1000)

    def test_elo_upset(self):
        new_w, new_l = EloStrategy.calculate_new_elo(800, 1200)
        gain = new_w - 800
        self.assertGreater(gain, 16)

    def test_elo_expected_win(self):
        new_w, new_l = EloStrategy.calculate_new_elo(1200, 800)
        gain = new_w - 1200
        self.assertLess(gain, 16)


class TestHeadToHeadStrategy(StrategyTestBase):
    def test_ranks_by_h2h(self):
        t1 = self._make_team("A", "A", points=6)
        t2 = self._make_team("B", "B", points=6)
        matches = [
            self._make_match(t1.id, t2.id, MatchResult.TEAM1_WIN),
            self._make_match(t1.id, t2.id, MatchResult.TEAM1_WIN),
        ]
        result = HeadToHeadStrategy().rank([t1, t2], matches)
        self.assertEqual(result[0]["team"].name, "A")

    def test_no_matches(self):
        t1 = self._make_team("A", "A", points=6)
        t2 = self._make_team("B", "B", points=3)
        result = HeadToHeadStrategy().rank([t1, t2], [])
        self.assertEqual(result[0]["team"].name, "A")


class TestRankingContext(StrategyTestBase):
    def test_set_strategy(self):
        ctx = RankingContext("Points")
        self.assertEqual(ctx.strategy.name, "Points")
        ctx.set_strategy("Elo")
        self.assertEqual(ctx.strategy.name, "Elo")

    def test_invalid_strategy(self):
        ctx = RankingContext()
        with self.assertRaises(ValueError):
            ctx.set_strategy("NonExistent")

    def test_available_strategies(self):
        strategies = RankingContext.available_strategies()
        self.assertEqual(len(strategies), 4)
        self.assertIn("Points", strategies)
        self.assertIn("Win Rate", strategies)
        self.assertIn("Elo", strategies)
        self.assertIn("Head-to-Head", strategies)

    def test_get_rankings(self):
        ctx = RankingContext("Points")
        teams = [
            self._make_team("A", "A", points=10),
            self._make_team("B", "B", points=5),
        ]
        rankings = ctx.get_rankings(teams, [])
        self.assertEqual(len(rankings), 2)
        self.assertEqual(rankings[0]["rank"], 1)


if __name__ == "__main__":
    unittest.main()
