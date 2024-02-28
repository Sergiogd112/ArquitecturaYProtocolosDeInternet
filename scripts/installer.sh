#!/usr/bin/env bash
# This is an installer script for the project
echo "Installing the project"
echo "Installing python3"
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.5 git python3-pip -y

echo "Installing poetry"

python3 -m pip install poetry
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
echo "To run the project, run the command 'poetry run python3 main.py'"
