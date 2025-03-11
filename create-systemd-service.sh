#!/bin/bash -e

SERVICENAME=$(basename "$(pwd)")

echo "Creating systemd service... /etc/systemd/system/${SERVICENAME}.service"
# Create systemd service file
cat >$SERVICENAME.service <<EOF
[Unit]
Description=$SERVICENAME
Requires=network.target
After=network.target

[Service]
Type=oneshot
User=$(whoami)
Group=$(id -gn)
WorkingDirectory=$(pwd)
ExecStart=/bin/bash -c "source .venv/bin/activate && python tba_awards_scraper.py"

[Install]
WantedBy=multi-user.target
EOF

sudo cp "${SERVICENAME}.service" "/etc/systemd/system/$SERVICENAME.service"

echo "Creating systemd timer... /etc/systemd/system/${SERVICENAME}.timer"
# Create systemd timer file to start the service
cat >$SERVICENAME.timer <<EOF
[Unit]
Description=$SERVICENAME
Requires=$SERVICENAME.service

[Timer]
Unit=$SERVICENAME.service
OnCalendar=*-*-1/2 00:00:00
Persistent=false

[Install]
WantedBy=timers.target
EOF

sudo cp "${SERVICENAME}.timer" "/etc/systemd/system/$SERVICENAME.timer"

echo "Enabling & starting $SERVICENAME"
# Reload unit files
sudo systemctl daemon-reload
# Autostart systemd service via the timer
sudo systemctl enable $SERVICENAME.timer
# Start systemd timer now
sudo systemctl start $SERVICENAME.timer
# Start systemd service now, but don't wait for it to complete
sudo systemctl start --no-block $SERVICENAME.service
