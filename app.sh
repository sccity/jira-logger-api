#!/bin/bash

docker_compose="docker-compose -f docker-compose.yaml"

[ -f .env ] || { echo "Missing .env file. Exiting."; exit 1; }

if [[ $1 = "start" ]]; then
  echo "Starting Jira Logger API..."
	$docker_compose up -d
elif [[ $1 = "stop" ]]; then
	echo "Stopping Jira Logger API..."
	$docker_compose stop
elif [[ $1 = "restart" ]]; then
	echo "Restarting Jira Logger API..."
  $docker_compose down
  $docker_compose start
elif [[ $1 = "down" ]]; then
	echo "Tearing Down Jira Logger API..."
	$docker_compose down
elif [[ $1 = "rebuild" ]]; then
	echo "Rebuilding Jira Logger API..."
	$docker_compose down --remove-orphans
	$docker_compose build --no-cache
elif [[ $1 = "update" ]]; then
	echo "Updating Jira Logger API..."
	$docker_compose down --remove-orphans
	git pull origin prod
elif [[ $1 = "shell" ]]; then
	echo "Entering Jira Logger API Shell..."
	docker exec -it spillman-api sh
else
	echo "Unkown or missing command..."
fi