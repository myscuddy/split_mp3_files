#!/bin/bash

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip and install dependencies
pip install -v --upgrade pip
pip install -v pydub ffmpeg-python 

/bin/echo "This project requires tkinter... and  on Linux you will have to run the following as it is not usually installed"
/bin/echo "sudo apt-get install python3-tk"

echo "Dependencies installed. Please ensure 'ffmpeg' is installed on your system and accessible in PATH."