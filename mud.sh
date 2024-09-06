#!/bin/bash

current_dir=$(dirname "$(realpath "$0")")
venv_path="$current_dir/.venv/bin/python"

# Activate virtual environment if not already active
if [[ "$(which python)" != "$venv_path" ]]; then
    exec "$venv_path" "$current_dir/main.py" "$@"
else
    exec "$current_dir/main.py" "$@"
fi