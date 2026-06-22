import unittest
from services.bracket_service import BracketService
from models.match import Match


class TestBracketService(unittest.TestCase):

    def _make_service(self, n_teams=8):
        svc = BracketService()
        team_ids = [f"t{i}" for i in range(n_teams)]
        team_names = {f"t{i}": f"Team {i}" for i in range(n_teams)}

        def factory(t1, t2, rnd, pos):
            return Match(team1_id=t1 or "", team2_id=t2 or "",
                        round_number=rnd, bracket_position=pos)

        svc.set_match_factory(factory)
        svc.generate_bracket(team_ids, team_names)
        return svc

    def test_generate_bracket(self):
        svc = self._make_service(8)
        self.assertEqual(svc.total_rounds, 3)
        self.assertGreater(svc.total_matches, 0)

    def test_get_bracket_data(self):
        svc = self._make_service(8)
        data = svc.get_bracket_data()
        self.assertEqual(len(data), 3)
        self.assertIn("matches", data[0])
        self.assertIn("round_number", data[0])

    def test_bracket_data_has_teams(self):
        svc = self._make_service(4)
        data = svc.get_bracket_data()
        first_match = data[0]["matches"][0]
        self.assertIn("team1_name", first_match)
        self.assertIn("team2_name", first_match)

    def test_advance_winner(self):
        svc = self._make_service(4)
        data = svc.get_bracket_data()
        first_match = data[0]["matches"][0]
        match_id = first_match.get("match_id")
        if match_id:
            svc.advance_winner(match_id, "t0")
            data2 = svc.get_bracket_data()
            final = data2[1]["matches"][0]
            self.assertIn("Team 0", [final["team1_name"], final["team2_name"]])

    def test_get_match_node(self):
        svc = self._make_service(4)
        data = svc.get_bracket_data()
        match_id = data[0]["matches"][0].get("match_id")
        if match_id:
            node = svc.get_match_node(match_id)
            self.assertIsNotNone(node)

    def test_reset(self):
        svc = self._make_service(8)
        svc.reset()
        self.assertEqual(svc.total_rounds, 0)
        self.assertEqual(svc.total_matches, 0)

    def test_small_bracket(self):
        svc = BracketService()
        svc.generate_bracket(["t1", "t2"], {"t1": "A", "t2": "B"})
        self.assertEqual(svc.total_rounds, 1)

    def test_get_all_matches(self):
        svc = self._make_service(8)
        matches = svc.get_all_matches()
        self.assertGreater(len(matches), 0)


if __name__ == "__main__":
    unittest.main()
