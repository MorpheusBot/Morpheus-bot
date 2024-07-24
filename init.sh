#!/bin/bash

DEFAULT_UID=$(id -u)
DEFAULT_GID=$(id -g)

# Create env file
echo "Creating .env file"
printf "DEFAULT_UID=$DEFAULT_UID\nDEFAULT_GID=$DEFAULT_GID\n" > .env

# Create logs folder with permissions
echo "Updating logs folder permissions"
mkdir -p logs
sudo chmod -R 777 logs
sudo chown -R $DEFAULT_UID:$DEFAULT_GID logs/

# Update plugin folder permissions
echo "Updating plugin folder permissions"
mkdir -p plugins
sudo chown -R 322:322 plugins/
