@echo off
setlocal enabledelayedexpansion

:: Specify the settings file path
set settings_file=settings/launcher_configurations.ini

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Read settings from the configurations file
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
for /f "tokens=1,2 delims==" %%a in (%settings_file%) do (
    set key=%%a
    set value=%%b
    if not "!key:~0,1!"=="[" (                
        if "!key!"=="use_custom_environment" set use_custom_environment=!value!
        if "!key!"=="custom_env_name" set custom_env_name=!value!
    )
)

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Check if conda is installed
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
where conda >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Anaconda/Miniconda is not installed. Please install it manually first.
    pause
    goto exit
) else (
    echo Anaconda/Miniconda already installed. Checking python environment...
    goto :initial_check   
)

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Check if the 'ADSORFIT' environment exists when not using a custom environment
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:initial_check
if /i "%use_custom_environment%"=="false" (
    set "env_name=ADSORFIT"
    goto :check_environment
) else (
    echo A custom Python environment '%custom_env_name%' has been selected.
    set "env_name=%custom_env_name%"
    goto :check_environment
)

:check_environment
set "env_exists=false"
:: Loop through Conda environments to check if the specified environment exists
for /f "skip=2 tokens=1*" %%a in ('conda env list') do (
    if /i "%%a"=="%env_name%" (
        set "env_exists=true"
        goto :env_found
    )
)

:env_found
if "%env_exists%"=="true" (
    echo Python environment '%env_name%' detected.
    goto :main_menu
) else (
    if /i "%env_name%"=="ADSORFIT" (
        echo Running first-time installation for ADSORFIT. Please wait until completion and do not close the console!
        call "%~dp0\..\setup\ADSORFIT_installer.bat"
        set "custom_env_name=ADSORFIT"
        goto :main_menu
    ) else (
        echo Selected custom environment '%custom_env_name%' does not exist.
        echo Please select a valid environment or set use_custom_environment=false.
        pause
        exit
    )
)

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Show main menu
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:main_menu
echo.
echo =======================================
echo                ADSORFIT 
echo =======================================
echo 1. Run ADSORFIT
echo 2. ADSORFIT setup
echo 3. Exit and close
echo.
set /p choice="Select an option (1-3): "

if "%choice%"=="1" goto :main
if "%choice%"=="2" goto :setup_menu
if "%choice%"=="3" goto exit
echo Invalid option, try again.
pause
goto :main_menu

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Run main application
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:main
cls
call conda activate %env_name% && python .\commons\main.py
pause
goto :main_menu

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Show setup menu
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:setup_menu
cls
echo =======================================
echo            ADSORFIT setup
echo =======================================
echo 1. Install project into environment
echo 2. Remove logs
echo 3. Back to main menu
echo.
set /p sub_choice="Select an option (1-3): "

if "%sub_choice%"=="1" goto :eggs
if "%sub_choice%"=="2" goto :logs
if "%sub_choice%"=="3" goto :main_menu
echo Invalid option, try again.
pause
goto :setup_menu

:eggs
call conda activate %env_name% && cd .. && pip install -e . --use-pep517 && cd ADSORFIT
pause
goto :setup_menu

:logs
cd /d "%~dp0..\ADSORFIT\resources\logs"
del *.log /q
cd ..\..
pause
goto :setup_menu