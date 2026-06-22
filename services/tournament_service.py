from typing import List, Optional, Dict
from datetime import datetime, timedelta
import json
import os

from models.player import Player
from models.team import Team
from models.match import Match, MatchStatus, MatchResult
from patterns.factory import TournamentFactory, TournamentConfig, TournamentType
from patterns.observer import (
    MatchPublisher, MatchEvent, EventType,
    LoggingSubscriber, StatsSubscriber, NotificationSubscriber,
    BracketUpdateSubscriber, ObserverBridge,
)
from patterns.state import MatchContext, InvalidStateTransitionError, STATE_MAP
from patterns.strategy import EloStrategy


class TournamentService:

    def __init__(self):
        self.tournaments: Dict[str, dict] = {}
        self.active_tournament_id: Optional[str] = "default"
        self.tournaments["default"] = {
            "id": "default",
            "name": "EsportsHub Tournament",
            "game": "CS2",
            "type_name": "Single Elimination",
            "max_teams": 8,
            "teams": {},
            "matches": {},
            "match_contexts": {},
            "config": None,
            "bracket": None,
            "tournament_started": False
        }

        self.publisher = MatchPublisher()
        self.logging_sub = LoggingSubscriber()
        self.stats_sub = StatsSubscriber()
        self.notification_sub = NotificationSubscriber()
        self.bracket_sub = BracketUpdateSubscriber()
        self.observer_bridge: Optional[ObserverBridge] = None

        self.publisher.subscribe(self.logging_sub)
        self.publisher.subscribe(self.stats_sub)
        self.publisher.subscribe(self.notification_sub)
        self.publisher.subscribe(self.bracket_sub)

    @property
    def teams(self) -> Dict[str, Team]:
        return self.tournaments[self.active_tournament_id]["teams"]

    @teams.setter
    def teams(self, value):
        self.tournaments[self.active_tournament_id]["teams"] = value

    @property
    def matches(self) -> Dict[str, Match]:
        return self.tournaments[self.active_tournament_id]["matches"]

    @matches.setter
    def matches(self, value):
        self.tournaments[self.active_tournament_id]["matches"] = value

    @property
    def match_contexts(self) -> Dict[str, MatchContext]:
        return self.tournaments[self.active_tournament_id]["match_contexts"]

    @match_contexts.setter
    def match_contexts(self, value):
        self.tournaments[self.active_tournament_id]["match_contexts"] = value

    @property
    def config(self) -> Optional[TournamentConfig]:
        return self.tournaments[self.active_tournament_id]["config"]

    @config.setter
    def config(self, value):
        self.tournaments[self.active_tournament_id]["config"] = value

    @property
    def tournament_name(self) -> str:
        return self.tournaments[self.active_tournament_id]["name"]

    @tournament_name.setter
    def tournament_name(self, value):
        self.tournaments[self.active_tournament_id]["name"] = value

    @property
    def tournament_started(self) -> bool:
        return self.tournaments[self.active_tournament_id]["tournament_started"]

    @tournament_started.setter
    def tournament_started(self, value):
        self.tournaments[self.active_tournament_id]["tournament_started"] = value

    @property
    def bracket(self):
        return self.tournaments[self.active_tournament_id].get("bracket")

    @bracket.setter
    def bracket(self, value):
        self.tournaments[self.active_tournament_id]["bracket"] = value

    @property
    def game(self) -> str:
        return self.tournaments[self.active_tournament_id]["game"]

    @game.setter
    def game(self, value):
        self.tournaments[self.active_tournament_id]["game"] = value

    @property
    def type_name(self) -> str:
        return self.tournaments[self.active_tournament_id]["type_name"]

    @type_name.setter
    def type_name(self, value):
        self.tournaments[self.active_tournament_id]["type_name"] = value

    @property
    def max_teams(self) -> int:
        return self.tournaments[self.active_tournament_id]["max_teams"]

    @max_teams.setter
    def max_teams(self, value):
        self.tournaments[self.active_tournament_id]["max_teams"] = value

    def create_new_tournament(self, name: str, game: str, type_name: str, max_teams: int) -> str:
        t_id = f"t_{len(self.tournaments) + 1}"
        self.tournaments[t_id] = {
            "id": t_id,
            "name": name,
            "game": game,
            "type_name": type_name,
            "max_teams": max_teams,
            "teams": {},
            "matches": {},
            "match_contexts": {},
            "config": None,
            "bracket": None,
            "tournament_started": False
        }
        self.switch_tournament(t_id)
        return t_id

    def switch_tournament(self, tournament_id: str):
        if tournament_id not in self.tournaments:
            raise ValueError(f"Tournament {tournament_id} not found")
        self.active_tournament_id = tournament_id
        
        self.publisher.notify(MatchEvent(
            event_type=EventType.TOURNAMENT_STARTED,
            description=f"Switched to tournament '{self.tournament_name}'",
        ))

    def set_observer_bridge(self, bridge: ObserverBridge):
        self.observer_bridge = bridge
        self.publisher.subscribe(bridge)


    def register_team(self, team: Team) -> Team:
        if len(team.players) < 1:
            raise ValueError("Team must have at least 1 player")
        self.teams[team.id] = team
        self.publisher.notify(MatchEvent(
            event_type=EventType.TEAM_REGISTERED,
            description=f"Team '{team.name}' [{team.tag}] registered",
            team_id=team.id,
        ))
        return team

    def update_team(self, team: Team) -> Team:
        self.teams[team.id] = team
        self.publisher.notify(MatchEvent(
            event_type=EventType.TEAM_UPDATED,
            description=f"Team '{team.name}' updated",
            team_id=team.id,
        ))
        return team

    def remove_team(self, team_id: str):
        team = self.teams.pop(team_id, None)
        if team:
            self.publisher.notify(MatchEvent(
                event_type=EventType.TEAM_UPDATED,
                description=f"Team '{team.name}' removed",
                team_id=team_id,
            ))

    def get_team(self, team_id: str) -> Optional[Team]:
        return self.teams.get(team_id)

    def get_team_name(self, team_id: str) -> str:
        team = self.teams.get(team_id)
        return team.name if team else team_id

    def get_all_teams(self) -> List[Team]:
        return list(self.teams.values())

    def get_team_names_map(self) -> Dict[str, str]:
        return {tid: t.name for tid, t in self.teams.items()}


    def create_match(self, team1_id: str, team2_id: str,
                     game: str = "CS2", round_number: int = 1,
                     bracket_position: int = 0,
                     scheduled_time: str = "") -> Match:
        match = Match(
            team1_id=team1_id,
            team2_id=team2_id,
            game=game,
            round_number=round_number,
            bracket_position=bracket_position,
            scheduled_time=scheduled_time or datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
        self.matches[match.id] = match

        ctx = MatchContext(match, initial_state="SCHEDULED")
        ctx.set_on_transition(
            lambda from_s, to_s: self._on_match_state_change(match.id, from_s, to_s)
        )
        self.match_contexts[match.id] = ctx

        t1_name = self.get_team_name(team1_id)
        t2_name = self.get_team_name(team2_id)
        self.publisher.notify(MatchEvent(
            event_type=EventType.MATCH_CREATED,
            description=f"Match created: {t1_name} vs {t2_name}",
            match_id=match.id,
        ))
        return match

    def get_match(self, match_id: str) -> Optional[Match]:
        return self.matches.get(match_id)

    def get_match_context(self, match_id: str) -> Optional[MatchContext]:
        return self.match_contexts.get(match_id)

    def get_all_matches(self) -> List[Match]:
        return list(self.matches.values())

    def get_matches_by_status(self, status: MatchStatus) -> List[Match]:
        return [m for m in self.matches.values() if m.status == status]

    def get_live_matches(self) -> List[Match]:
        return [m for m in self.matches.values() if m.is_live]


    def update_score(self, match_id: str, score1: int, score2: int):
        match = self.matches.get(match_id)
        if match is None:
            raise ValueError(f"Match {match_id} not found")
        match.score1 = score1
        match.score2 = score2

        t1_name = self.get_team_name(match.team1_id)
        t2_name = self.get_team_name(match.team2_id)
        self.publisher.notify(MatchEvent(
            event_type=EventType.SCORE_UPDATED,
            description=f"Score update: {t1_name} {score1} - {score2} {t2_name}",
            match_id=match_id,
            data={"score1": score1, "score2": score2},
        ))

    def increment_score(self, match_id: str, team_num: int):
        match = self.matches.get(match_id)
        if match is None:
            return
        if team_num == 1:
            match.score1 += 1
        else:
            match.score2 += 1
        self.update_score(match_id, match.score1, match.score2)


    def transition_match(self, match_id: str, action: str):
        ctx = self.match_contexts.get(match_id)
        if ctx is None:
            raise ValueError(f"Match context {match_id} not found")

        action_map = {
            "start_checkin": "CHECK_IN",
            "start_match": "LIVE",
            "overtime": "OVERTIME",
            "complete": "COMPLETED",
            "cancel": "CANCELLED",
            "dispute": "DISPUTED",
        }
        target_state = action_map.get(action)
        if target_state is None:
            raise ValueError(f"Unknown action: {action}")

        ctx.transition_to(target_state)

        if target_state == "COMPLETED":
            match = self.matches[match_id]
            result = match.determine_result()
            self._apply_match_result(match, result)

    def get_available_actions(self, match_id: str) -> List[str]:
        ctx = self.match_contexts.get(match_id)
        if ctx is None:
            return []
        action_reverse = {
            "CHECK_IN": "start_checkin",
            "LIVE": "start_match",
            "OVERTIME": "overtime",
            "COMPLETED": "complete",
            "CANCELLED": "cancel",
            "DISPUTED": "dispute",
        }
        allowed = ctx.state.get_allowed_transitions()
        return [action_reverse[s] for s in allowed if s in action_reverse]

    def _on_match_state_change(self, match_id: str, from_state: str, to_state: str):
        match = self.matches.get(match_id)
        if not match:
            return
        t1 = self.get_team_name(match.team1_id)
        t2 = self.get_team_name(match.team2_id)

        event_map = {
            "CHECK_IN": (EventType.MATCH_CHECKIN, f"Check-in started: {t1} vs {t2}"),
            "LIVE": (EventType.MATCH_STARTED, f"Match LIVE: {t1} vs {t2}"),
            "OVERTIME": (EventType.MATCH_OVERTIME, f"OVERTIME: {t1} vs {t2}"),
            "COMPLETED": (EventType.MATCH_COMPLETED,
                          f"Match completed: {t1} {match.score1}-{match.score2} {t2}"),
            "CANCELLED": (EventType.MATCH_CANCELLED, f"Match cancelled: {t1} vs {t2}"),
            "DISPUTED": (EventType.MATCH_DISPUTED, f"Match disputed: {t1} vs {t2}"),
        }
        if to_state in event_map:
            evt_type, desc = event_map[to_state]
            self.publisher.notify(MatchEvent(
                event_type=evt_type,
                description=desc,
                match_id=match_id,
            ))

    def _apply_match_result(self, match: Match, result: MatchResult):
        team1 = self.teams.get(match.team1_id)
        team2 = self.teams.get(match.team2_id)

        if team1 and team2:
            if result == MatchResult.TEAM1_WIN:
                team1.record_win(3)
                team2.record_loss(0)
                new_elo1, new_elo2 = EloStrategy.calculate_new_elo(
                    team1.elo, team2.elo
                )
                team1.update_elo(new_elo1)
                team2.update_elo(new_elo2)
            elif result == MatchResult.TEAM2_WIN:
                team2.record_win(3)
                team1.record_loss(0)
                new_elo2, new_elo1 = EloStrategy.calculate_new_elo(
                    team2.elo, team1.elo
                )
                team1.update_elo(new_elo1)
                team2.update_elo(new_elo2)
            elif result == MatchResult.DRAW:
                team1.record_draw(1)
                team2.record_draw(1)


    def configure_tournament(self, type_name: str, name: str = "",
                             game: str = "CS2", max_teams: int = 8) -> TournamentConfig:
        self.config = TournamentFactory.create(
            type_name, name=name or self.tournament_name,
            game=game, max_teams=max_teams,
        )
        self.tournament_name = name or self.tournament_name
        return self.config

    def start_tournament(self) -> bool:
        if len(self.teams) < 2:
            raise ValueError("Need at least 2 teams to start tournament")
        if self.config is None:
            self.configure_tournament("Single Elimination",
                                      max_teams=len(self.teams))
        self.tournament_started = True
        self.publisher.notify(MatchEvent(
            event_type=EventType.TOURNAMENT_STARTED,
            description=f"Tournament '{self.tournament_name}' started with {len(self.teams)} teams",
        ))
        return True


    def get_stats(self) -> dict:
        active_count = sum(1 for t in self.tournaments.values() if t.get("tournament_started"))
        return {
            "active_tournaments": active_count,
            "total_teams": len(self.teams),
            "matches_today": len([
                m for m in self.matches.values()
                if m.scheduled_time.startswith(datetime.now().strftime("%Y-%m-%d"))
            ]),
            "pending_results": len(self.get_matches_by_status(MatchStatus.SCHEDULED)) +
                               len(self.get_matches_by_status(MatchStatus.CHECK_IN)),
            "live_matches": len(self.get_live_matches()),
            "completed_matches": len(self.get_matches_by_status(MatchStatus.COMPLETED)),
        }


    def export_data(self) -> dict:
        return {
            "tournament_name": self.tournament_name,
            "tournament_started": self.tournament_started,
            "config": {
                "type": self.config.tournament_type.value if self.config else "",
                "game": self.config.game if self.config else "CS2",
                "max_teams": self.config.max_teams if self.config else 8,
            } if self.config else None,
            "teams": [t.to_dict() for t in self.teams.values()],
            "matches": [m.to_dict() for m in self.matches.values()],
        }

    def export_json(self, filepath: str):
        with open(filepath, "w") as f:
            json.dump(self.export_data(), f, indent=2)

    def reset(self):
        self.teams.clear()
        self.matches.clear()
        self.match_contexts.clear()
        self.config = None
        self.tournament_started = False
        self.logging_sub.clear()
        self.notification_sub.notifications.clear()
        self.notification_sub.unread_count = 0
        self.tournaments.clear()
        self.active_tournament_id = "default"
        self.tournaments["default"] = {
            "id": "default",
            "name": "EsportsHub Tournament",
            "game": "CS2",
            "type_name": "Single Elimination",
            "max_teams": 8,
            "teams": {},
            "matches": {},
            "match_contexts": {},
            "config": None,
            "tournament_started": False
        }

    def search(self, query: str) -> List[dict]:
        results = []
        q = query.lower().strip()
        if not q:
            return results
        for team in self.teams.values():
            if q in team.name.lower() or q in team.tag.lower():
                results.append({"type": "team", "item": team, "label": str(team)})
        for match in self.matches.values():
            t1 = self.get_team_name(match.team1_id)
            t2 = self.get_team_name(match.team2_id)
            label = f"{t1} vs {t2}"
            if q in label.lower() or q in match.id.lower():
                results.append({"type": "match", "item": match, "label": label})
        return results
