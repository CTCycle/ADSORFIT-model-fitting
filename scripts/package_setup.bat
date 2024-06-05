@echo off
rem Use this script to create a new environment called "ADSORFIT"

call conda activate ADSORFIT && cd .. && pip install -e .
if errorlevel 1 (
    echo Failed to install the package in editable mode
    goto :eof
)

