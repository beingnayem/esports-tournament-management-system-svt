from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING


class InvalidStateTransitionError(Exception):

    def __init__(self, from_state: str, to_state: str, action: str = ""):
        self.from_state = from_state
        self.to_state = to_state
        self.action = action
        msg = f"Invalid transition: {from_state} → {to_state}"
        if action:
            msg += f" (action: {action})"
        super().__init__(msg)


class MatchState(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def color_key(self) -> str:
        pass

    @property
    def is_terminal(self) -> bool:
        return False

    @property
    def is_active(self) -> bool:
        return False

    def enter(self, context: "MatchContext"):
        pass

    def exit(self, context: "MatchContext"):
        pass

    @abstractmethod
    def get_allowed_transitions(self) -> list:
        pass

    def can_transition_to(self, state_name: str) -> bool:
        return state_name in self.get_allowed_transitions()

    def __repr__(self):
        return f"{self.name}State"


class ScheduledState(MatchState):
    @property
    def name(self) -> str:
        return "SCHEDULED"

    @property
    def color_key(self) -> str:
        return "AMBER"

    def get_allowed_transitions(self) -> list:
        return ["CHECK_IN", "CANCELLED"]


class CheckInState(MatchState):
    @property
    def name(self) -> str:
        return "CHECK_IN"

    @property
    def color_key(self) -> str:
        return "CYAN"

    def get_allowed_transitions(self) -> list:
        return ["LIVE", "CANCELLED"]


class LiveState(MatchState):
    @property
    def name(self) -> str:
        return "LIVE"

    @property
    def color_key(self) -> str:
        return "GREEN"

    @property
    def is_active(self) -> bool:
        return True

    def get_allowed_transitions(self) -> list:
        return ["OVERTIME", "COMPLETED", "CANCELLED", "DISPUTED"]


class OvertimeState(MatchState):
    @property
    def name(self) -> str:
        return "OVERTIME"

    @property
    def color_key(self) -> str:
        return "ACCENT"

    @property
    def is_active(self) -> bool:
        return True

    def get_allowed_transitions(self) -> list:
        return ["COMPLETED", "CANCELLED", "DISPUTED"]


class CompletedState(MatchState):
    @property
    def name(self) -> str:
        return "COMPLETED"

    @property
    def color_key(self) -> str:
        return "TEXT_MUTED"

    @property
    def is_terminal(self) -> bool:
        return True

    def get_allowed_transitions(self) -> list:
        return ["DISPUTED"]


class CancelledState(MatchState):
    @property
    def name(self) -> str:
        return "CANCELLED"

    @property
    def color_key(self) -> str:
        return "RED"

    @property
    def is_terminal(self) -> bool:
        return True

    def get_allowed_transitions(self) -> list:
        return []


class DisputedState(MatchState):
    @property
    def name(self) -> str:
        return "DISPUTED"

    @property
    def color_key(self) -> str:
        return "AMBER"

    def get_allowed_transitions(self) -> list:
        return ["LIVE", "COMPLETED", "CANCELLED"]


STATE_MAP = {
    "SCHEDULED": ScheduledState,
    "CHECK_IN": CheckInState,
    "LIVE": LiveState,
    "OVERTIME": OvertimeState,
    "COMPLETED": CompletedState,
    "CANCELLED": CancelledState,
    "DISPUTED": DisputedState,
}


class MatchContext:

    def __init__(self, match=None, initial_state: str = "SCHEDULED"):
        self._match = match
        state_cls = STATE_MAP.get(initial_state, ScheduledState)
        self._state: MatchState = state_cls()
        self._history: list = [self._state.name]
        self._on_transition = None

    @property
    def state(self) -> MatchState:
        return self._state

    @property
    def state_name(self) -> str:
        return self._state.name

    @property
    def match(self):
        return self._match

    @property
    def history(self) -> list:
        return list(self._history)

    def set_on_transition(self, callback):
        self._on_transition = callback

    def transition_to(self, state_name: str):
        if not self._state.can_transition_to(state_name):
            raise InvalidStateTransitionError(
                self._state.name, state_name
            )

        old_state = self._state
        new_state_cls = STATE_MAP.get(state_name)
        if new_state_cls is None:
            raise ValueError(f"Unknown state: {state_name}")

        new_state = new_state_cls()

        old_state.exit(self)
        self._state = new_state
        new_state.enter(self)
        self._history.append(state_name)

        if self._match is not None:
            from models.match import MatchStatus
            status_map = {
                "SCHEDULED": MatchStatus.SCHEDULED,
                "CHECK_IN": MatchStatus.CHECK_IN,
                "LIVE": MatchStatus.LIVE,
                "OVERTIME": MatchStatus.OVERTIME,
                "COMPLETED": MatchStatus.COMPLETED,
                "CANCELLED": MatchStatus.CANCELLED,
                "DISPUTED": MatchStatus.DISPUTED,
            }
            if state_name in status_map:
                self._match.status = status_map[state_name]

        if self._on_transition:
            try:
                self._on_transition(old_state.name, state_name)
            except Exception:
                pass


    def start_checkin(self):
        self.transition_to("CHECK_IN")

    def start_match(self):
        self.transition_to("LIVE")

    def go_overtime(self):
        self.transition_to("OVERTIME")

    def complete(self):
        self.transition_to("COMPLETED")

    def cancel(self):
        self.transition_to("CANCELLED")

    def dispute(self):
        self.transition_to("DISPUTED")

    def get_available_actions(self) -> list:
        action_map = {
            "CHECK_IN": "Start Check-in",
            "LIVE": "Start Match",
            "OVERTIME": "Overtime",
            "COMPLETED": "Complete",
            "CANCELLED": "Cancel",
            "DISPUTED": "Dispute",
        }
        allowed = self._state.get_allowed_transitions()
        return [action_map[s] for s in allowed if s in action_map]
