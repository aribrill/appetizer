#!/bin/bash

eval "$(conda shell.bash hook)"
conda activate app
google-chrome http://localhost:8080
python appetizer.py
