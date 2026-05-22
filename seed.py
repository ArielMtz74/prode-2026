from models import init_db, SessionLocal, Match
from datetime import datetime, timedelta

def seed_matches():
    db = SessionLocal()
    # Check if matches already exist
    if db.query(Match).count() > 0:
        print("Matches already seeded.")
        db.close()
        return

    groups = {
        'A': ['México', 'Equipo A2', 'Equipo A3', 'Equipo A4'],
        'B': ['Canadá', 'Equipo B2', 'Equipo B3', 'Equipo B4'],
        'C': ['EEUU', 'Equipo C2', 'Equipo C3', 'Equipo C4'],
        'D': ['Argentina', 'Equipo D2', 'Equipo D3', 'Equipo D4'],
        'E': ['Brasil', 'Equipo E2', 'Equipo E3', 'Equipo E4'],
        'F': ['Francia', 'Equipo F2', 'Equipo F3', 'Equipo F4'],
        'G': ['España', 'Equipo G2', 'Equipo G3', 'Equipo G4'],
        'H': ['Inglaterra', 'Equipo H2', 'Equipo H3', 'Equipo H4'],
        'I': ['Alemania', 'Equipo I2', 'Equipo I3', 'Equipo I4'],
        'J': ['Portugal', 'Equipo J2', 'Equipo J3', 'Equipo J4'],
        'K': ['Italia', 'Equipo K2', 'Equipo K3', 'Equipo K4'],
        'L': ['Colombia', 'Equipo L2', 'Equipo L3', 'Equipo L4'],
    }

    start_date = datetime(2026, 6, 11, 15, 0) # Inaugural match date
    
    for group_name, teams in groups.items():
        # 6 matches per group (Round robin: 1v2, 3v4, 1v3, 2v4, 1v4, 2v3)
        matchups = [
            (0, 1), (2, 3), # Matchday 1
            (0, 2), (1, 3), # Matchday 2
            (0, 3), (1, 2)  # Matchday 3
        ]
        
        for i, (t1_idx, t2_idx) in enumerate(matchups):
            match = Match(
                group=group_name,
                team_a=teams[t1_idx],
                team_b=teams[t2_idx],
                date=start_date + timedelta(days=ord(group_name)-65 + i) # Just offset dates for testing
            )
            db.add(match)
            
    db.commit()
    print("Database seeded with 72 group stage matches.")
    db.close()

if __name__ == "__main__":
    init_db()
    seed_matches()
