import sys
from datetime import date
from database import fetch_todays_races, fetch_runners_for_race

def run_model():
    # Automatically use today's date, or accept a date passed via command line
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    else:
        target_date = date.today().strftime("%Y-%m-%d")

    print(f"Running value-bet model for date: {target_date}...")

    races = fetch_todays_races(target_date)
    
    if not races:
        print(f"No races found in the database for date: {target_date}.")
        return

    print(f"Found {len(races)} races. Processing analytics...")
    
    for race in races:
        race_id = race.get("id")
        runners = fetch_runners_for_race(race_id)
        # Add your model evaluation/value-bet logic here
        print(f"Processing race {race_id} with {len(runners)} runners.")

if __name__ == "__main__":
    run_model()