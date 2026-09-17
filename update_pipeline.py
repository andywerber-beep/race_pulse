import os
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
from database import supabase

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
API_HOST = "the-racing-api1.p.rapidapi.com"

def safe_int(value):
    """Safely convert API values like '-' or empty strings to None for integer columns."""
    if value is None or value == "" or value == "-":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def run_pipeline():
    """Fetches upcoming racecards across a rolling 7-day window and automatically populates Supabase tables."""
    if not RAPIDAPI_KEY:
        print("Error: RAPIDAPI_KEY not found in environment variables.")
        return

    url = f"https://{API_HOST}/v1/racecards"
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": API_HOST
    }

    # Generate a rolling 7-day window starting from today
    today = datetime.today()
    date_window = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    
    total_races_ingested = 0
    total_runners_ingested = 0

    print(f"Starting rolling 7-day pipeline fetch for dates: {date_window[0]} to {date_window[-1]}...")

    for target_date in date_window:
        querystring = {"date": target_date}
        print(f"Fetching racecards for date: {target_date}...")
        
        try:
            response = requests.get(url, headers=headers, params=querystring)
            
            # If the free tier blocks specific future dates, log it gracefully and continue
            if response.status_code != 200:
                print(f"Notice for {target_date}: API returned status {response.status_code} - {response.text}")
                continue

            data = response.json()
            races = data if isinstance(data, list) else data.get("racecards", [])
            
            if not races:
                print(f"No racecards found for {target_date}.")
                continue

            for race in races:
                course_name = race.get("course", "Unknown Course")
                race_date = race.get("date", target_date)
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
                total_races_ingested += 1
                
                # 3. Insert Runners linked to this race's ID with defensive fallback for horse names
                for runner in race.get("runners", []):
                    horse_name = (
                        runner.get("horse") or 
                        runner.get("name") or 
                        runner.get("horse_name") or 
                        runner.get("runner") or 
                        "Unknown Horse"
                    )

                    runner_payload = {
                        "race_id": race_id,
                        "horse_name": horse_name,
                        "trainer": runner.get("trainer", "Unknown"),
                        "jockey": runner.get("jockey", "Unknown"),
                        "form": str(runner.get("form", "")),
                        "age": safe_int(runner.get("age")),
                        "official_rating": safe_int(runner.get("ofr")),
                    }
                    supabase.table("runners").insert(runner_payload).execute()
                    total_runners_ingested += 1

        except Exception as e:
            print(f"Exception encountered while fetching {target_date}: {e}")

    print(f"Pipeline execution completed. Total ingested: {total_races_ingested} races and {total_runners_ingested} runners across the window.")

if __name__ == "__main__":
    run_pipeline()