#!/bin/sh
# Run the DB init script first
python db_init.py

# Then start the flask server
flask run --host=0.0.0.0 --port=8000
