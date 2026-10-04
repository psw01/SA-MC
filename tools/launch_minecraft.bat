@echo off
rem Starts the SACraft Minecraft client (dev launcher, offline name "Dovahkiin").
rem It waits on the title screen until SA (with the SACraft SA-host plugin) is running,
rem then hides its window and loads the mirror world by itself.
cd /d "%~dp0..\fabric"
call gradlew.bat runClient --no-configuration-cache
