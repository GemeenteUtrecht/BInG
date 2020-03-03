#!/bin/bash
#
# Resets the migrations. Run from the root of the project.

src/manage.py migrate config zero

# fake migrations forwards
src/manage.py migrate
