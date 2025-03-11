# Setting Up Systemd Service for FRC Team Awards Scraper

This guide explains how to set up a systemd service and timer to automatically run the FRC Team Awards Scraper every two days.

## Installation Steps

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
   
4. Install the service and timer files, then start them:

```bash
./create-systemd-service.sh
```

## Verification

To verify that the timer is set up correctly:

```bash
# Check the status of the timer
sudo systemctl status hexfecta.timer

# List all timers
systemctl list-timers
```

## Manual Execution

If you want to run the service manually without waiting for the timer:

```bash
sudo systemctl start hexfecta.service
```

## Viewing Logs

To view the logs from the service:

```bash
journalctl -u hexfecta.service
```

## Customization

If you need to modify the schedule or other settings:

1. Edit the service or timer files
2. Reload the systemd daemon
3. Restart the timer

```bash
sudo systemctl daemon-reload
sudo systemctl restart hexfecta.timer
```

## Stop service steps

```bash
sudo systemctl disable hexfecta.timer
sudo systemctl disable hexfecta.service
sudo systemctl stop hexfecta.timer
sudo systemctl stop hexfecta.service
```

## Troubleshooting

If the service fails to run:

1. Check the logs: `journalctl -u hexfecta-scraper.service`
2. Verify that the paths in the service file are correct
3. Ensure the user specified in the service file has permission to run the script
4. Check that the .env file with the TBA_API_KEY is properly set up in the working directory 