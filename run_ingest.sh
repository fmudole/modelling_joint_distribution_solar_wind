#!/bin/bash

echo "Starting Energy Ingestion..."

cd /c/dev/modelling_joint_distribution_solar_wind || exit 1

# Activate virtual environment
source .venv_313/Scripts/activate

# Run ingestion script
python data_ingestion/ingest_openelectricity.py >> ingest_log.txt 2>&1

echo "Finished."

