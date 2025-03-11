import copy
import datetime
import json
import math
import os
import time

from dotenv import load_dotenv
from jinja2 import Template
import requests
from tqdm import tqdm


# Load environment variables
load_dotenv()


# Copied from https://github.com/the-blue-alliance/the-blue-alliance/blob/3dafb6697bd9d5511afaf7240eab733bd11b26a6/consts/award_type.py
# With modifications for HEXFECTA
class AwardType(object):
    """
    An award type defines a logical type of award that an award falls into.
    These types are the same across both years and competitions within a year.
    In other words, an industrial design award from 2013casj and
    2010cmp will be of award type AwardType.INDUSTRIAL_DESIGN.

    An award type must be enumerated for every type of award ever awarded.
    ONCE A TYPE IS ENUMERATED, IT MUST NOT BE CHANGED.

    Award types don't care about what type of event (Regional, District,
    District Championship, Championship Division, Championship Finals, etc.)
    the award is from. In other words, RCA and CCA are of the same award type.
    """
    CHAIRMANS = 0
    WINNER = 1
    FINALIST = 2

    WOODIE_FLOWERS = 3
    DEANS_LIST = 4
    VOLUNTEER = 5
    FOUNDERS = 6
    BART_KAMEN_MEMORIAL = 7
    MAKE_IT_LOUD = 8

    ENGINEERING_INSPIRATION = 9
    ROOKIE_ALL_STAR = 10
    GRACIOUS_PROFESSIONALISM = 11
    COOPERTITION = 12
    JUDGES = 13
    HIGHEST_ROOKIE_SEED = 14
    ROOKIE_INSPIRATION = 15
    INDUSTRIAL_DESIGN = 16
    QUALITY = 17
    SAFETY = 18
    SPORTSMANSHIP = 19
    CREATIVITY = 20
    ENGINEERING_EXCELLENCE = 21
    ENTREPRENEURSHIP = 22
    EXCELLENCE_IN_DESIGN = 23
    EXCELLENCE_IN_DESIGN_CAD = 24
    EXCELLENCE_IN_DESIGN_ANIMATION = 25
    DRIVING_TOMORROWS_TECHNOLOGY = 26
    IMAGERY = 27
    MEDIA_AND_TECHNOLOGY = 28
    INNOVATION_IN_CONTROL = 29
    SPIRIT = 30
    WEBSITE = 31
    VISUALIZATION = 32
    AUTODESK_INVENTOR = 33
    FUTURE_INNOVATOR = 34
    RECOGNITION_OF_EXTRAORDINARY_SERVICE = 35
    OUTSTANDING_CART = 36
    WSU_AIM_HIGHER = 37
    LEADERSHIP_IN_CONTROL = 38
    NUM_1_SEED = 39
    INCREDIBLE_PLAY = 40
    PEOPLES_CHOICE_ANIMATION = 41
    VISUALIZATION_RISING_STAR = 42
    BEST_OFFENSIVE_ROUND = 43
    BEST_PLAY_OF_THE_DAY = 44
    FEATHERWEIGHT_IN_THE_FINALS = 45
    MOST_PHOTOGENIC = 46
    OUTSTANDING_DEFENSE = 47
    POWER_TO_SIMPLIFY = 48
    AGAINST_ALL_ODDS = 49
    RISING_STAR = 50
    CHAIRMANS_HONORABLE_MENTION = 51
    CONTENT_COMMUNICATION_HONORABLE_MENTION = 52
    TECHNICAL_EXECUTION_HONORABLE_MENTION = 53
    REALIZATION = 54
    REALIZATION_HONORABLE_MENTION = 55
    DESIGN_YOUR_FUTURE = 56
    DESIGN_YOUR_FUTURE_HONORABLE_MENTION = 57
    SPECIAL_RECOGNITION_CHARACTER_ANIMATION = 58
    HIGH_SCORE = 59
    TEACHER_PIONEER = 60
    BEST_CRAFTSMANSHIP = 61
    BEST_DEFENSIVE_MATCH = 62
    PLAY_OF_THE_DAY = 63
    PROGRAMMING = 64
    PROFESSIONALISM = 65
    GOLDEN_CORNDOG = 66
    MOST_IMPROVED_TEAM = 67
    WILDCARD = 68
    CHAIRMANS_FINALIST = 69
    OTHER = 70
    AUTONOMOUS = 71
    INNOVATION_CHALLENGE_SEMI_FINALIST = 72
    ROOKIE_GAME_CHANGER = 73
    SKILLS_COMPETITION_WINNER = 74
    SKILLS_COMPETITION_FINALIST = 75
    ROOKIE_DESIGN = 76
    ENGINEERING_DESIGN = 77
    DESIGNERS = 78
    CONCEPT = 79
    GAME_DESIGN_CHALLENGE_WINNER = 80
    GAME_DESIGN_CHALLENGE_FINALIST = 81

    BLUE_BANNER_AWARDS = {CHAIRMANS, CHAIRMANS_FINALIST, WINNER, WOODIE_FLOWERS, SKILLS_COMPETITION_WINNER, GAME_DESIGN_CHALLENGE_WINNER}
    INDIVIDUAL_AWARDS = {WOODIE_FLOWERS, DEANS_LIST, VOLUNTEER, FOUNDERS,
                         BART_KAMEN_MEMORIAL, MAKE_IT_LOUD}
    NON_JUDGED_NON_TEAM_AWARDS = {  # awards not used in the district point model
        HIGHEST_ROOKIE_SEED,
        WOODIE_FLOWERS,
        DEANS_LIST,
        VOLUNTEER,
        WINNER,
        FINALIST,
        WILDCARD,
    }

    SEARCHABLE = {  # Only searchable awards. Obscure & old awards not listed
        CHAIRMANS: 'Chairman\'s',
        CHAIRMANS_FINALIST: 'Chairman\'s Finalist',
        ENGINEERING_INSPIRATION: 'Engineering Inspiration',
        COOPERTITION: 'Coopertition',
        CREATIVITY: 'Creativity',
        ENGINEERING_EXCELLENCE: 'Engineering Excellence',
        ENTREPRENEURSHIP: 'Entrepreneurship',
        DEANS_LIST: 'Dean\'s List',
        BART_KAMEN_MEMORIAL: 'Bart Kamen Memorial',
        GRACIOUS_PROFESSIONALISM: 'Gracious Professionalism',
        HIGHEST_ROOKIE_SEED: 'Highest Rookie Seed',
        IMAGERY: 'Imagery',
        INDUSTRIAL_DESIGN: 'Industrial Design',
        SAFETY: 'Safety',
        INNOVATION_IN_CONTROL: 'Innovation in Control',
        QUALITY: 'Quality',
        ROOKIE_ALL_STAR: 'Rookie All Star',
        ROOKIE_INSPIRATION: 'Rookie Inspiration',
        SPIRIT: 'Spirit',
        VOLUNTEER: 'Volunteer',
        WOODIE_FLOWERS: 'Woodie Flowers',
        JUDGES: 'Judges\'',
    }

    HEXFECTA = {
        ENGINEERING_EXCELLENCE: SEARCHABLE[ENGINEERING_EXCELLENCE],
        QUALITY: SEARCHABLE[QUALITY],
        INDUSTRIAL_DESIGN: SEARCHABLE[INDUSTRIAL_DESIGN],
        CREATIVITY: SEARCHABLE[CREATIVITY],
        AUTONOMOUS: 'Autonomous',  # Missing, add our own name
        INNOVATION_IN_CONTROL: SEARCHABLE[INNOVATION_IN_CONTROL],
    }


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
        result_time = datetime.datetime.fromisoformat(cache_result[self._GOT_AT_KEY])
        now = datetime.datetime.now(datetime.timezone.utc)
        return now - result_time < datetime.timedelta(hours=24)

    def now_timestamp(self):
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def request_with_cache_and_headers(self, url, cache, cache_key):
        etag = None
        cache_key = str(cache_key)
        if cache_key in cache:
            cached = cache[cache_key]
            if self.is_fresh_cache_result(cached):
                return cached['response'], cached[self._GOT_AT_KEY]
            cached_headers = cached["headers"]
            if self._ETAG_HEADER_KEY in cached_headers:
                etag = cached_headers[self._ETAG_HEADER_KEY]
        try:
            args = copy.deepcopy(self.headers)
            if etag is not None:
                args['If-None-Match'] = etag

            response = requests.get(url, headers=args, timeout=5)
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
            return cache[cache_key]['response'], cache[cache_key][self._GOT_AT_KEY]
        except Exception as e:
            print(f"Exception when calling url ({url}): {e}\n")
            return None, None

    def get_all_teams(self, page: int = 0):
        """Fetch a page of FRC teams."""
        url = f"{self.BASE_URL}/teams/{page}"
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

def team_summaries(team, awards):
    """
    Genearate the summaries object for a team.
    :param team: Dict, looks like this:
    {
        'key': 'frc254',
        'team_number': 254,
        'nickname': 'The Cheesy Poofs',
        'rookie_year': 1999,
    }
    :param awards: List, looks like this:
    [
        {
            'name': 'Rookie All Star Award',
            'award_type': 10,
            'event_key': '2025cave',
            'year': 2025,
        },
        ...
    ]
    :return: Dict, looks like this:
    {
        'awards_received': 100,
        'awards_by_category': {
            'Sprit': 94,
            'Engineering Excellence': 1,
            'Quality': 1,
            'Industrial Design': 1,
            'Creativity': 1,
            'Autonomous': 1,
            'Innovation in Control': 1,
        },
        'hexfecta_category_awards': 6,
        'awards_by_hexfecta_category': {
            'Engineering Excellence': 1,
            'Quality': 1,
            'Industrial Design': 1,
            'Creativity': 1,
            'Autonomous': 1,
            'Innovation in Control': 1,
        },
        'awards_per_year': 1.0,
        'hexfecta_category_awards_per_year': 1.0,
        'awards_per_year_by_hexfecta_category': {
            'Engineering Excellence': 1.0,
            'Quality': 1.0,
            'Industrial Design': 1.0,
            'Creativity': 1.0,
            'Autonomous': 1.0,
            'Innovation in Control': 1.0,
        },
        'hexfectas': 1,
        'hexfectas_per_year': 1.0,
    }
    """
    # Calculate awards received. Count of all awards team has received.

    # Calculate the number of awards in hexfecta categories.

    # Calculate the count of awards in hexfecta categories, grouped by category.

    # Calculate the number of awards per year. If current year is 2025 and
    # rookie year is 2025, team has participated in 1 year.

    # Calculate the number of awards in hexfecta categories per year.
    # If current year is 2025 and rookie year is 2025, team has participated
    # in 1 year.

    # Calculate the number of awards in hexfecta categories per year, grouped
    # by category.
    # If current year is 2025 and rookie year is 2025, team has participated
    # in 1 year.

    # Calculate the number of hexfectas. Defined as the lowest number of awards
    # in any hexfecta category.

    # Calculate hexfectas per year.
    # If current year is 2025 and rookie year is 2025, team has participated
    # in 1 year.

    current_year = datetime.datetime.now().year
    if team['rookie_year'] is None:
        team['rookie_year'] = current_year - 1  # Some teams seem to have bad data here
        print(f'Team has no rookie_year! {team["key"]}')
    team_years = max(current_year - team['rookie_year'] + 1, 1)

    awards_received = len(awards)

    awards_by_category = {}
    for award in awards:
        category_name = award['name']
        awards_by_category[category_name] = awards_by_category.get(category_name, 0) + 1

    hexfecta_awards = [award for award in awards if award['award_type'] in AwardType.HEXFECTA]
    hexfecta_awards_count = len(hexfecta_awards)

    awards_by_hexfecta_category = {name: 0 for _, name in AwardType.HEXFECTA.items()}
    for award in hexfecta_awards:
        category_name = AwardType.HEXFECTA[award['award_type']]
        awards_by_hexfecta_category[category_name] = awards_by_hexfecta_category.get(category_name, 0) + 1

    awards_per_year = awards_received / team_years
    hexfecta_awards_per_year = hexfecta_awards_count / team_years

    awards_per_year_by_hexfecta_category = {
        category: count / team_years for category, count in awards_by_hexfecta_category.items()
    }

    hexfectas = math.inf
    for count in awards_by_hexfecta_category.values():
        hexfectas = min(hexfectas, count)

    hexfectas = 0 if math.isinf(hexfectas) else hexfectas
    hexfectas_per_year = hexfectas / team_years

    return {
        'awards_received': awards_received,
        'awards_by_category': awards_by_category,
        'hexfecta_category_awards': hexfecta_awards_count,
        'awards_by_hexfecta_category': awards_by_hexfecta_category,
        'awards_per_year': awards_per_year,
        'hexfecta_category_awards_per_year': hexfecta_awards_per_year,
        'awards_per_year_by_hexfecta_category': awards_per_year_by_hexfecta_category,
        'hexfectas': hexfectas,
        'hexfectas_per_year': hexfectas_per_year,
    }


def overall_summaries(teams):
    """
    Generate the summaries object.
    :param teams: Dict, where each key represents a team's data:
    {
        '254': {
            'team_number': 254,
            'team_name': 'The Cheesy Poofs',
            'rookie_year': 1999,
            'summaries': {
                'hexfectas': 3,
                # Other summary metrics...
            }
        }
    }
    :return: Dict, containing the top 10 teams by Hexfectas:
    {
        'top_n_hexfectas': [
            {
                'team_number': 254,
                'team_name': 'The Cheesy Poofs',
                'rookie_year': 1999,
                'hexfectas': 3,
            },
            ...
        ]
    }
    """
    # Extract and sort teams by Hexfectas in descending order
    teams_with_hexfectas = [
        {
            'team_number': team_data['team_number'],
            'team_name': team_data['team_name'],
            'rookie_year': team_data['rookie_year'],
            'hexfectas': team_data['summaries']['hexfectas'],
        }
        for team_data in teams.values()
        if team_data['summaries']['hexfectas'] > 0
    ]
    sorted_teams = sorted(teams_with_hexfectas, key=lambda t: t['hexfectas'], reverse=True)

    # Find team 2200 and ensure it is included in the top N list
    ind_2200 = next((i for i, team in enumerate(sorted_teams) if team['team_number'] == 2200), len(sorted_teams))
    top_n_hexfectas = sorted_teams[:ind_2200 + 1]

    return {
        'top_n_hexfectas': top_n_hexfectas,
        'all_by_hexfectas': sorted_teams,
    }


def scrape_and_summarize():
    client = TBAClient()
    try:
        client.load_from_file()

        # Create a list to store all teams and their award counts
        team_awards = {}
        page = 0

        print("Fetching teams...")
        while True:
            teams, team_got_at = client.get_all_teams(page)
            if not teams:  # No more teams
                break

            print(f"Processing page {page}, teams {page*500}-{page*500+99}...")
            for team in tqdm(teams):
                team_key = team['key']

                awards, awards_got_at = client.get_team_awards(team_key)

                if awards is not None:
                    award_details = []
                    for award in awards:
                        award_details.append({
                            'name': award['name'],
                            'award_type': award['award_type'],
                            'year': award['year'],
                            'event_key': award['event_key'],
                        })

                    team_awards[team['team_number']] = {
                        "team_number": team['team_number'],
                        "team_name": team['nickname'],
                        'rookie_year': team['rookie_year'],
                        'last_updated': awards_got_at,
                        "awards": award_details,
                        'summaries': team_summaries(team, award_details),
                    }
                else:
                    print(f'Warning: Award search for team {team_key} returned None.')

            page += 1

        if not team_awards:
            print("No team data was collected. Please check your API key and internet connection.")
            return

        results = {
            'teams': team_awards,
            'summaries': overall_summaries(team_awards),
            'last_updated': team_got_at,
        }

        with open("frc_team_awards.json", "w") as f:
            json.dump(results, f, indent=2)

        print("\nResults saved to frc_team_awards.csv and frc_team_awards.json")
        print(f"Processed {len(team_awards.keys())} teams")
    finally:
        client.write_to_file()


def generate_html():
    print(f'Rendering HTML pages')
    with open("frc_team_awards.json", "r") as f:
        data = json.load(f)

    # Define common components
    style_template = '''
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f4f4f9;
                color: #333;
                line-height: 1.6;
            }
            h1, h2, h3 {
                color: #004085;
            }
            h1 {
                text-align: center;
                padding: 20px 0;
                background-color: #007bff;
                color: #fff;
                margin: 0;
            }
            h2 {
                margin-top: 20px;
            }
            h3 {
                margin: 15px 0 10px;
            }
            p {
                margin: 10px 0;
            }
            ul {
                list-style-type: square;
                margin: 10px 20px;
                padding: 0;
            }
            li {
                margin: 5px 0;
            }
            div {
                padding: 20px;
                margin: 20px auto;
                max-width: 800px;
                background: #fff;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }
            a {
                color: #007bff;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
    '''
    header_nav = '''
    <header>
        <h1>FRC Hexfecta Awards</h1>
        <nav style="text-align: center; background-color: #0056b3; padding: 10px 0;">
            <a href="index.html" style="color: white; margin: 0 10px;">All Teams</a>
            <a href="top.html" style="color: white; margin: 0 10px;">Top Teams</a>
            <a href="all_hexfecta.html" style="color: white; margin: 0 10px;">All Hexfecta Teams</a>
        </nav>
    </header>
    '''

    # Define the HTML template
    html_template = Template('''
    <html>
    <head>
        <title>FRC Team {{ team_data.team_number }} Awards</title>
        <style>
    ''' + style_template + '''
        </style>
    </head>
    <body>
        ''' + header_nav + '''
        <div>
            <h2>Team {{ team_data.team_number }} - {{ team_data.team_name }}</h2>
            <p><strong>Rookie year:</strong> {{ team_data.rookie_year }}</p>
            <h3>Hexfectas</h3>
            <p><strong>Hexfectas:</strong> {{ team_data.summaries.hexfectas }}</p>
            <p><strong>Hexfectas Per Year:</strong> {{ team_data.summaries.hexfectas_per_year }}</p>
            <p><strong>Awards Received:</strong> {{ team_data.summaries.awards_received }}</p>
            <h3>Hexfecta Category Awards</h3>
            <p><strong>Awards Received:</strong> {{ team_data.summaries.hexfecta_category_awards }}</p>
            <h3>Awards by Hexfecta category</h3>
            <ul>
            {% for category, count in team_data.summaries.awards_by_hexfecta_category.items() %}
                <li><strong>{{ category }}</strong>: {{ count }}</li>
            {% endfor %}
            </ul>
            <h3>Awards by Category</h3>
            <ul>
            {% for category, count in team_data.summaries.awards_by_category.items() %}
                <li><strong>{{ category }}</strong>: {{ count }}</li>
            {% endfor %}
            </ul>
            <h3>Awards Per Year</h3>
            <p><strong>Awards Per Year:</strong> {{ team_data.summaries.awards_per_year }}</p>
            <h3>Hexfecta Category Awards Per Year</h3>
            <p><strong>Hexfecta Category Awards Per Year:</strong> {{ team_data.summaries.hexfecta_category_awards_per_year }}</p>
            <ul>
            {% for category, per_year in team_data.summaries.awards_per_year_by_hexfecta_category.items() %}
                <li><strong>{{ category }}</strong>: {{ per_year }}</li>
            {% endfor %}
            </ul>
            <h3>All Awards</h3>
            <ul>
            {% for award in team_data.awards %}
                <li><strong>{{ award.year }}</strong>: {{ award.name }} -- {{ award.event_key }}</li>
            {% endfor %}
            </ul>
        </div>
        <p style="text-align: center; font-style: italic;">Last updated: {{ team_data.last_updated }}</p>
    </body>
    </html>
    ''')

    for team_number, team_data in tqdm(data['teams'].items()):
        # Render the template with the data
        html_content = html_template.render(team_data=team_data)

        # Create HTML output directory if it doesn't exist
        os.makedirs("html_output", exist_ok=True)

        # Save the HTML content to a file
        with open(f"html_output/{team_number}.html", "w") as html_file:
            html_file.write(html_content)

    # Create an all hexfecta page to list all teams that have at least 1 hexfecta
    all_hexfecta_template = Template('''
    <html>
    <head>
        <title>FRC All Hexfecta Awards</title>
        <style>
    ''' + style_template + '''
        </style>
    </head>
    <body>
        ''' + header_nav + '''
        <div>
            <h3>Top {{ data.summaries.all_by_hexfectas|length }} by Hexfectas</h3>
            <ul>
            {% for team_data in data.summaries.all_by_hexfectas %}
                <li><a href="{{ team_data.team_number }}.html">{{ team_data.hexfectas }} - Team {{ team_data.team_number }} - {{ team_data.team_name }} (Rookie year: {{ team_data.rookie_year }})</a></li>
            {% endfor %}
            </ul>
        </div>
        <p style="text-align: center; font-style: italic;">Last updated: {{ data.last_updated }}</p>
    </body>
    </html>
    ''')
    html_content = all_hexfecta_template.render(data=data)
    with open("html_output/all_hexfecta.html", "w") as f:
        f.write(html_content)

    # Create a top page to list top teams
    top_template = Template('''
    <html>
    <head>
        <title>FRC Top Hexfecta Awards</title>
        <style>
    ''' + style_template + '''
        </style>
    </head>
    <body>
        ''' + header_nav + '''
        <div>
            <h3>Top {{ data.summaries.top_n_hexfectas|length }} by Hexfectas</h3>
            <ul>
            {% for team_data in data.summaries.top_n_hexfectas %}
                <li><a href="{{ team_data.team_number }}.html">{{ team_data.hexfectas }} - Team {{ team_data.team_number }} - {{ team_data.team_name }} (Rookie year: {{ team_data.rookie_year }})</a></li>
            {% endfor %}
            </ul>
        </div>
        <p style="text-align: center; font-style: italic;">Last updated: {{ data.last_updated }}</p>
    </body>
    </html>
    ''')
    html_content = top_template.render(data=data)
    with open("html_output/top.html", "w") as f:
        f.write(html_content)

    # Create an index HTML page to list all teams
    index_template = Template('''
    <html>
    <head>
        <title>FRC Hexfecta Awards Index</title>
        <style>
    ''' + style_template + '''
        </style>
    </head>
    <body>
        ''' + header_nav + '''
        <div>
            <h3>All Teams</h3>
            <ul>
            {% for team_number, team_data in data.teams.items() %}
                <li><a href="{{ team_data.team_number }}.html">{{ team_data.summaries.hexfectas }} - Team {{ team_data.team_number }} - {{ team_data.team_name }} (Rookie year: {{ team_data.rookie_year }})</a></li>
            {% endfor %}
            </ul>
        </div>
        <p style="text-align: center; font-style: italic;">Last updated: {{ data.last_updated }}</p>
    </body>
    </html>
    ''')
    html_content = index_template.render(data=data)
    with open("html_output/index.html", "w") as index_file:
        index_file.write(html_content)


def main():
    scrape_and_summarize()
    generate_html()

if __name__ == "__main__":
    main() 