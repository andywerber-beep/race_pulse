from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client, Client

# Initialize the Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upsert_venue(venue_name: str, surface_type: str = None, track_orientation: str = None):
    """Inserts a venue or returns its existing ID."""
    response = supabase.table("venues").select("id").eq("venue_name", venue_name).execute()
    if response.data:
        return response.data[0]["id"]
    
    insert_res = supabase.table("venues").insert({
        "venue_name": venue_name,
        "surface_type": surface_type,
        "track_orientation": track_orientation
    }).execute()
    
    if insert_res.data:
        return insert_res.data[0]["id"]
    return None

def insert_race(venue_id: int, race_date: str, race_time: str, race_title: str, race_class: str, distance_yards: int, going: str, field_size: int):
    """Inserts a race record and returns its ID."""
    response = supabase.table("races").insert({
        "venue_id": venue_id,
        "race_date": race_date,
        "race_time": race_time,
        "race_title": race_title,
        "race_class": race_class,
        "distance_yards": distance_yards,
        "going": going,
        "field_size": field_size
    }).execute()
    
    if response.data:
        return response.data[0]["id"]
    return None

def insert_runner(race_id: int, horse_name: str, saddle_cloth_number: int, trainer: str, jockey: str, official_rating: int, weight_carried_lbs: int, days_since_last_run: int, equipment: str, morning_odds: float):
    """Inserts an individual runner linked to a specific race."""
    supabase.table("runners").insert({
        "race_id": race_id,
        "horse_name": horse_name,
        "saddle_cloth_number": saddle_cloth_number,
        "trainer": trainer,
        "jockey": jockey,
        "official_rating": official_rating,
        "weight_carried_lbs": weight_carried_lbs,
        "days_since_last_run": days_since_last_run,
        "equipment": equipment,
        "morning_odds": morning_odds
    }).execute()

def fetch_todays_races(race_date: str):
    """Fetches all scheduled races for a given date."""
    response = supabase.table("races").select("*, venues(venue_name)").eq("race_date", race_date).execute()
    return response.data