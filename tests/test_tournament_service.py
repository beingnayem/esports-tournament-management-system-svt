import unittest
import os
import json
from services.tournament_service import TournamentService
from models.player import Player
from models.team import Team
from models.match import MatchStatus, MatchResult
from patterns.state import InvalidStateTransitionError


class TestTournamentService(unittest.TestCase):

    def setUp(self):
        self.svc = TournamentService()

    def _make_team(self, name="Test", tag="TST"):
        t = Team(name=name, tag=tag, region="NA",
                 players=[Player(username=f"{tag}_p1")])
        return t

    def _register_teams(self, n=2):
        teams = []
        for i in range(n):
            t = self._make_team(f"Team {i}", f"T{i}")
            self.svc.register_team(t)
            teams.append(t)
        return teams

    def test_register_team(self):
        t = self._make_team()
        result = self.svc.register_team(t)
        self.assertEqual(result.name, "Test")
        self.assertEqual(len(self.svc.teams), 1)

    def test_register_team_no_players(self):
        t = Team(name="Empty", tag="EMP", region="NA")
        with self.assertRaises(ValueError):
            self.svc.register_team(t)

    def test_get_team(self):
        t = self._make_team()
        self.svc.register_team(t)
        found = self.svc.get_team(t.id)
        self.assertEqual(found.name, "Test")

    def test_remove_team(self):
        t = self._make_team()
        self.svc.register_team(t)
        self.svc.remove_team(t.id)
        self.assertEqual(len(self.svc.teams), 0)

    def test_create_match(self):
        teams = self._register_teams(2)
        m = self.svc.create_match(teams[0].id, teams[1].id)
        self.assertEqual(m.team1_id, teams[0].id)
        self.assertEqual(len(self.svc.matches), 1)

    def test_update_score(self):
        teams = self._register_teams(2)
        m = self.svc.create_match(teams[0].id, teams[1].id)
        self.svc.update_score(m.id, 3, 1)
        updated = self.svc.get_match(m.id)
        self.assertEqual(updated.score1, 3)
        self.assertEqual(updated.score2, 1)

    def test_increment_score(self):
        teams = self._register_teams(2)
        m = self.svc.create_match(teams[0].id, teams[1].id)
        self.svc.increment_score(m.id, 1)
        self.svc.increment_score(m.id, 1)
        self.svc.increment_score(m.id, 2)
        updated = self.svc.get_match(m.id)
        self.assertEqual(updated.score1, 2)
        self.assertEqual(updated.score2, 1)

    def test_transition_match(self):
        teams = self._register_teams(2)
        m = self.svc.create_match(teams[0].id, teams[1].id)
        self.svc.transition_match(m.id, "start_checkin")
        self.assertEqual(m.status, MatchStatus.CHECK_IN)

    def test_complete_match_updates_stats(self):
        teams = self._register_teams(2)
        m = self.svc.create_match(teams[0].id, teams[1].id)
        self.svc.transition_match(m.id, "start_checkin")
        self.svc.transition_match(m.id, "start_match")
        self.svc.update_score(m.id, 2, 0)
        self.svc.transition_match(m.id, "complete")

        winner = self.svc.get_team(teams[0].id)
        loser = self.svc.get_team(teams[1].id)
        self.assertEqual(winner.wins, 1)
        self.assertEqual(loser.losses, 1)
        self.assertGreater(winner.elo, 1000)

    def test_get_live_matches(self):
        teams = self._register_teams(2)
        m = self.svc.create_match(teams[0].id, teams[1].id)
        self.svc.transition_match(m.id, "start_checkin")
        self.svc.transition_match(m.id, "start_match")
        live = self.svc.get_live_matches()
        self.assertEqual(len(live), 1)

    def test_get_available_actions(self):
        teams = self._register_teams(2)
        m = self.svc.create_match(teams[0].id, teams[1].id)
        actions = self.svc.get_available_actions(m.id)
        self.assertIn("start_checkin", actions)
        self.assertIn("cancel", actions)

    def test_configure_tournament(self):
        config = self.svc.configure_tournament("Single Elimination", max_teams=8)
        self.assertEqual(config.max_teams, 8)

    def test_start_tournament(self):
        self._register_teams(4)
        self.svc.start_tournament()
        self.assertTrue(self.svc.tournament_started)

    def test_start_tournament_needs_teams(self):
        with self.assertRaises(ValueError):
            self.svc.start_tournament()

    def test_get_stats(self):
        self._register_teams(3)
        stats = self.svc.get_stats()
        self.assertEqual(stats["total_teams"], 3)

    def test_search_teams(self):
        teams = self._register_teams(3)
        results = self.svc.search("Team 1")
        self.assertGreater(len(results), 0)

    def test_search_no_results(self):
        results = self.svc.search("nonexistent")
        self.assertEqual(len(results), 0)

    def test_export_data(self):
        self._register_teams(2)
        data = self.svc.export_data()
        self.assertEqual(len(data["teams"]), 2)

    def test_reset(self):
        self._register_teams(3)
        self.svc.reset()
        self.assertEqual(len(self.svc.teams), 0)
        self.assertEqual(len(self.svc.matches), 0)

    def test_observer_events_fired(self):
        self._register_teams(2)
        self.assertGreater(len(self.svc.logging_sub.logs), 0)

    def test_multiple_tournaments_bracket_isolation(self):
        self.assertEqual(self.svc.active_tournament_id, "default")
        self.svc.tournament_name = "Default Tournament"
        self.svc.game = "CS2"
        self.svc.type_name = "Single Elimination"
        self.svc.max_teams = 8
        self.svc.bracket = "Default Bracket Object"

        t_id = self.svc.create_new_tournament("New League", "Valorant", "Double Elimination", 16)
        self.assertEqual(self.svc.active_tournament_id, t_id)
        self.assertEqual(self.svc.tournament_name, "New League")
        self.assertEqual(self.svc.game, "Valorant")
        self.assertEqual(self.svc.type_name, "Double Elimination")
        self.assertEqual(self.svc.max_teams, 16)
        
        self.assertIsNone(self.svc.bracket)
        self.svc.bracket = "New Bracket Object"

        self.svc.switch_tournament("default")
        self.assertEqual(self.svc.active_tournament_id, "default")
        self.assertEqual(self.svc.tournament_name, "Default Tournament")
        self.assertEqual(self.svc.game, "CS2")
        self.assertEqual(self.svc.type_name, "Single Elimination")
        self.assertEqual(self.svc.max_teams, 8)
        self.assertEqual(self.svc.bracket, "Default Bracket Object")


if __name__ == "__main__":
    unittest.main()
