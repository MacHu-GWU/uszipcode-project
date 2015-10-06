pushd "%~dp0"
python3 setup.py sdist
python3 setup.py build --plat-name=win32 bdist_wininst
python3 setup.py build --plat-name=win-amd64 bdist_wininst
pause