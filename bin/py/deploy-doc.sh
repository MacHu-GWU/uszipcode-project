#!/bin/bash
# -*- coding: utf-8 -*-
#
# Deploy html doc to s3://<s3-bucket-name>/<dir-prefix>/<package-name>/<version>
# and s3://<s3-bucket-name>/<dir-prefix>/<package-name>/latest


dir_here="$( cd "$(dirname "$0")" ; pwd -P )"
dir_bin="$(dirname "${dir_here}")"
dir_project_root=$(dirname "${dir_bin}")

source ${dir_bin}/py/python-env.sh

print_colored_line $color_cyan "[DOING] deploy ${path_sphinx_doc_build_html} to ${s3_uri_doc_versioned} ..."
deploy_doc_to_s3 ${path_sphinx_doc_build_html} ${s3_uri_doc_versioned}

print_colored_line $color_cyan "Also deploy to ${s3_uri_doc_latest} (y/n)? "
read answer
if [ "$answer" != "${answer#[Yy]}" ] ;then
    deploy_doc_to_s3 ${path_sphinx_doc_build_html} ${s3_uri_doc_latest}
fi
