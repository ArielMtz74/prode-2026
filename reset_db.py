import os
import pandas as pd
from models import init_db, SessionLocal, Match
from datetime import datetime

def reset_and_seed():
    init_db()
    db = SessionLocal()
    
    # Clear matches table instead of deleting db file
    db.query(Match).delete()
    db.commit()
    db = SessionLocal()
    
    df = pd.read_csv('matches.csv')
    
    for index, row in df.iterrows():
        # parse date DD/MM/YYYY
        date_obj = datetime.strptime(row['Fecha'], '%d/%m/%Y')
        
        match = Match(
            group=row['Grupo'],
            team_a=row['Equipo Local'],
            flag_a=row['Bandera Local'],
            team_b=row['Equipo Visitante'],
            flag_b=row['Bandera Visitante'],
            date=date_obj,
            time=row['Hora'],
            stadium=row['Estadio']
        )
        db.add(match)
        
    db.commit()
    print(f"Database seeded with {len(df)} real group stage matches.")
    db.close()

if __name__ == "__main__":
    reset_and_seed()
