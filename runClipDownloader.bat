@echo off
REM Set the path to your Python executable (assuming it's in the system PATH)
SET PYTHON_CMD=python

REM Set the path to your Python script and log file (relative to the batch file location)
SET SCRIPT_PATH=getClips.py
SET LOG_FILE=logfile.log

REM Add a timestamp to the log file
ECHO %DATE% %TIME% >> "%LOG_FILE%"

REM Run the Python script and redirect output and errors to the log file
"%PYTHON_CMD%" "%SCRIPT_PATH%" >> "%LOG_FILE%" 2>&1

REM Capture the exit code of the Python script
SET EXIT_CODE=%ERRORLEVEL%

REM Check if the script ran successfully and log the result
IF %EXIT_CODE% NEQ 0 (
    echo Python script failed with exit code %EXIT_CODE%. >> "%LOG_FILE%"
) ELSE (
    echo Python script completed successfully. >> "%LOG_FILE%"
)

REM Exit with the same code as the Python script
EXIT /B %EXIT_CODE%
