#!/bin/bash

git clone https://github.com/jasursadikov/mud
cd mud

chmod +x ~/.local/bin/mud

python3 -m venv .venv
source .venv/bin/activate
pip install prettytable

if [[ $SHELL == *"zsh"* ]]; then
    CONFIG_FILE=~/.zshrc
    ALIAS_CMD="alias mud='$PWD/mud.py'"
elif [[ $SHELL == *"bash"* ]]; then
    CONFIG_FILE=~/.bashrc
    ALIAS_CMD="alias mud='$PWD/mud.py'"
elif [[ $SHELL == *"fish"* ]]; then
    CONFIG_FILE=~/.config/fish/config.fish
    ALIAS_CMD="alias mud '$PWD/mud.py'"
else
    echo "Unsupported shell. Defaulting to .bashrc."
    CONFIG_FILE=~/.bashrc
    ALIAS_CMD="alias mud='$PWD/mud.py'"
fi

echo "$ALIAS_CMD" >> $CONFIG_FILE

echo "Alias added to $CONFIG_FILE. Please restart your terminal or run 'source $CONFIG_FILE' to apply the changes."