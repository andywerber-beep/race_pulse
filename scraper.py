from datetime import datetime
import requests
from bs4 import BeautifulSoup
from database import insert_race, insert_runner, upsert_venue


def fetch_race_cards(target_url: str, race_date: str):
    """Scrapes daily race cards from a target racing data source

    and populates the Supabase database.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    print(f"Fetching race data from {target_url} for date: {race_date}...")

    try:
        response = requests.get(target_url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Network or HTTP error occurred while scraping: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # Note: Selectors below serve as a foundational template
    # and should be adapted to the specific HTML structure of your data source.
    race_sections = soup.find_all("div", class_="race-card-container")

    if not race_sections:
        print(
            "No race cards found with current selectors. "
            "Check HTML structure or target URL."
        )
        return

    for section in race_sections:
        # Extract basic race and venue metadata
        venue_name = (
            section.find("span", class_="course-name").text.strip()
            if section.find("span", class_="course-name")
            else "Unknown Venue"
        )
        race_time_str = (
            section.find("span", class_="race-time").text.strip()
            if section.find("span", class_="race-time")
            else "12:00"
        )
        race_title = (
            section.find("h2", class_="race-title").text.strip()
            if section.find("h2", class_="race-title")
            else "Standard Race"
        )
        race_class = (
            section.find("span", class_="race-class").text.strip()
            if section.find("span", class_="race-class")
            else "Class 4"
        )
        going = (
            section.find("span", class_="going-description").text.strip()
            if section.find("span", class_="going-description")
            else "Good"
        )

        # Upsert venue to get unique ID
        venue_id = upsert_venue(venue_name=venue_name, surface_type="Turf")

        # Insert race record
        race_id = insert_race(
            venue_id=venue_id,
            race_date=race_date,
            race_time=race_time_str,
            race_title=race_title,
            race_class=race_class,
            distance_yards=1760,  # Default fallback placeholder (1 mile)
            going=going,
            field_size=0,
        )

        if not race_id:
            continue

        # Extract runners
        runner_rows = section.find_all("tr", class_="runner-row")
        for idx, runner in enumerate(runner_rows, start=1):
            horse_name = (
                runner.find("td", class_="horse-name").text.strip()
                if runner.find("td", class_="horse-name")
                else f"Horse {idx}"
            )
            trainer = (
                runner.find("td", class_="trainer-name").text.strip()
                if runner.find("td", class_="trainer-name")
                else "Unknown"
            )
            jockey = (
                runner.find("td", class_="jockey-name").text.strip()
                if runner.find("td", class_="jockey-name")
                else "Unknown"
            )

            # Safe conversion of morning odds string to float (e.g., '4/1' -> 5.0 decimal equivalent or direct float)
            odds_raw = (
                runner.find("td", class_="odds").text.strip()
                if runner.find("td", class_="odds")
                else "1.0"
            )
            try:
                if "/" in odds_raw:
                    num, den = map(float, odds_raw.split("/"))
                    morning_odds = round((num / den) + 1.0, 2)
                else:
                    morning_odds = float(odds_raw)
            except ValueError:
                morning_odds = 2.0

            insert_runner(
                race_id=race_id,
                horse_name=horse_name,
                saddle_cloth_number=idx,
                trainer=trainer,
                jockey=jockey,
                official_rating=75,  # Placeholder default rating
                weight_carried_lbs=130,  # Placeholder default weight
                days_since_last_run=30,  # Placeholder default rest period
                equipment="",
                morning_odds=morning_odds,
            )

    print("Successfully scraped and ingested daily race cards into Supabase.")


if __name__ == "__main__":
    # Test execution for today's date
    today_str = datetime.now().strftime("%Y-%m-%d")
    sample_url = "https://www.example-racing-source.com/cards"
    # fetch_race_cards(sample_url, today_str)