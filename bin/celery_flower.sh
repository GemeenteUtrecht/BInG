#!/bin/sh

celery flower -A bing --workdir src --address=127.0.0.1 --port=5555
