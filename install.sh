#!/bin/bash

git clone https://github.com/jasursadikov/mud
cd mud

chmod +x mud.sh

python3 -m venv .venv
source .venv/bin/activate
pip install prettytable

ALIAS_CMD="alias mud='$PWD/mud.sh'"

if [[ $SHELL == *"zsh"* ]]; then
    CONFIG_FILE=~/.zshrc
elif [[ $SHELL == *"bash"* ]]; then
    CONFIG_FILE=~/.bashrc
elif [[ $SHELL == *"fish"* ]]; then
    CONFIG_FILE=~/.config/fish/config.fish
    ALIAS_CMD="alias mud '$PWD/mud.sh'"
else
    echo "Unsupported shell. Falling back to .bashrc."
    CONFIG_FILE=~/.bashrc
fi

echo "$ALIAS_CMD" >> $CONFIG_FILE

echo "Alias added to $CONFIG_FILE. Please restart your terminal or run 'source $CONFIG_FILE' to apply the changes."