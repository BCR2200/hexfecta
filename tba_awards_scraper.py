import copy
import datetime
import os
import requests
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm
import time
import json

# Load environment variables
load_dotenv()

class TBAClient:
    BASE_URL = "https://www.thebluealliance.com/api/v3"
    _ETAG_HEADER_KEY = 'ETag'
    _GOT_AT_KEY = 'got_at'

    def __init__(self):
        self.api_key = os.getenv("TBA_API_KEY")
        if not self.api_key:
            raise ValueError("TBA_API_KEY environment variable not found. Please set it in .env file.")

        self.headers = {
            "X-TBA-Auth-Key": self.api_key,
            "accept": "application/json"
        }

        self.teams_simple_page_cache = {}
        self.team_awards_cache = {}

    def is_fresh_cache_result(self, cache_result):
        """Returns True if the cache result is from within 24 hours of now."""
        # This could be static, but it is only relevant for this class, so make it seem like
        # we use self.
        _ = self
        if cache_result is None:
            return False
        result_time = datetime.datetime.fromisoformat(cache_result['got_at'])
        now = datetime.datetime.now(datetime.UTC)
        return now - result_time < datetime.timedelta(hours=24)

    def now_timestamp(self):
        return datetime.datetime.now(datetime.UTC).isoformat()

    def request_with_cache_and_headers(self, url, cache, cache_key):
        etag = None
        cache_key = str(cache_key)
        if cache_key in cache:
            cached = cache[cache_key]
            if self.is_fresh_cache_result(cached):
                return cached['response']
            cached_headers = cached["headers"]
            if self._ETAG_HEADER_KEY in cached_headers:
                etag = cached_headers[self._ETAG_HEADER_KEY]
        try:
            args = copy.deepcopy(self.headers)
            if etag is not None:
                args['If-None-Match'] = etag

            response = requests.get(url, headers=args)
            response.raise_for_status()
            headers = dict(response.headers)
            etag = None
            if self._ETAG_HEADER_KEY in headers:
                etag = headers[self._ETAG_HEADER_KEY]
            elif 'Etag' in headers:
                etag = headers['Etag']  # TBA API WTF
            if response.status_code == 200:
                cache[cache_key] = {
                    'response': response.json(),
                    'headers': {
                        self._ETAG_HEADER_KEY: etag,
                    },
                    self._GOT_AT_KEY: self.now_timestamp(),
                }
                # Sleep briefly to avoid hitting rate limits
                time.sleep(0.1)
            elif response.status_code == 304:
                cached = cache[cache_key]
                cached.update({self._GOT_AT_KEY: self.now_timestamp()})
                cache[cache_key] = cached
            return cache[cache_key]['response']
        except Exception as e:
            print(f"Exception when calling url ({url}): {e}\n")
            return None

    def get_all_teams(self, page: int = 0):
        """Fetch a page of FRC teams."""
        url = f"{self.BASE_URL}/teams/{page}/simple"
        return self.request_with_cache_and_headers(url, self.teams_simple_page_cache, page)

    def get_team_awards(self, team_key: str):
        """Fetch all awards for a specific team."""
        url = f"{self.BASE_URL}/team/{team_key}/awards"
        return self.request_with_cache_and_headers(url, self.team_awards_cache, team_key)

    def write_to_file(self):
        with open("tba_api_cache.json", "w") as f:
            json.dump({
                'all_teams': self.teams_simple_page_cache,
                'team_awards': self.team_awards_cache,
            }, f, indent=2)

    def load_from_file(self):
        try:
            with open("tba_api_cache.json", "r") as f:
                data = json.load(f)
                self.teams_simple_page_cache = data['all_teams']
                self.team_awards_cache = data['team_awards']
                print(f"Loaded {len(self.teams_simple_page_cache)} teams and {len(self.team_awards_cache)} awards from file.")
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            # delete the corrupted file
            os.remove("tba_api_cache.json")
            print("Corrupted cache file deleted.")

def main():
    client = TBAClient()
    try:
        client.load_from_file()

        # Create a list to store all teams and their award counts
        team_awards = []
        page = 0

        print("Fetching teams...")
        while True:
            teams = client.get_all_teams(page)
            if not teams:  # No more teams
                break

            print(f"Processing page {page}...")
            for team in tqdm(teams):
                team_key = team['key']

                awards = client.get_team_awards(team_key)

                if awards is not None:
                    award_details = []
                    for award in awards:
                        award_details.append({
                            'name': award['name'],
                            'award_type': award['award_type'],
                            'year': award['year'],
                            'event_key': award['event_key'],
                        })

                    team_awards.append({
                        "team_number": team['team_number'],
                        "team_name": team['nickname'],
                        "award_count": len(awards),
                        "awards": award_details,
                    })

            page += 1

        if not team_awards:
            print("No team data was collected. Please check your API key and internet connection.")
            return

        # Convert to DataFrame and sort by award count
        df = pd.DataFrame(team_awards)
        df = df.sort_values("award_count", ascending=False)

        # Save to CSV and JSON
        df.to_csv("frc_team_awards.csv", index=False)

        # Create a more detailed JSON output
        results = {
            "total_teams_processed": len(df),
            "total_awards": int(df["award_count"].sum()),
            "average_awards_per_team": float(df["award_count"].mean()),
            "median_awards": float(df["award_count"].median()),
            "teams": df.to_dict("records")
        }

        with open("frc_team_awards.json", "w") as f:
            json.dump(results, f, indent=2)

        print("\nResults saved to frc_team_awards.csv and frc_team_awards.json")
        print(f"Processed {len(df)} teams")
        print(f"Total awards across all teams: {df['award_count'].sum()}")
        print(f"Average awards per team: {df['award_count'].mean():.2f}")
        print(f"Top 5 teams by award count:")
        try:
            print(df.head().to_string(index=False))
        except Exception as e:
            print(f'exception: {e}')
    finally:
        client.write_to_file()

if __name__ == "__main__":
    main() 