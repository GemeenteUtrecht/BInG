#!/bin/bash

echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

JOB_NAME=push ./bin/release_docker_image.sh
