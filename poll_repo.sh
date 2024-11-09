#!/bin/bash

# Command to run
COMMAND="~/ls-venv/bin/python ./discord_bot.py"

# Function to run the command
run_command() {
    echo "Running command: $COMMAND"
    $COMMAND &
    COMMAND_PID=$!
}

# Function to stop the command
stop_command() {
    echo "Stopping command: $COMMAND"
    kill $COMMAND_PID
}

# Initial run of the command
run_command

# Check for updates every 5 minutes
while true; do
    sleep 300 # 300 seconds = 5 minutes

    git fetch origin
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)

    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "New changes detected. Updating..."
        stop_command
        git pull origin main
        run_command
    else
        echo "No changes detected."
    fi
done
