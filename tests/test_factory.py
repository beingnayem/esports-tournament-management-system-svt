import unittest
from patterns.factory import TournamentFactory, TournamentConfig, TournamentType


class TestTournamentFactory(unittest.TestCase):

    def test_create_single_elimination(self):
        config = TournamentFactory.create("Single Elimination", max_teams=8)
        self.assertEqual(config.tournament_type, TournamentType.SINGLE_ELIMINATION)
        self.assertEqual(config.rounds, 3)
        self.assertEqual(config.total_matches, 7)
        self.assertFalse(config.has_losers_bracket)

    def test_create_double_elimination(self):
        config = TournamentFactory.create("Double Elimination", max_teams=8)
        self.assertEqual(config.tournament_type, TournamentType.DOUBLE_ELIMINATION)
        self.assertTrue(config.has_losers_bracket)
        self.assertEqual(config.total_matches, 14)

    def test_create_round_robin(self):
        config = TournamentFactory.create("Round Robin", max_teams=8)
        self.assertEqual(config.tournament_type, TournamentType.ROUND_ROBIN)
        self.assertEqual(config.rounds, 7)
        self.assertEqual(config.total_matches, 28)

    def test_create_swiss(self):
        config = TournamentFactory.create("Swiss", max_teams=8)
        self.assertEqual(config.tournament_type, TournamentType.SWISS)
        self.assertGreater(config.rounds, 0)

    def test_create_unknown_type(self):
        with self.assertRaises(ValueError):
            TournamentFactory.create("Battle Royale")

    def test_available_types(self):
        types = TournamentFactory.available_types()
        self.assertEqual(len(types), 4)
        self.assertIn("Single Elimination", types)
        self.assertIn("Round Robin", types)

    def test_create_by_enum(self):
        config = TournamentFactory.create_by_enum(
            TournamentType.SINGLE_ELIMINATION, max_teams=16
        )
        self.assertEqual(config.tournament_type, TournamentType.SINGLE_ELIMINATION)
        self.assertEqual(config.max_teams, 16)
        self.assertEqual(config.rounds, 4)

    def test_min_teams(self):
        config = TournamentFactory.create("Single Elimination", max_teams=2)
        self.assertEqual(config.total_matches, 1)

    def test_invalid_team_count(self):
        with self.assertRaises(ValueError):
            TournamentFactory.create("Single Elimination", max_teams=1)

    def test_config_description(self):
        config = TournamentFactory.create("Single Elimination", max_teams=8)
        self.assertIn("8 teams", config.description)

    def test_config_custom_name(self):
        config = TournamentFactory.create("Round Robin", name="My Tournament")
        self.assertEqual(config.name, "My Tournament")

    def test_sixteen_team_single_elim(self):
        config = TournamentFactory.create("Single Elimination", max_teams=16)
        self.assertEqual(config.rounds, 4)
        self.assertEqual(config.total_matches, 15)


if __name__ == "__main__":
    unittest.main()
