@echo off
rem Use this script to create a new environment called "ADSORFIT"

echo STEP 1: Creation of ADSORFIT environment
call conda create -n ADSORFIT python=3.11 -y
if errorlevel 1 (
    echo Failed to create the environment ADSORFIT
    goto :eof
)

rem If present, activate the environment
call conda activate ADSORFIT

rem Install additional packages with pip
echo STEP 2: Install python libraries and packages
call pip install tqdm numpy pandas scipy
if errorlevel 1 (
    echo Failed to install Python libraries.
    goto :eof
)

rem install packages in editable mode
echo STEP 3: Install utils packages in editable mode
call cd .. && pip install -e .
if errorlevel 1 (
    echo Failed to install the package in editable mode
    goto :eof
)

rem Print the list of dependencies installed in the environment
echo List of installed dependencies
call conda list

set/p<nul =Press any key to exit... & pause>nul
