# FRC Team Awards Scraper

This tool is designed to fetch and process data from The Blue Alliance (TBA) API. It retrieves teams' information alongside their awards and generates a CSV file and a JSON file with detailed summaries.

## Prerequisites

1. **Python**: The script requires Python 3 is installed on your machine.

## Setup Instructions

Follow these steps to prepare and run the script:

1. Clone the repository if you haven't already:
    ```bash
    git clone <your-repository-url>
    cd <your-repository-directory>
    ```

2. Run the setup script to create and activate the virtual environment and install dependencies:
    ```bash
    source setup.bash
    ```

3. Ensure the `.env` file with the `TBA_API_KEY` is in the same directory as the script.
You can use `template.env` as a template. Rename it to `.env`:
    ```bash
    TBA_API_KEY=<Your_TBA_API_Key>
    ```

## Running the Script

To execute the script and fetch the award information:

1. Run the Python script:
    ```bash
    python tba_awards_scraper.py
    ```

2. After execution, the results will be saved as:
	- `frc_team_awards.json`: A JSON file containing teams and their awards, including detailed award information such as award names, types, years, and event keys.
	- `tba_api_cache.json`: A cache file to store API responses and reduce unnecessary API calls.

## Output

Upon successful execution, the script will:
- Fetch all the teams and their awards from The Blue Alliance API
- Save the detailed results in JSON format
- Display progress information during execution
- Cache API responses to improve performance and respect rate limits

## Notes

- Ensure your API key (`TBA_API_KEY`) is valid and you're authorized to access The Blue Alliance API.
- The script incorporates a delay (`time.sleep()`) to manage rate limits effectively.