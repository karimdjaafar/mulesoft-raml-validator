@echo off
rem raml-validator (Windows): runs the command shipped with the skill,
rem skills\mulesoft-raml-validator\bin\raml-validator.cmd. Put this folder on your PATH.
call "%~dp0..\skills\mulesoft-raml-validator\bin\raml-validator.cmd" %*
exit /b %ERRORLEVEL%
