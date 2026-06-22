from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
import math


class BracketNode(ABC):

    @abstractmethod
    def get_winner(self) -> Optional[str]:
        pass

    @abstractmethod
    def get_matches(self) -> list:
        pass

    @abstractmethod
    def get_depth(self) -> int:
        pass

    @abstractmethod
    def get_all_nodes(self) -> List["BracketNode"]:
        pass


class MatchNode(BracketNode):

    def __init__(self, match=None, position: int = 0, round_num: int = 1):
        self.match = match
        self.position = position
        self.round_num = round_num
        self.team1_name: str = ""
        self.team2_name: str = ""

    def get_winner(self) -> Optional[str]:
        if self.match is None:
            return None
        if self.match.winner_id:
            return self.match.winner_id
        return None

    def get_matches(self) -> list:
        return [self.match] if self.match else []

    def get_depth(self) -> int:
        return 1

    def get_all_nodes(self) -> List[BracketNode]:
        return [self]

    def __repr__(self):
        if self.match:
            return f"MatchNode(R{self.round_num}P{self.position}: {self.team1_name} vs {self.team2_name})"
        return f"MatchNode(R{self.round_num}P{self.position}: TBD)"


class RoundNode(BracketNode):

    def __init__(self, round_number: int = 1, name: str = ""):
        self.round_number = round_number
        self.name = name or f"Round {round_number}"
        self.children: List[BracketNode] = []

    def add_child(self, node: BracketNode):
        self.children.append(node)

    def remove_child(self, node: BracketNode):
        self.children = [c for c in self.children if c is not node]

    def get_winner(self) -> Optional[str]:
        return None

    def get_matches(self) -> list:
        matches = []
        for child in self.children:
            matches.extend(child.get_matches())
        return matches

    def get_depth(self) -> int:
        if not self.children:
            return 1
        return 1 + max(child.get_depth() for child in self.children)

    def get_all_nodes(self) -> List[BracketNode]:
        nodes = [self]
        for child in self.children:
            nodes.extend(child.get_all_nodes())
        return nodes

    @property
    def match_count(self) -> int:
        return sum(1 for child in self.children if isinstance(child, MatchNode))

    def __repr__(self):
        return f"RoundNode({self.name}, {len(self.children)} children)"


class TournamentBracket:

    def __init__(self):
        self.rounds: List[RoundNode] = []
        self.team_ids: List[str] = []
        self.team_names: dict = {}
        self.match_node_map: dict = {}

    def build(self, team_ids: List[str], team_names: dict = None,
              match_factory=None):
        self.team_ids = list(team_ids)
        self.team_names = team_names or {}
        self.rounds.clear()
        self.match_node_map.clear()

        n = len(team_ids)
        if n < 2:
            return

        n_padded = 1
        while n_padded < n:
            n_padded *= 2

        padded_ids = list(team_ids) + ["BYE"] * (n_padded - n)
        num_rounds = int(math.log2(n_padded))

        round_names = self._get_round_names(num_rounds)

        r1 = RoundNode(round_number=1, name=round_names[0])
        for i in range(0, n_padded, 2):
            t1 = padded_ids[i]
            t2 = padded_ids[i + 1]
            match = None
            if match_factory and t1 != "BYE" and t2 != "BYE":
                match = match_factory(t1, t2, 1, i // 2)
            node = MatchNode(match=match, position=i // 2, round_num=1)
            node.team1_name = self.team_names.get(t1, t1)
            node.team2_name = self.team_names.get(t2, t2)
            if match:
                self.match_node_map[match.id] = node
            if t2 == "BYE" and match is None:
                node.team2_name = "BYE"
            if t1 == "BYE" and match is None:
                node.team1_name = "BYE"
            r1.add_child(node)
        self.rounds.append(r1)

        for r in range(2, num_rounds + 1):
            round_node = RoundNode(
                round_number=r,
                name=round_names[r - 1] if r - 1 < len(round_names) else f"Round {r}"
            )
            matches_in_round = n_padded // (2 ** r)
            for pos in range(matches_in_round):
                match = None
                if match_factory:
                    match = match_factory("", "", r, pos)
                node = MatchNode(match=match, position=pos, round_num=r)
                node.team1_name = "TBD"
                node.team2_name = "TBD"
                if match:
                    self.match_node_map[match.id] = node
                round_node.add_child(node)
            self.rounds.append(round_node)

    def _get_round_names(self, num_rounds: int) -> List[str]:
        names = []
        for i in range(num_rounds):
            remaining = num_rounds - i
            if remaining == 1:
                names.append("Grand Final")
            elif remaining == 2:
                names.append("Semifinals")
            elif remaining == 3:
                names.append("Quarterfinals")
            else:
                names.append(f"Round {i + 1}")
        return names

    def get_all_matches(self) -> list:
        matches = []
        for round_node in self.rounds:
            matches.extend(round_node.get_matches())
        return matches

    def get_round(self, round_number: int) -> Optional[RoundNode]:
        for r in self.rounds:
            if r.round_number == round_number:
                return r
        return None

    def get_match_nodes_by_round(self, round_number: int) -> List[MatchNode]:
        r = self.get_round(round_number)
        if r is None:
            return []
        return [c for c in r.children if isinstance(c, MatchNode)]

    @property
    def total_rounds(self) -> int:
        return len(self.rounds)

    @property
    def total_matches(self) -> int:
        return sum(len(r.get_matches()) for r in self.rounds)

    def advance_winner(self, match_id: str, winner_id: str):
        node = self.match_node_map.get(match_id)
        if node is None:
            return
        round_num = node.round_num
        position = node.position

        next_round = self.get_round(round_num + 1)
        if next_round is None:
            return

        next_position = position // 2
        next_nodes = [c for c in next_round.children if isinstance(c, MatchNode)]
        for nn in next_nodes:
            if nn.position == next_position:
                winner_name = self.team_names.get(winner_id, winner_id)
                if position % 2 == 0:
                    nn.team1_name = winner_name
                    if nn.match:
                        nn.match.team1_id = winner_id
                else:
                    nn.team2_name = winner_name
                    if nn.match:
                        nn.match.team2_id = winner_id
                break
