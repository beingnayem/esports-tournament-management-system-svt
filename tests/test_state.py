import unittest
from patterns.state import (
    MatchContext, MatchState, InvalidStateTransitionError,
    ScheduledState, CheckInState, LiveState, OvertimeState,
    CompletedState, CancelledState, DisputedState,
    STATE_MAP,
)
from models.match import Match, MatchStatus


class TestMatchStates(unittest.TestCase):

    def test_scheduled_state(self):
        s = ScheduledState()
        self.assertEqual(s.name, "SCHEDULED")
        self.assertEqual(s.color_key, "AMBER")
        self.assertFalse(s.is_terminal)
        self.assertFalse(s.is_active)

    def test_scheduled_transitions(self):
        s = ScheduledState()
        self.assertTrue(s.can_transition_to("CHECK_IN"))
        self.assertTrue(s.can_transition_to("CANCELLED"))
        self.assertFalse(s.can_transition_to("COMPLETED"))
        self.assertFalse(s.can_transition_to("LIVE"))

    def test_live_state(self):
        s = LiveState()
        self.assertEqual(s.name, "LIVE")
        self.assertTrue(s.is_active)
        self.assertFalse(s.is_terminal)

    def test_live_transitions(self):
        s = LiveState()
        self.assertTrue(s.can_transition_to("OVERTIME"))
        self.assertTrue(s.can_transition_to("COMPLETED"))
        self.assertTrue(s.can_transition_to("CANCELLED"))
        self.assertTrue(s.can_transition_to("DISPUTED"))

    def test_completed_state(self):
        s = CompletedState()
        self.assertTrue(s.is_terminal)
        self.assertTrue(s.can_transition_to("DISPUTED"))
        self.assertFalse(s.can_transition_to("LIVE"))

    def test_cancelled_state(self):
        s = CancelledState()
        self.assertTrue(s.is_terminal)
        self.assertEqual(s.get_allowed_transitions(), [])

    def test_disputed_transitions(self):
        s = DisputedState()
        self.assertTrue(s.can_transition_to("LIVE"))
        self.assertTrue(s.can_transition_to("COMPLETED"))
        self.assertTrue(s.can_transition_to("CANCELLED"))

    def test_overtime_state(self):
        s = OvertimeState()
        self.assertTrue(s.is_active)
        self.assertEqual(s.color_key, "ACCENT")


class TestMatchContext(unittest.TestCase):

    def _make_context(self, initial="SCHEDULED"):
        m = Match(team1_id="t1", team2_id="t2")
        return MatchContext(m, initial_state=initial)

    def test_initial_state(self):
        ctx = self._make_context()
        self.assertEqual(ctx.state_name, "SCHEDULED")

    def test_valid_transition(self):
        ctx = self._make_context()
        ctx.transition_to("CHECK_IN")
        self.assertEqual(ctx.state_name, "CHECK_IN")

    def test_invalid_transition(self):
        ctx = self._make_context()
        with self.assertRaises(InvalidStateTransitionError):
            ctx.transition_to("COMPLETED")

    def test_full_lifecycle(self):
        ctx = self._make_context()
        ctx.start_checkin()
        self.assertEqual(ctx.state_name, "CHECK_IN")
        ctx.start_match()
        self.assertEqual(ctx.state_name, "LIVE")
        ctx.complete()
        self.assertEqual(ctx.state_name, "COMPLETED")

    def test_lifecycle_with_overtime(self):
        ctx = self._make_context()
        ctx.start_checkin()
        ctx.start_match()
        ctx.go_overtime()
        self.assertEqual(ctx.state_name, "OVERTIME")
        ctx.complete()
        self.assertEqual(ctx.state_name, "COMPLETED")

    def test_cancel_from_scheduled(self):
        ctx = self._make_context()
        ctx.cancel()
        self.assertEqual(ctx.state_name, "CANCELLED")

    def test_cancel_from_live(self):
        ctx = self._make_context("LIVE")
        ctx.cancel()
        self.assertEqual(ctx.state_name, "CANCELLED")

    def test_cannot_transition_from_cancelled(self):
        ctx = self._make_context("CANCELLED")
        with self.assertRaises(InvalidStateTransitionError):
            ctx.start_match()

    def test_dispute_from_live(self):
        ctx = self._make_context("LIVE")
        ctx.dispute()
        self.assertEqual(ctx.state_name, "DISPUTED")

    def test_history(self):
        ctx = self._make_context()
        ctx.start_checkin()
        ctx.start_match()
        self.assertEqual(ctx.history, ["SCHEDULED", "CHECK_IN", "LIVE"])

    def test_match_status_updated(self):
        ctx = self._make_context()
        ctx.start_checkin()
        self.assertEqual(ctx.match.status, MatchStatus.CHECK_IN)
        ctx.start_match()
        self.assertEqual(ctx.match.status, MatchStatus.LIVE)

    def test_on_transition_callback(self):
        ctx = self._make_context()
        transitions = []
        ctx.set_on_transition(lambda f, t: transitions.append((f, t)))
        ctx.start_checkin()
        self.assertEqual(transitions, [("SCHEDULED", "CHECK_IN")])

    def test_get_available_actions(self):
        ctx = self._make_context()
        actions = ctx.get_available_actions()
        self.assertIn("Start Check-in", actions)
        self.assertIn("Cancel", actions)
        self.assertNotIn("Complete", actions)

    def test_state_map_all_states(self):
        self.assertEqual(len(STATE_MAP), 7)
        for name in ["SCHEDULED", "CHECK_IN", "LIVE", "OVERTIME",
                      "COMPLETED", "CANCELLED", "DISPUTED"]:
            self.assertIn(name, STATE_MAP)


class TestInvalidStateTransitionError(unittest.TestCase):
    def test_error_message(self):
        err = InvalidStateTransitionError("SCHEDULED", "COMPLETED")
        self.assertIn("SCHEDULED", str(err))
        self.assertIn("COMPLETED", str(err))

    def test_error_with_action(self):
        err = InvalidStateTransitionError("SCHEDULED", "LIVE", "start_match")
        self.assertIn("start_match", str(err))


if __name__ == "__main__":
    unittest.main()
