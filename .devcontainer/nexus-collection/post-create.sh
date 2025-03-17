#!/bin/bash

# Get python version
python_version=$(python --version | cut -d " " -f 2)

# set python_version variable system-wide
echo "export python_version=$python_version" >> /etc/profile

# Create and activate a Python virtual environment
echo "Creating Python virtual environment for Python $python_version"
python3 -m venv .venv-$python_version
source .venv-$python_version/bin/activate
