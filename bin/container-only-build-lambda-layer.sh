#!/bin/bash
#
# NOTE: This script should be executed INSIDE of the container

dir_here="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
dir_project_root="$(dirname "${dir_here}")"
dir_build_lambda="${dir_project_root}/build/lambda"
echo "build lambda layer"

if [ -e "${dir_build_lambda}/layer.zip" ]; then
    rm "${dir_build_lambda}/layer.zip"
fi
if [ -e "${dir_build_lambda}/python" ]; then
    rm -r "${dir_build_lambda}/python"
fi

pip install -r "${dir_project_root}/requirements.txt" -t "${dir_build_lambda}/python"
cd "${dir_build_lambda}" || exit
zip "${dir_build_lambda}/layer.zip" * -r -9 -q -x python/boto3\* python/botocore\* python/s3transfer\* python/setuptools\* python/easy_install.py python/pip\* python/wheel\* python/twine\* python/_pytest\* python/pytest\*;
