import unittest
from patterns.observer import (
    MatchPublisher, MatchEvent, EventType,
    MatchEventSubscriber, LoggingSubscriber, StatsSubscriber,
    NotificationSubscriber, BracketUpdateSubscriber,
)


class MockSubscriber(MatchEventSubscriber):

    def __init__(self):
        self.events = []

    def on_event(self, event):
        self.events.append(event)


class TestMatchPublisher(unittest.TestCase):

    def test_subscribe(self):
        pub = MatchPublisher()
        sub = MockSubscriber()
        pub.subscribe(sub)
        self.assertEqual(pub.subscriber_count, 1)

    def test_unsubscribe(self):
        pub = MatchPublisher()
        sub = MockSubscriber()
        pub.subscribe(sub)
        pub.unsubscribe(sub)
        self.assertEqual(pub.subscriber_count, 0)

    def test_notify(self):
        pub = MatchPublisher()
        sub = MockSubscriber()
        pub.subscribe(sub)
        event = MatchEvent(event_type=EventType.MATCH_CREATED, description="Test")
        pub.notify(event)
        self.assertEqual(len(sub.events), 1)
        self.assertEqual(sub.events[0].description, "Test")

    def test_multiple_subscribers(self):
        pub = MatchPublisher()
        sub1 = MockSubscriber()
        sub2 = MockSubscriber()
        pub.subscribe(sub1)
        pub.subscribe(sub2)
        pub.notify(MatchEvent(event_type=EventType.MATCH_STARTED, description="Go"))
        self.assertEqual(len(sub1.events), 1)
        self.assertEqual(len(sub2.events), 1)

    def test_no_duplicate_subscribe(self):
        pub = MatchPublisher()
        sub = MockSubscriber()
        pub.subscribe(sub)
        pub.subscribe(sub)
        self.assertEqual(pub.subscriber_count, 1)

    def test_subscriber_error_doesnt_crash(self):
        pub = MatchPublisher()

        class FailingSub(MatchEventSubscriber):
            def on_event(self, event):
                raise RuntimeError("Boom")

        good = MockSubscriber()
        pub.subscribe(FailingSub())
        pub.subscribe(good)
        pub.notify(MatchEvent(event_type=EventType.MATCH_COMPLETED, description="OK"))
        self.assertEqual(len(good.events), 1)


class TestLoggingSubscriber(unittest.TestCase):
    def test_logs_events(self):
        sub = LoggingSubscriber()
        sub.on_event(MatchEvent(event_type=EventType.MATCH_STARTED, description="M1"))
        sub.on_event(MatchEvent(event_type=EventType.MATCH_COMPLETED, description="M2"))
        self.assertEqual(len(sub.logs), 2)

    def test_get_recent(self):
        sub = LoggingSubscriber()
        for i in range(30):
            sub.on_event(MatchEvent(event_type=EventType.SCORE_UPDATED, description=f"E{i}"))
        recent = sub.get_recent(5)
        self.assertEqual(len(recent), 5)

    def test_clear(self):
        sub = LoggingSubscriber()
        sub.on_event(MatchEvent(event_type=EventType.MATCH_STARTED, description="X"))
        sub.clear()
        self.assertEqual(len(sub.logs), 0)


class TestStatsSubscriber(unittest.TestCase):
    def test_counts_events(self):
        sub = StatsSubscriber()
        sub.on_event(MatchEvent(event_type=EventType.MATCH_STARTED, description=""))
        sub.on_event(MatchEvent(event_type=EventType.MATCH_STARTED, description=""))
        sub.on_event(MatchEvent(event_type=EventType.MATCH_COMPLETED, description=""))
        self.assertEqual(sub.get_count(EventType.MATCH_STARTED), 2)
        self.assertEqual(sub.get_count(EventType.MATCH_COMPLETED), 1)
        self.assertEqual(sub.total, 3)


class TestNotificationSubscriber(unittest.TestCase):
    def test_unread_count(self):
        sub = NotificationSubscriber()
        sub.on_event(MatchEvent(event_type=EventType.MATCH_CREATED, description=""))
        sub.on_event(MatchEvent(event_type=EventType.TEAM_REGISTERED, description=""))
        self.assertEqual(sub.unread_count, 2)

    def test_mark_all_read(self):
        sub = NotificationSubscriber()
        sub.on_event(MatchEvent(event_type=EventType.MATCH_CREATED, description=""))
        sub.mark_all_read()
        self.assertEqual(sub.unread_count, 0)


class TestBracketUpdateSubscriber(unittest.TestCase):
    def test_pending_updates(self):
        sub = BracketUpdateSubscriber()
        sub.on_event(MatchEvent(event_type=EventType.MATCH_COMPLETED,
                                description="", match_id="m1"))
        self.assertEqual(len(sub.pending_updates), 1)

    def test_ignores_non_completion(self):
        sub = BracketUpdateSubscriber()
        sub.on_event(MatchEvent(event_type=EventType.MATCH_STARTED,
                                description="", match_id="m1"))
        self.assertEqual(len(sub.pending_updates), 0)

    def test_callback(self):
        sub = BracketUpdateSubscriber()
        called_with = []
        sub.set_callback(lambda mid: called_with.append(mid))
        sub.on_event(MatchEvent(event_type=EventType.MATCH_COMPLETED,
                                description="", match_id="m99"))
        self.assertEqual(called_with, ["m99"])


class TestMatchEvent(unittest.TestCase):
    def test_event_color_completed(self):
        e = MatchEvent(event_type=EventType.MATCH_COMPLETED, description="")
        self.assertEqual(e.color, "GREEN")

    def test_event_color_started(self):
        e = MatchEvent(event_type=EventType.MATCH_STARTED, description="")
        self.assertEqual(e.color, "AMBER")

    def test_event_color_cancelled(self):
        e = MatchEvent(event_type=EventType.MATCH_CANCELLED, description="")
        self.assertEqual(e.color, "RED")

    def test_event_timestamp(self):
        e = MatchEvent(event_type=EventType.MATCH_CREATED, description="")
        self.assertIsNotNone(e.timestamp)


if __name__ == "__main__":
    unittest.main()
