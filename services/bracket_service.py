from typing import List, Optional, Dict
from patterns.composite import TournamentBracket, MatchNode, RoundNode


class BracketService:

    def __init__(self, tournament_service=None):
        self._tournament_service = tournament_service
        self._local_bracket = TournamentBracket()
        self._match_factory = None

    @property
    def bracket(self) -> TournamentBracket:
        if self._tournament_service and self._tournament_service.active_tournament_id:
            b = self._tournament_service.bracket
            if b is None:
                b = TournamentBracket()
                self._tournament_service.bracket = b
            return b
        return self._local_bracket

    @bracket.setter
    def bracket(self, value):
        if self._tournament_service and self._tournament_service.active_tournament_id:
            self._tournament_service.bracket = value
        else:
            self._local_bracket = value

    def set_match_factory(self, factory_fn):
        self._match_factory = factory_fn

    def generate_bracket(self, team_ids: List[str],
                         team_names: Dict[str, str] = None) -> TournamentBracket:
        self.bracket = TournamentBracket()
        self.bracket.build(
            team_ids=team_ids,
            team_names=team_names or {},
            match_factory=self._match_factory,
        )
        return self.bracket

    def get_bracket_data(self) -> List[dict]:
        data = []
        for round_node in self.bracket.rounds:
            round_data = {
                "round_number": round_node.round_number,
                "name": round_node.name,
                "matches": [],
            }
            for child in round_node.children:
                if isinstance(child, MatchNode):
                    match_data = {
                        "position": child.position,
                        "team1_name": child.team1_name,
                        "team2_name": child.team2_name,
                        "match": child.match,
                        "winner": child.get_winner(),
                    }
                    if child.match:
                        match_data["match_id"] = child.match.id
                        match_data["score1"] = child.match.score1
                        match_data["score2"] = child.match.score2
                        match_data["status"] = child.match.status.value
                    round_data["matches"].append(match_data)
            data.append(round_data)
        return data

    def advance_winner(self, match_id: str, winner_id: str):
        self.bracket.advance_winner(match_id, winner_id)

    def get_match_node(self, match_id: str) -> Optional[MatchNode]:
        return self.bracket.match_node_map.get(match_id)

    @property
    def total_rounds(self) -> int:
        return self.bracket.total_rounds

    @property
    def total_matches(self) -> int:
        return self.bracket.total_matches

    def get_all_matches(self) -> list:
        return self.bracket.get_all_matches()

    def reset(self):
        self.bracket = TournamentBracket()
