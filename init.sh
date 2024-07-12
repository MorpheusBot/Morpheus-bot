#!/bin/bash

# Create env file
echo "Creating .env file"
printf "DEFAULT_UID=$(id -u)\nDEFAULT_GID=$(id -g)\n" > .env

# Update logs folder permissions
echo "Updating logs folder permissions"
sudo chmod -R 777 logs

# Update plugin folder permissions
echo "Updating plugin folder permissions"
sudo chown 322:322 plugins/
