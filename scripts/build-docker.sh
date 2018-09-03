#!/usr/bin/env bash

# WHAT DOES THIS?
# This file builds a docker image and tags it
# after that it uploads the image to our private docker repository

# Read version out of version file
VERSION="$(python -c 'import version; print version.__version__')"

echo Building version: $VERSION
NAME="pi-subtocall"
HUB="harbor.piplanning.io"
PROJECT="test"  # Harbor project to push to

# Fetch password for docker harbor hub as first argument
HARBORPW=$1

# Create docker image
docker build -t $NAME .
docker tag $NAME $NAME:$VERSION

# Login to our remote docker hub
echo $HARBORPW | docker login -u=rt-uploader $HUB --password-stdin

# Push image to our private hub
docker tag $NAME:$VERSION $HUB/$PROJECT/$NAME:$VERSION
docker push $HUB/$PROJECT/$NAME:$VERSION