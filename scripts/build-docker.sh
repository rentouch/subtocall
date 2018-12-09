#!/usr/bin/env bash

# WHAT DOES THIS?
# This file builds a docker image and tags it
# after that it uploads the image to our private docker repository
NAME="pi-subtocall"
HUB="harbor.piplanning.io"
prod_flag=false
username='rt-uploader'
password=''

print_usage() {
  printf "Usage: build-docker.sh\n"
  printf " -s  Push to stable/production project (by default it pushes to test)\n"
  printf " -u  Username for docker repo (default is rt-uploader) \n"
  printf " -p  Password to docker repository \n"
}

while getopts 'su:p:' flag; do
  case "${flag}" in
    s) prod_flag=true ;;
    u) username="${OPTARG}" ;;
    p) password="${OPTARG}" ;;
    *) print_usage
       exit 1 ;;
  esac
done

# Password check
if [ -z "$password" ]
then
      echo "[ERROR]: Please pass a password!"
      print_usage
      exit
fi

# Set project on harbor repo
PROJECT="test"
if [ "$prod_flag" = true ] ; then
    PROJECT="k8sprod"
fi


DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
VERSION="$(cd $DIR/../ && python -c 'import version; print version.__version__')"
echo Building version: $VERSION

# Create docker image
docker build -t $NAME .
docker tag $NAME $NAME:$VERSION

# Login to our remote docker hub
echo $password | docker login -u=rt-uploader $HUB --password-stdin

# Push image to our private hub
docker tag $NAME:$VERSION $HUB/$PROJECT/$NAME:$VERSION
docker push $HUB/$PROJECT/$NAME:$VERSION
