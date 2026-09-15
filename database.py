import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_todays_races(race_date: str):
    """
    Fetches all races scheduled for a specific date string (YYYY-MM-DD).
    """
    try:
        # Pulls table data safely without complex query filters
        response = supabase.table("races").select("*").execute()
        races = response.data
        if not races:
            return []
            
        # Filter matching dates safely in Python
        matched_races = [r for r in races if r.get("race_date") == race_date]
        return matched_races
    except Exception as e:
        print(f"Error fetching races: {e}")
        return []


def fetch_runners_for_race(race_id):
    """
    Fetches all runners/horses participating in a specific race.
    """
    try:
        response = supabase.table("runners").select("*").eq("race_id", race_id).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching runners: {e}")
        return []


def save_venue(venue_name, location):
    """
    Saves or retrieves a venue.
    """
    try:
        response = supabase.table("venues").upsert(
            {"venue_name": venue_name, "location": location},
            on_conflict="venue_name"
        ).execute()
        return response.data
    except Exception as e:
        print(f"Error saving venue: {e}")
        return None