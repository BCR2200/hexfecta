import os
import requests
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm
import time
from typing import Dict, List
import json

# Load environment variables
load_dotenv()

class TBAClient:
    BASE_URL = "https://www.thebluealliance.com/api/v3"
    
    def __init__(self):
        self.api_key = os.getenv("TBA_API_KEY")
        if not self.api_key:
            raise ValueError("TBA_API_KEY environment variable not found. Please set it in .env file.")
        
        self.headers = {
            "X-TBA-Auth-Key": self.api_key,
            "accept": "application/json"
        }
    
    def get_all_teams(self, page: int = 0) -> List[Dict]:
        """Fetch a page of FRC teams."""
        url = f"{self.BASE_URL}/teams/{page}/simple"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_team_awards(self, team_key: str) -> List[Dict]:
        """Fetch all awards for a specific team."""
        url = f"{self.BASE_URL}/team/{team_key}/awards"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

def main():
    client = TBAClient()
    
    # Create a list to store all teams and their award counts
    team_awards = []
    page = 0
    
    print("Fetching teams...")
    while True:
        try:
            teams = client.get_all_teams(page)
            if not teams:  # No more teams
                break
                
            print(f"Processing page {page}...")
            for team in tqdm(teams):
                team_key = team["key"]
                try:
                    awards = client.get_team_awards(team_key)
                    team_awards.append({
                        "team_number": team["team_number"],
                        "team_name": team["nickname"],
                        "award_count": len(awards),
                        "awards": awards,
                    })
                    # Sleep briefly to avoid hitting rate limits
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Error fetching awards for team {team_key}: {str(e)}")
            
            page += 1
            
        except Exception as e:
            print(f"Error fetching teams page {page}: {str(e)}")
            break
    
    # Convert to DataFrame and sort by award count
    df = pd.DataFrame(team_awards)
    df = df.sort_values("award_count", ascending=False)
    
    # Save to CSV and JSON
    df.to_csv("frc_team_awards.csv", index=False)
    
    # Create a more detailed JSON output
    results = {
        "total_teams_processed": len(df),
        "total_awards": df["award_count"].sum(),
        "average_awards_per_team": df["award_count"].mean(),
        "median_awards": df["award_count"].median(),
        "teams": df.to_dict("records")
    }
    
    with open("frc_team_awards.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to frc_team_awards.csv and frc_team_awards.json")
    print(f"Processed {len(df)} teams")
    print(f"Total awards across all teams: {df['award_count'].sum()}")
    print(f"Average awards per team: {df['award_count'].mean():.2f}")
    print(f"Top 5 teams by award count:")
    print(df.head().to_string(index=False))

if __name__ == "__main__":
    main() 