#!/bin/bash

# Update package list and install prerequisites
sudo apt-get update

# Install Python 3 and pip if not already installed
sudo apt-get install -y python3 python3-pip python3-venv

# Verify Python installation
python3 --version
pip3 --version

# Create a virtual environment
python3 -m venv emg_env

# Activate the virtual environment
source emg_env/bin/activate

# Install dependencies from requirements.txt
pip install --upgrade pip
pip install -r requirements.txt

# Confirm the installation
pip list

echo "Virtual environment setup complete. All dependencies are installed."

