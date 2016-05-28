pushd "%~dp0"
python3 setup.py sdist
python3 setup.py bdist_wheel --universal
pause