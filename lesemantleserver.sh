#!/bin/bash

APP_DIR=$(dirname $(readlink -f $0))
source dataset.sh

[ -d ${APP_STORAGE} ]|| mkdir -p ${APP_STORAGE}

if [[ "$1" == "dev" ]]
then
    source ./venv/bin/activate

    export FLASK_DEBUG=1
    export FLASK_APP=lesemantleserver

    flask run
else # prod
    gunicorn -b 0.0.0.0:8000 lesemantleserver:app
fi