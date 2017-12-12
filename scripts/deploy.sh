#!/bin/sh -eux

PRODUCTION_HOST=gold1.rss.chalmers.se
REMOTE_DIR=/etc/docker-compose/uservice/
REMOTE_COMPOSE_FILE=${REMOTE_DIR}docker-compose.yml
GIT_ROOT=$(git rev-parse --show-toplevel)
REMOTE_USER=ubuntu

remoteDockerCompose () {
    ssh "$REMOTE_USER"@"$PRODUCTION_HOST" -t -- docker-compose -f "$REMOTE_COMPOSE_FILE" "$*"
}

scp "${GIT_ROOT}"/scripts/docker-compose.deploy.yml "$REMOTE_USER"@"$PRODUCTION_HOST:$REMOTE_COMPOSE_FILE"
remoteDockerCompose pull
remoteDockerCompose up -d --remove-orphans
remoteDockerCompose ps
