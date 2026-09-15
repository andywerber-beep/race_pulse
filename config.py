import os
from dotenv import load_dotenv

# Load local environment variables if a .env file exists
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "CRITICAL ERROR: Missing Supabase credentials. "
        "Ensure SUPABASE_URL and SUPABASE_KEY are set in your environment variables or .env file."
    )