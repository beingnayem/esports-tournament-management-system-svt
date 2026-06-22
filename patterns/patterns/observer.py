from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Callable, Optional
from enum import Enum


class EventType(Enum):
    MATCH_CREATED = "match_created"
    MATCH_CHECKIN = "match_checkin"
    MATCH_STARTED = "match_started"
    SCORE_UPDATED = "score_updated"
    MATCH_OVERTIME = "match_overtime"
    MATCH_COMPLETED = "match_completed"
    MATCH_CANCELLED = "match_cancelled"
    MATCH_DISPUTED = "match_disputed"
    TEAM_REGISTERED = "team_registered"
    TEAM_UPDATED = "team_updated"
    TOURNAMENT_STARTED = "tournament_started"
    BRACKET_UPDATED = "bracket_updated"


@dataclass
class MatchEvent:
    event_type: EventType
    description: str
    match_id: str = ""
    team_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    data: dict = field(default_factory=dict)

    @property
    def color(self) -> str:
        completed = {EventType.MATCH_COMPLETED, EventType.TEAM_REGISTERED, EventType.TOURNAMENT_STARTED}
        started = {EventType.MATCH_STARTED, EventType.MATCH_CHECKIN, EventType.SCORE_UPDATED,
                   EventType.MATCH_OVERTIME, EventType.BRACKET_UPDATED}
        cancelled = {EventType.MATCH_CANCELLED, EventType.MATCH_DISPUTED}
        if self.event_type in completed:
            return "GREEN"
        elif self.event_type in started:
            return "AMBER"
        elif self.event_type in cancelled:
            return "RED"
        return "CYAN"


class MatchEventSubscriber(ABC):

    @abstractmethod
    def on_event(self, event: MatchEvent):
        pass


class LoggingSubscriber(MatchEventSubscriber):

    def __init__(self):
        self.logs: List[MatchEvent] = []

    def on_event(self, event: MatchEvent):
        self.logs.append(event)

    def get_recent(self, count: int = 20) -> List[MatchEvent]:
        return self.logs[-count:]

    def clear(self):
        self.logs.clear()


class StatsSubscriber(MatchEventSubscriber):

    def __init__(self):
        self.counts: dict = {et.value: 0 for et in EventType}
        self.total = 0

    def on_event(self, event: MatchEvent):
        self.counts[event.event_type.value] = self.counts.get(event.event_type.value, 0) + 1
        self.total += 1

    def get_count(self, event_type: EventType) -> int:
        return self.counts.get(event_type.value, 0)


class NotificationSubscriber(MatchEventSubscriber):

    def __init__(self):
        self.notifications: List[MatchEvent] = []
        self.unread_count: int = 0

    def on_event(self, event: MatchEvent):
        self.notifications.append(event)
        self.unread_count += 1

    def mark_all_read(self):
        self.unread_count = 0

    def get_unread(self) -> List[MatchEvent]:
        return self.notifications[-self.unread_count:] if self.unread_count > 0 else []


class BracketUpdateSubscriber(MatchEventSubscriber):

    def __init__(self):
        self.pending_updates: List[str] = []
        self._callback: Optional[Callable] = None

    def set_callback(self, callback: Callable):
        self._callback = callback

    def on_event(self, event: MatchEvent):
        if event.event_type == EventType.MATCH_COMPLETED:
            self.pending_updates.append(event.match_id)
            if self._callback:
                self._callback(event.match_id)


class MatchPublisher:

    def __init__(self):
        self._subscribers: List[MatchEventSubscriber] = []

    def subscribe(self, subscriber: MatchEventSubscriber):
        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)

    def unsubscribe(self, subscriber: MatchEventSubscriber):
        self._subscribers = [s for s in self._subscribers if s is not subscriber]

    def notify(self, event: MatchEvent):
        for sub in self._subscribers:
            try:
                sub.on_event(event)
            except Exception:
                pass

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


class ObserverBridge(MatchEventSubscriber):

    def __init__(self, root=None):
        self._root = root
        self._gui_callbacks: List[Callable] = []

    def set_root(self, root):
        self._root = root

    def add_gui_callback(self, callback: Callable):
        self._gui_callbacks.append(callback)

    def remove_gui_callback(self, callback: Callable):
        self._gui_callbacks = [cb for cb in self._gui_callbacks if cb is not callback]

    def on_event(self, event: MatchEvent):
        if self._root is None:
            return
        for cb in self._gui_callbacks:
            try:
                self._root.after(0, lambda c=cb, e=event: c(e))
            except Exception:
                pass
