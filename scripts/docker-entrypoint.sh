#!/bin/bash
set -e

# Default cron schedule if not provided
CRON_SCHEDULE=${CRON_SCHEDULE:-"0 */6 * * *"}

echo "Setting up cron job with schedule: $CRON_SCHEDULE"

# Create the cron job
echo "$CRON_SCHEDULE cd /app && python main.py >> /var/log/mealie-translator.log 2>&1" > /etc/cron.d/mealie-translator

# Give execution rights on the cron job
chmod 0644 /etc/cron.d/mealie-translator

# Apply cron job
crontab /etc/cron.d/mealie-translator

# Create the log file to be able to run tail
touch /var/log/mealie-translator.log

# Start cron in the background
cron

echo "Cron job configured. Schedule: $CRON_SCHEDULE"
echo "Log file: /var/log/mealie-translator.log"

# Run once immediately on startup
echo "Running initial translation job..."
cd /app && python main.py

# Follow the log file to keep the container running
echo "Following log file to keep container running..."
tail -f /var/log/mealie-translator.log
