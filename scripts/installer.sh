#!/usr/bin/env bash
# This is an installer script for the project
echo "Installing the project"
echo "Installing python3"
sudo apt update
sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget -y
sudo apt-get install build-essential checkinstall -y
sudo apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev \
    libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev -y
cd /opt
sudo wget https://www.python.org/ftp/python/3.8.12/Python-3.8.12.tgz
sudo tar xzf Python-3.8.12.tgz
cd Python-3.8.12
sudo ./configure --enable-optimizations
sudo make altinstall
cd
sudo apt install git
echo "Installing poetry"

python3.8 -m pip install poetry
poetry completions bash >>~/.bash_completion
source ~/.bash_completion
# check if the file "01-create-containers is in the directory"
# ask the user if they want to continue with the installation
response=$(echo "Do you want to continue with the installation? (y/n)")
if [ -f "01-create-containers" ]; then
    echo "Codebase already cloned. Moving on to the next step."
    cd ..
else
    git clone https://github.com/Sergiogd112/ArquitecturaYProtocolosDeInternet.git
    echo "Codebase cloned"
    cd ArquitecturaYProtocolosDeInternet
fi
poetry update
echo "Project installed"
echo "To run the project, run the command 'poetry run python3.8 main.py'"
