#!/bin/bash

cd Morpheus
git pull
docker build -t morpheus .
docker compose down
docker compose up -d
