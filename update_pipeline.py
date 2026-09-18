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

    # Let's test with just 'today' first to keep logs clean and fast
    querystring = {"day": "today"}
    print("Fetching racecards for 'today' to test database ingestion...")
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code != 200:
            print(f"API Error: {response.status_code} - {response.text}")
            return

        data = response.json()
        races = data if isinstance(data, list) else data.get("racecards", [])
        
        if not races:
            print("No racecards found.")
            return

        # Take just the FIRST race to debug the full chain
        test_race = races[0]
        course_name = test_race.get("course", "Unknown Course")
        today_str = datetime.today().strftime('%Y-%m-%d')
        race_date = test_race.get("date", today_str)
        off_time = test_race.get("off_time", "00:00")
        race_name = test_race.get("race_name", "Standard Race")
        class_run = str(test_race.get("class", "Class N/A"))
        going = test_race.get("going", "Unknown")

        print(f"\n--- TESTING VENUE UPSERT FOR: {course_name} ---")
        venue_data = {"venue_name": course_name, "surface_type": going}
        venue_res = supabase.table("venues").upsert(venue_data, on_conflict="venue_name").select("id").execute()
        print("Venue Response Object:", venue_res)

        if not venue_res.data:
            print("CRITICAL: Venue insert returned no data! Check your 'venues' table columns.")
            return

        venue_id = venue_res.data[0].get("id")
        print(f"Got Venue ID: {venue_id}")

        print(f"\n--- TESTING RACE INSERT FOR: {race_name} ---")
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
        print("Race Response Object:", race_res)

        if not race_res.data:
            print("CRITICAL: Race insert returned no data! Check your 'races' table columns.")
            return

        race_id = race_res.data[0].get("id")
        print(f"Got Race ID: {race_id}")

        print("\n--- TESTING RUNNER INSERT ---")
        runners = test_race.get("runners", [])
        if runners:
            test_runner = runners[0]
            runner_payload = {
                "race_id": race_id,
                "horse_name": test_runner.get("horse") or "Unknown Horse",
                "trainer": test_runner.get("trainer") or "Unknown",
                "jockey": test_runner.get("jockey") or "Unknown",
                "form": str(test_runner.get("form", "")),
                "age": safe_int(test_runner.get("age")),
                "official_rating": safe_int(test_runner.get("ofr")),
            }
            print("Runner Payload:", runner_payload)
            runner_res = supabase.table("runners").insert(runner_payload).execute()
            print("Runner Response Object:", runner_res)
        else:
            print("No runners found in this test race.")

    except Exception as e:
        print(f"Exception during test run: {e}")

if __name__ == "__main__":
    run_pipeline()