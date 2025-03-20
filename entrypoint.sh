#!/bin/bash
set -e

cd /app
mkdir -p .data

echo "Downloading embeddings vector database"
pushd .data
wget https://storage.googleapis.com/lapodocs/vectordb
popd

echo "Cloning plugin-tools repository"
pushd ..
git clone https://github.com/grafana/plugin-tools.git
popd

echo "Running lapodocs"
uv run lapo.py $@
