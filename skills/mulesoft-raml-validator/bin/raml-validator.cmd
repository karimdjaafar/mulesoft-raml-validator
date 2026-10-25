@echo off
rem raml-validator launcher for Windows (cmd and PowerShell).
rem Python used, in this order: %RAML_VALIDATOR_PYTHON%, the .venv folder of the
rem repository, then python (or the py launcher) from the PATH.
setlocal
set "ROOT=%~dp0.."
if defined RAML_VALIDATOR_PYTHON (
  set "PY=%RAML_VALIDATOR_PYTHON%"
) else if exist "%ROOT%\.venv\Scripts\python.exe" (
  set "PY=%ROOT%\.venv\Scripts\python.exe"
) else (
  where python >nul 2>nul && (set "PY=python") || (set "PY=py")
)
"%PY%" "%ROOT%\scripts\raml_validator.py" %*
exit /b %ERRORLEVEL%
