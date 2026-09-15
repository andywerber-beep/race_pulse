from datetime import datetime, timedelta
from database import fetch_todays_races, supabase


def calculate_implied_probability(odds: float) -> float:
    """Calculates the implied probability of a horse winning based on decimal odds."""
    if odds <= 1.0:
        return 1.0
    return round(1.0 / odds, 4)


def evaluate_value_bets(race_date: str):
    """Evaluates runners for a given date to find positive Expected Value (EV) betting opportunities."""
    print(f"Running value-bet model for date: {race_date}...")

    races = fetch_todays_races(race_date)
    if not races:
        print(f"No races found in the database for date: {race_date}.")
        return []

    value_bets = []

    for race in races:
        race_id = race["id"]
        # Fallback handling for venue name depending on database response structure
        venue_name = race.get("venue_name") or race.get("venues", {}).get("venue_name", "Unknown Venue")
        race_time = race["race_time"]

        # Fetch all runners for this race
        runners_res = (
            supabase.table("runners")
            .select("*")
            .eq("race_id", race_id)
            .execute()
        )
        runners = runners_res.data

        if not runners:
            continue

        for runner in runners:
            horse_name = runner["horse_name"]
            morning_odds = runner["morning_odds"]
            official_rating = runner["official_rating"] or 70

            # Market implied probability from bookmaker/exchange odds
            implied_prob = calculate_implied_probability(morning_odds)

            # Foundational Heuristic Model Probability:
            # Adjusts theoretical probability using official rating relative to a baseline field rating of 80.
            rating_factor = official_rating / 80.0
            model_prob = round(min(max(implied_prob * rating_factor * 0.95, 0.01), 0.99), 4)

            # Expected Value (EV) calculation for a single bet: (Model Probability * Decimal Odds) - 1
            expected_value = round((model_prob * morning_odds) - 1.0, 4)

            # Flag as a value bet if expected value is positive (> 5% value threshold margin)
            if expected_value > 0.05:
                value_bets.append({
                    "venue": venue_name,
                    "time": race_time,
                    "horse": horse_name,
                    "odds": morning_odds,
                    "model_probability": model_prob,
                    "implied_probability": implied_prob,
                    "expected_value": expected_value,
                })

    print(f"Analysis complete. Found {len(value_bets)} potential value singles.")
    return value_bets


if __name__ == "__main__":
    # Automatically target tomorrow's date since today's racing has concluded
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    opportunities = evaluate_value_bets(tomorrow_str)
    for bet in opportunities:
        print(
            f"[{bet['time']}] {bet['venue']} - {bet['horse']} "
            f"(Odds: {bet['odds']} | EV: +{bet['expected_value'] * 100:.1f}%)"
        )