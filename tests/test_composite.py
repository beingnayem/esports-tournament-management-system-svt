import unittest
from patterns.composite import (
    MatchNode, RoundNode, TournamentBracket, BracketNode,
)
from models.match import Match


class TestMatchNode(unittest.TestCase):

    def test_create_match_node(self):
        node = MatchNode(position=0, round_num=1)
        self.assertIsNone(node.match)
        self.assertEqual(node.position, 0)
        self.assertEqual(node.round_num, 1)

    def test_match_node_with_match(self):
        m = Match(team1_id="t1", team2_id="t2")
        node = MatchNode(match=m)
        self.assertEqual(node.get_matches(), [m])

    def test_no_winner_without_result(self):
        m = Match(team1_id="t1", team2_id="t2")
        node = MatchNode(match=m)
        self.assertIsNone(node.get_winner())

    def test_winner_after_result(self):
        m = Match(team1_id="t1", team2_id="t2", score1=2, score2=0)
        m.determine_result()
        node = MatchNode(match=m)
        self.assertEqual(node.get_winner(), "t1")

    def test_depth(self):
        node = MatchNode()
        self.assertEqual(node.get_depth(), 1)

    def test_get_all_nodes(self):
        node = MatchNode()
        self.assertEqual(len(node.get_all_nodes()), 1)


class TestRoundNode(unittest.TestCase):

    def test_create_round(self):
        r = RoundNode(round_number=1, name="Round 1")
        self.assertEqual(r.round_number, 1)
        self.assertEqual(r.name, "Round 1")
        self.assertEqual(len(r.children), 0)

    def test_add_children(self):
        r = RoundNode(round_number=1)
        r.add_child(MatchNode())
        r.add_child(MatchNode())
        self.assertEqual(len(r.children), 2)

    def test_remove_child(self):
        r = RoundNode(round_number=1)
        n = MatchNode()
        r.add_child(n)
        r.remove_child(n)
        self.assertEqual(len(r.children), 0)

    def test_get_matches(self):
        r = RoundNode(round_number=1)
        m1 = Match(team1_id="a", team2_id="b")
        m2 = Match(team1_id="c", team2_id="d")
        r.add_child(MatchNode(match=m1))
        r.add_child(MatchNode(match=m2))
        self.assertEqual(len(r.get_matches()), 2)

    def test_depth(self):
        r = RoundNode(round_number=1)
        r.add_child(MatchNode())
        self.assertEqual(r.get_depth(), 2)

    def test_match_count(self):
        r = RoundNode(round_number=1)
        r.add_child(MatchNode(match=Match(team1_id="a", team2_id="b")))
        r.add_child(MatchNode())
        self.assertEqual(r.match_count, 2)

    def test_no_winner(self):
        r = RoundNode(round_number=1)
        self.assertIsNone(r.get_winner())


class TestTournamentBracket(unittest.TestCase):

    def _build_bracket(self, n_teams=8):
        bracket = TournamentBracket()
        team_ids = [f"t{i}" for i in range(n_teams)]
        team_names = {f"t{i}": f"Team {i}" for i in range(n_teams)}

        def factory(t1, t2, rnd, pos):
            if t1 and t2:
                return Match(team1_id=t1, team2_id=t2,
                            round_number=rnd, bracket_position=pos)
            return Match(team1_id=t1 or "", team2_id=t2 or "",
                        round_number=rnd, bracket_position=pos)

        bracket.build(team_ids, team_names, factory)
        return bracket

    def test_build_bracket_8_teams(self):
        bracket = self._build_bracket(8)
        self.assertEqual(bracket.total_rounds, 3)

    def test_build_bracket_4_teams(self):
        bracket = self._build_bracket(4)
        self.assertEqual(bracket.total_rounds, 2)

    def test_round_names(self):
        bracket = self._build_bracket(8)
        names = [r.name for r in bracket.rounds]
        self.assertIn("Grand Final", names)
        self.assertIn("Semifinals", names)

    def test_get_round(self):
        bracket = self._build_bracket(8)
        r1 = bracket.get_round(1)
        self.assertIsNotNone(r1)
        self.assertEqual(r1.round_number, 1)

    def test_get_round_none(self):
        bracket = self._build_bracket(8)
        self.assertIsNone(bracket.get_round(99))

    def test_advance_winner(self):
        bracket = self._build_bracket(4)
        r1 = bracket.get_round(1)
        first_match_node = [c for c in r1.children if isinstance(c, MatchNode)][0]
        match = first_match_node.match
        match.score1 = 2
        match.score2 = 0
        match.determine_result()
        bracket.advance_winner(match.id, match.winner_id)

        r2 = bracket.get_round(2)
        final_node = [c for c in r2.children if isinstance(c, MatchNode)][0]
        self.assertIn("Team", final_node.team1_name)

    def test_empty_bracket(self):
        bracket = TournamentBracket()
        bracket.build([], {})
        self.assertEqual(bracket.total_rounds, 0)

    def test_single_team(self):
        bracket = TournamentBracket()
        bracket.build(["t1"], {"t1": "Solo"})
        self.assertEqual(bracket.total_rounds, 0)

    def test_get_match_nodes_by_round(self):
        bracket = self._build_bracket(8)
        nodes = bracket.get_match_nodes_by_round(1)
        self.assertEqual(len(nodes), 4)


if __name__ == "__main__":
    unittest.main()
