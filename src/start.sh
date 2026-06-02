#!/bin/bash
gunicorn --bind 0:9012 app.main:app --reload -w ${GUNICORN_WORKERS:=1}
