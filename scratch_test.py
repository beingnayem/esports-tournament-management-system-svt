import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
os.environ["DISPLAY"] = ""

from gui.app import EsportsApp

class HeadlessEsportsApp(EsportsApp):
    def __init__(self):
        pass

def test_flow():
    from services.tournament_service import TournamentService
    from services.bracket_service import BracketService
    
    service = TournamentService()
    bracket_service = BracketService(tournament_service=service)
    
    print("Initial tournaments:", list(service.tournaments.keys()))
    print("Initial active ID:", service.active_tournament_id)
    print("Initial active name:", service.tournament_name)
    
    t_id = service.create_new_tournament("Pro League", "CS2", "Single Elimination", 8)
    print("\nAfter creation:")
    print("Tournaments list:", list(service.tournaments.keys()))
    print("Active tournament ID:", service.active_tournament_id)
    print("Active tournament name:", service.tournament_name)
    print("Active tournament teams:", service.teams)
    print("Active tournament matches:", service.matches)
    print("Active tournament started:", service.tournament_started)
    
    try:
        service.start_tournament()
        print("Started tournament successfully!")
    except Exception as e:
        print("Start tournament failed as expected:", e)
        
    from models.team import Team
    from models.player import Player
    t1 = Team(name="Alpha", tag="ALP", region="NA", players=[Player(username="p1")])
    t2 = Team(name="Beta", tag="BET", region="NA", players=[Player(username="p2")])
    service.register_team(t1)
    service.register_team(t2)
    
    print("\nAfter registering 2 teams:")
    print("Teams count:", len(service.teams))
    
    service.configure_tournament("Single Elimination", name="Pro League", game="CS2", max_teams=8)
    service.start_tournament()
    print("Tournament started:", service.tournament_started)
    
    team_ids = [t.id for t in service.get_all_teams()]
    team_names = {t.id: t.name for t in service.get_all_teams()}
    
    def match_factory(t1_id, t2_id, round_num, position):
        return service.create_match(t1_id or "", t2_id or "", "CS2", round_num, position)
        
    bracket_service.set_match_factory(match_factory)
    bracket_service.generate_bracket(team_ids, team_names)
    
    print("\nAfter starting and generating matches:")
    print("Matches count:", len(service.matches))
    print("Bracket matches:", len(bracket_service.bracket.get_all_matches()))
    
    service.switch_tournament("default")
    print("\nAfter switching back to default:")
    print("Active ID:", service.active_tournament_id)
    print("Active name:", service.tournament_name)
    print("Teams count:", len(service.teams))
    print("Matches count:", len(service.matches))

if __name__ == "__main__":
    test_flow()
