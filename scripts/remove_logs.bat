@echo off
REM Change directory to the resources/logs folder 
cd /d "%~dp0..\ADSORFIT\resources\logs"

REM Remove all .log files in the resources/logs folder
del *.log /q

