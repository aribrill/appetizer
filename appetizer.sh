#!/bin/bash

eval "$(conda shell.bash hook)"
conda activate app
if command -v open &> /dev/null
then
    open http://localhost:8080
else
    xdg-open http://localhost:8080
fi
python appetizer.py
