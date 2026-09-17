import os
from datetime import datetime
import requests
from dotenv import load_dotenv
from database import supabase

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
API_HOST = "the-racing-api1.p.rapidapi.com"

def run_pipeline():
    """Fetches upcoming racecards and automatically populates Supabase tables."""
    if not RAPIDAPI_KEY:
        print("Error: RAPIDAPI_KEY not found in environment variables.")
        return

    url = f"https://{API_HOST}/v1/racecards/free"
    querystring = {"day": "today"}
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": API_HOST
    }

    print("Fetching live racecards from API...")
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code != 200:
            print(f"API Error: {response.status_code} - {response.text}")
            return

        data = response.json()
        races = data if isinstance(data, list) else data.get("racecards", [])
        
        if not races:
            print("No racecards found for ingestion.")
            return

        today_str = datetime.today().strftime('%Y-%m-%d')
        total_runners = 0
        
        for race in races:
            course_name = race.get("course", "Unknown Course")
            race_date = race.get("date", today_str)
            off_time = race.get("off_time", "00:00")
            race_name = race.get("race_name", "Standard Race")
            class_run = str(race.get("class", "Class N/A"))
            going = race.get("going", "Unknown")

            # 1. Upsert Venue and retrieve its generated ID
            venue_data = {
                "venue_name": course_name,
                "surface_type": going
            }
            venue_res = supabase.table("venues").upsert(venue_data, on_conflict="venue_name").select("id").execute()
            venue_id = venue_res.data[0].get("id") if venue_res.data else None

            # 2. Insert Race and retrieve its generated ID
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
            race_id = race_res.data[0].get("id") if race_res.data else None
            
            # 3. Insert Runners linked to this race's ID
            for runner in race.get("runners", []):
                runner_payload = {
                    "race_id": race_id,
                    "horse_name": runner.get("horse_name", "Unknown Horse"),
                    "trainer": runner.get("trainer", "Unknown"),
                    "jockey": runner.get("jockey", "Unknown"),
                    "form": runner.get("form", ""),
                    "age": runner.get("age"),
                    "official_rating": runner.get("ofr"),
                }
                supabase.table("runners").insert(runner_payload).execute()
                total_runners += 1

        print(f"Pipeline execution successful. Ingested data for {len(races)} races and {total_runners} runners.")

    except Exception as e:
        print(f"Exception during pipeline execution: {e}")

if __name__ == "__main__":
    run_pipeline()