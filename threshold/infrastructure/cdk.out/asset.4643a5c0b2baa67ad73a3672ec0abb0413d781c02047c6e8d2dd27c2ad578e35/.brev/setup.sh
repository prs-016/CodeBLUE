#!/bin/bash
# Brev.dev Setup Script (NVIDIA / Cloud Compute setup)
# This script provisions the environment required to run the Databricks, Snowflake, and ML stacks on Brev.dev.

set -e

echo "Running Brev.dev Setup for THRESHOLD..."
sudo apt-get update

# Install dependencies
sudo apt-get install -y python3.10-venv docker.io build-essential htop jq

# Create env
python3.10 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install --upgrade pip
if [ -f "backend/requirements.txt" ]; then
    pip install -r backend/requirements.txt
fi

pip install marimo pyspark sagemaker boto3 mangum tabulate

# For databricks
wget https://raw.githubusercontent.com/databricks/databricks-cli/main/install.sh
sh install.sh || echo "Databricks CLI install skipped."

echo "Brev environment initialized. Run 'source .venv/bin/activate' to start."
