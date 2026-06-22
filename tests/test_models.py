import unittest
from models.player import Player, ROLES
from models.team import Team, REGIONS
from models.match import Match, MatchStatus, MatchResult


class TestPlayer(unittest.TestCase):

    def test_create_player(self):
        p = Player(username="TestPlayer", role="Rifler", age=20)
        self.assertEqual(p.username, "TestPlayer")
        self.assertEqual(p.role, "Rifler")
        self.assertEqual(p.age, 20)

    def test_player_default_values(self):
        p = Player(username="Default")
        self.assertEqual(p.role, "Rifler")
        self.assertEqual(p.age, 18)
        self.assertEqual(p.team_id, "")

    def test_player_invalid_role(self):
        with self.assertRaises(ValueError):
            Player(username="Bad", role="InvalidRole")

    def test_player_invalid_age_low(self):
        with self.assertRaises(ValueError):
            Player(username="Young", age=5)

    def test_player_invalid_age_high(self):
        with self.assertRaises(ValueError):
            Player(username="Old", age=100)

    def test_player_empty_name(self):
        with self.assertRaises(ValueError):
            Player(username="")

    def test_player_to_dict(self):
        p = Player(username="Phantom", role="AWPer", age=22)
        d = p.to_dict()
        self.assertEqual(d["username"], "Phantom")
        self.assertEqual(d["role"], "AWPer")
        self.assertEqual(d["age"], 22)

    def test_player_from_dict(self):
        d = {"username": "Test", "role": "IGL", "age": 25, "id": "abc123"}
        p = Player.from_dict(d)
        self.assertEqual(p.username, "Test")
        self.assertEqual(p.role, "IGL")
        self.assertEqual(p.id, "abc123")

    def test_player_str(self):
        p = Player(username="Ghost", role="Support")
        self.assertIn("Ghost", str(p))
        self.assertIn("Support", str(p))

    def test_all_roles_valid(self):
        for role in ROLES:
            p = Player(username=f"Test_{role}", role=role)
            self.assertEqual(p.role, role)


class TestTeam(unittest.TestCase):

    def _make_team(self, **kwargs):
        defaults = {"name": "Test Team", "tag": "TST", "region": "NA"}
        defaults.update(kwargs)
        return Team(**defaults)

    def test_create_team(self):
        t = self._make_team()
        self.assertEqual(t.name, "Test Team")
        self.assertEqual(t.tag, "TST")
        self.assertEqual(t.region, "NA")

    def test_team_empty_name(self):
        with self.assertRaises(ValueError):
            Team(name="", tag="TST", region="NA")

    def test_team_empty_tag(self):
        with self.assertRaises(ValueError):
            Team(name="Test", tag="", region="NA")

    def test_team_tag_too_long(self):
        with self.assertRaises(ValueError):
            Team(name="Test", tag="TOOLONG7", region="NA")

    def test_team_invalid_region(self):
        with self.assertRaises(ValueError):
            Team(name="Test", tag="TST", region="MARS")

    def test_add_player(self):
        t = self._make_team()
        p = Player(username="Player1")
        t.add_player(p)
        self.assertEqual(t.roster_size, 1)
        self.assertEqual(p.team_id, t.id)

    def test_add_player_max(self):
        t = self._make_team()
        for i in range(10):
            t.add_player(Player(username=f"P{i}"))
        with self.assertRaises(ValueError):
            t.add_player(Player(username="P11"))

    def test_remove_player(self):
        t = self._make_team()
        p = Player(username="Player1")
        t.add_player(p)
        t.remove_player(p.id)
        self.assertEqual(t.roster_size, 0)

    def test_record_win(self):
        t = self._make_team()
        t.record_win(3)
        self.assertEqual(t.wins, 1)
        self.assertEqual(t.points, 3)

    def test_record_loss(self):
        t = self._make_team()
        t.record_loss()
        self.assertEqual(t.losses, 1)
        self.assertEqual(t.points, 0)

    def test_record_draw(self):
        t = self._make_team()
        t.record_draw()
        self.assertEqual(t.draws, 1)
        self.assertEqual(t.points, 1)

    def test_win_rate(self):
        t = self._make_team()
        t.record_win()
        t.record_loss()
        self.assertAlmostEqual(t.win_rate, 50.0)

    def test_win_rate_no_matches(self):
        t = self._make_team()
        self.assertEqual(t.win_rate, 0.0)

    def test_goal_difference(self):
        t = self._make_team()
        t.record_win()
        t.record_win()
        t.record_loss()
        self.assertEqual(t.goal_difference, 1)

    def test_team_to_dict(self):
        t = self._make_team()
        t.add_player(Player(username="P1"))
        d = t.to_dict()
        self.assertEqual(d["name"], "Test Team")
        self.assertEqual(len(d["players"]), 1)

    def test_team_from_dict(self):
        d = {"name": "From Dict", "tag": "FD", "region": "EU",
             "elo": 1200.0, "wins": 5, "players": [
                 {"username": "P1", "role": "Rifler", "age": 20}
             ]}
        t = Team.from_dict(d)
        self.assertEqual(t.name, "From Dict")
        self.assertEqual(t.elo, 1200.0)
        self.assertEqual(len(t.players), 1)

    def test_update_elo(self):
        t = self._make_team()
        t.update_elo(1150.5)
        self.assertEqual(t.elo, 1150.5)


class TestMatch(unittest.TestCase):

    def test_create_match(self):
        m = Match(team1_id="t1", team2_id="t2")
        self.assertEqual(m.team1_id, "t1")
        self.assertEqual(m.team2_id, "t2")
        self.assertEqual(m.status, MatchStatus.SCHEDULED)
        self.assertEqual(m.result, MatchResult.PENDING)

    def test_match_same_team(self):
        with self.assertRaises(ValueError):
            Match(team1_id="t1", team2_id="t1")

    def test_match_is_live(self):
        m = Match(team1_id="t1", team2_id="t2", status=MatchStatus.LIVE)
        self.assertTrue(m.is_live)

    def test_match_is_completed(self):
        m = Match(team1_id="t1", team2_id="t2", status=MatchStatus.COMPLETED)
        self.assertTrue(m.is_completed)

    def test_score_display(self):
        m = Match(team1_id="t1", team2_id="t2", score1=3, score2=1)
        self.assertEqual(m.score_display, "3  —  1")

    def test_determine_result_team1_win(self):
        m = Match(team1_id="t1", team2_id="t2", score1=2, score2=0)
        result = m.determine_result()
        self.assertEqual(result, MatchResult.TEAM1_WIN)
        self.assertEqual(m.winner_id, "t1")

    def test_determine_result_team2_win(self):
        m = Match(team1_id="t1", team2_id="t2", score1=0, score2=3)
        result = m.determine_result()
        self.assertEqual(result, MatchResult.TEAM2_WIN)
        self.assertEqual(m.winner_id, "t2")

    def test_determine_result_draw(self):
        m = Match(team1_id="t1", team2_id="t2", score1=1, score2=1)
        result = m.determine_result()
        self.assertEqual(result, MatchResult.DRAW)
        self.assertEqual(m.winner_id, "")

    def test_match_to_dict(self):
        m = Match(team1_id="t1", team2_id="t2", game="Valorant")
        d = m.to_dict()
        self.assertEqual(d["team1_id"], "t1")
        self.assertEqual(d["game"], "Valorant")

    def test_match_from_dict(self):
        d = {"team1_id": "a", "team2_id": "b", "score1": 3, "score2": 2,
             "status": "completed", "result": "team1_win", "game": "CS2"}
        m = Match.from_dict(d)
        self.assertEqual(m.score1, 3)
        self.assertEqual(m.status, MatchStatus.COMPLETED)
        self.assertEqual(m.result, MatchResult.TEAM1_WIN)


if __name__ == "__main__":
    unittest.main()
