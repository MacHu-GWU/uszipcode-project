#!/bin/bash
# -*- coding: utf-8 -*-

dir_here="$( cd "$(dirname "$0")" ; pwd -P )"
dir_bin="$(dirname "${dir_here}")"
dir_project_root=$(dirname "${dir_bin}")

source ${dir_bin}/py/python-env.sh

print_colored_line ${color_cyan} "[DOING] print useful information:"
print_colored_ref_line ${color_light_blue} "venv" $(colored_path ${dir_venv})
print_colored_ref_line ${color_light_blue} "${package_name} installed at" $(colored_path "${dir_venv_site_packages}/${package_name}")
print_colored_ref_line ${color_light_blue} "python executable" $(colored_path ${bin_python})
print_colored_ref_line ${color_light_blue} "pip executable" $(colored_path ${bin_pip})
print_colored_ref_line ${color_light_blue} "activate venv" "source $(colored_path ${bin_activate})"
print_colored_ref_line ${color_light_blue} "deactivate venv" "deactivate"
print_colored_ref_line ${color_light_blue} "site-packages" $(colored_path ${dir_venv_site_packages})
print_colored_ref_line ${color_light_blue} "site-packages64" $(colored_path ${dir_venv_site_packages64})
print_colored_ref_line ${color_yellow} "local html doc" $(colored_path ${path_sphinx_index_html})
print_colored_ref_line ${color_yellow} "latest doc on readthedocs.org" ${rtd_url}
print_colored_ref_line ${color_yellow} "readthedocs project" ${rtd_project_url}
print_colored_ref_line ${color_yellow} "latest doc on s3.amazonaws.com" ${s3_doc_url}
print_colored_ref_line ${color_yellow} "versioned doc on s3" ${s3_uri_doc_versioned}
print_colored_ref_line ${color_yellow} "latest doc on s3" ${s3_uri_doc_latest}
print_colored_ref_line ${color_yellow} "readme file" $(colored_path ${path_readme})
