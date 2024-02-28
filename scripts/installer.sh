#!/usr/bin/env bash
# This is an installer script for the project
echo "Installing the project"
echo "Installing python3"
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.10 git -y

echo "Installing poetry"

curl -sSL https://install.python-poetry.org | python3.10 -

# check if the file "01-create-containers is in the directory"
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