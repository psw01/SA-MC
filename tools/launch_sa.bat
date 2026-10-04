@echo off
rem Launches SA through MO2 + SA-host using the currently selected MO2 profile.
rem Set SACRAFT_PREFIX to your Mod Organizer folder (the one with ModOrganizer.exe).
if "%SACRAFT_PREFIX%"=="" (
    echo Set SACRAFT_PREFIX to your Mod Organizer folder first.
    exit /b 1
)
start "" ""%SACRAFT_PREFIX%\drive_c\Program Files\GTASA\gtasa.exe"" ""
