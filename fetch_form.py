import os
import requests
from dotenv import load_dotenv
from database import supabase

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
API_HOST = "the-racing-api1.p.rapidapi.com"

def fetch_and_store_historical_form(date_str: str):
    """Fetches past race results for a given date and populates historical_form in Supabase."""
    if not RAPIDAPI_KEY:
        print("Error: RAPIDAPI_KEY not found in environment variables.")
        return

    url = f"https://{API_HOST}/v1/results"
    querystring = {"date": date_str}
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": API_HOST
    }

    print(f"Fetching historical results for {date_str} from The Racing API...")
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code != 200:
            print(f"API Error: {response.status_code} - {response.text}")
            return

        data = response.json()
        races = data if isinstance(data, list) else data.get("results", [])
        
        if not races:
            print(f"No historical form records found for {date_str}.")
            return

        records_inserted = 0
        for race in races:
            course_name = race.get("course", "Unknown")
            race_date = race.get("date", date_str)
            class_run = str(race.get("class", "Class N/A"))

            for runner in race.get("runners", []):
                form_record = {
                    "horse_name": runner.get("horse_name"),
                    "race_date": race_date,
                    "course_name": course_name,
                    "finishing_position": runner.get("position"),
                    "beaten_lengths": runner.get("beaten_lengths", 0.0),
                    "class_run": class_run
                }

                supabase.table("historical_form").insert(form_record).execute()
                records_inserted += 1

        print(f"Successfully ingested {records_inserted} historical form records into Supabase.")

    except Exception as e:
        print(f"Exception during historical form ingestion: {e}")

if __name__ == "__main__":
    test_date = "2026-09-15"
    fetch_and_store_historical_form(test_date)