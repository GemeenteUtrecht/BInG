#!/bin/sh

celery worker -A bing --workdir src -l debug
