import os
from datetime import datetime
import requests
from dotenv import load_dotenv
from database import supabase

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
API_HOST = "the-racing-api1.p.rapidapi.com"

def safe_int(value):
    if value is None or value == "" or value == "-":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def run_pipeline():
    if not RAPIDAPI_KEY:
        print("Error: RAPIDAPI_KEY not found in environment variables.")
        return

    url = f"https://{API_HOST}/v1/racecards/free"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": API_HOST
    }

    days_to_fetch = ["today", "tomorrow"]
    total_races_ingested = 0
    total_runners_ingested = 0

    for day_param in days_to_fetch:
        querystring = {"day": day_param}
        print(f"Fetching racecards for '{day_param}'...")
        
        try:
            response = requests.get(url, headers=headers, params=querystring)
            if response.status_code != 200:
                print(f"API Error for {day_param}: {response.status_code} - {response.text}")
                continue

            data = response.json()
            races = data if isinstance(data, list) else data.get("racecards", [])
            
            if not races:
                print(f"No racecards found for {day_param}.")
                continue

            today_str = datetime.today().strftime('%Y-%m-%d')
            
            for race in races:
                course_name = race.get("course", "Unknown Course")
                race_date = race.get("date", today_str)
                off_time = race.get("off_time", "00:00")
                race_name = race.get("race_name", "Standard Race")
                class_run = str(race.get("class", "Class N/A"))
                going = race.get("going", "Unknown")

                # 1. Upsert Venue
                venue_data = {"venue_name": course_name, "surface_type": going}
                venue_res = supabase.table("venues").upsert(venue_data, on_conflict="venue_name").select("id").execute()
                
                if not venue_res.data:
                    print(f"Skipping race at {course_name} - Failed to get venue ID.")
                    continue
                    
                venue_id = venue_res.data[0].get("id")

                # 2. Insert Race
                race_payload = {
                    "venue_id": venue_id,
                    "course_name": course_name,
                    "race_date": race_date,
                    "off_time": off_time,
                    "race_time": off_time,
                    "race_name": race_name,
                    "class_run": class_run
                }
                race_res = supabase.table("races").insert(race_payload).select("id").execute()
                
                if not race_res.data:
                    print(f"Skipping runners for {race_name} - Failed to get race ID.")
                    continue

                race_id = race_res.data[0].get("id")
                total_races_ingested += 1
                
                # 3. Insert Runners with mapped missing columns
                for runner in race.get("runners", []):
                    horse_name = runner.get("horse") or "Unknown Horse"
                    trainer_name = runner.get("trainer") or "Unknown"
                    jockey_name = runner.get("jockey") or "Unknown"
                    form_str = str(runner.get("form", ""))

                    runner_payload = {
                        "race_id": race_id,
                        "horse_name": horse_name,
                        "trainer": trainer_name,
                        "jockey": jockey_name,
                        "form": form_str,
                        "age": safe_int(runner.get("age")),
                        "official_rating": safe_int(runner.get("ofr")),
                        "weight_carried_lbs": safe_int(runner.get("lbs")),
                        "days_since_last_run": safe_int(runner.get("last_run")),
                        "equipment": runner.get("headgear") or None,
                    }
                    
                    supabase.table("runners").insert(runner_payload).execute()
                    total_runners_ingested += 1

        except Exception as e:
            print(f"Exception encountered while fetching {day_param}: {e}")

    print(f"Pipeline execution completed. Total successfully inserted: {total_races_ingested} races and {total_runners_ingested} runners.")

if __name__ == "__main__":
    run_pipeline()