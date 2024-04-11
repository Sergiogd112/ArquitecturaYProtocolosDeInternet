#!/usr/bin/env bash
# This is an installer script for the project
echo "Installing the project"
echo "Installing python3"
sudo apt update
sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget -y
sudo apt-get install build-essential checkinstall -y
sudo apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev \
    libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev git -y
cd /opt
sudo wget https://www.python.org/ftp/python/3.9.18/Python-3.9.18.tar.xz
sudo tar xzf Python-3.9.18.tar.xz
cd Python-3.9.18
sudo ./configure --enable-optimizations
sudo make altinstall
cd
echo "Installing poetry"

python3.8 -m pip install poetry urllib3==1.26.6
poetry completions bash >>~/.bash_completion
source ~/.bash_completion
# check if the file "01-create-containers is in the directory"

if [ -f "01-create-containers" ]; then
    echo "Codebase already cloned. Moving on to the next step."
    cd ..
else
    git clone --depth 1 https://github.com/Sergiogd112/ArquitecturaYProtocolosDeInternet.git
    echo "Codebase cloned"
    cd ArquitecturaYProtocolosDeInternet
fi
pwd
poetry update || echo "Error: Failed to update dependencies. It usually can be fixed by \"cd ArquitecturaYProtocolosDeInternet && poetry update\""
echo "Project installed"
echo "To run the project, run the command 'poetry run python3.8 main.py' from ArquitecturaYProtocolosDeInternet directory"
