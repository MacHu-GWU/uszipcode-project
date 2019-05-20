#!/bin/bash
# -*- coding: utf-8 -*-
#
# This script should be sourced to use.


# test if a command is installed in your system
# usage:
#
#   if this_command_exists "brew"; then ...
this_command_exists() {
    if [ -x "$(command -v $1)" ]; then
        return 0
    else
        return 1
    fi
}


# if a file / dir exists, then remove it. do nothing if not exists.
# usage:
#
#   rm_if_exists "~/Documents/GitHub"
rm_if_exists() {
    if [ -e $1 ]; then
        if [ -d $1 ]; then
            rm -r $1
        elif [ -f $1 ]; then
            rm $1
        fi
    fi
}


# if a dir not exists, then create it and all necessary parent dir.
mkdir_if_not_exists() {
    if ! [ -e $1 ]; then
        mkdir -p $1
    fi
}


# exit if not exists
ensure_not_exists() {
    if [ -e $1 ]; then
        echo "${1} already exists!"
        exit 1
    fi
}


color_normal="\e[39m"
color_black="\e[30m"
color_red="\e[31m"
color_green="\e[32m"
color_yellow="\e[33m"
color_blue="\e[34m"
color_magenta="\e[35m"
color_cyan="\e[36m"
color_light_gray="\e[37m"
color_dark_gray="\e[90m"
color_light_red="\e[91m"
color_light_green="\e[92m"
color_light_yellow="\e[93m"
color_light_blue="\e[94m"
color_light_magenta="\e[95m"
color_light_cyan="\e[96m"
color_white="\e[97m"


# render text in color
colored_text() {
    local tmp_color=$1
    local tmp_text=$2
    echo "${tmp_color}${tmp_text}${color_normal}"
}


# render a path into green if exists, red if not exists
colored_path() {
    local tmp_path=$1
    if [ -e ${tmp_path} ]; then
        colored_text "${color_green}" "${tmp_path}"
    else
        colored_text "${color_red}" "${tmp_path}"
    fi
}


# print a line with color
# usage:
#
#   print_colored_line $color_red "Warning!"
print_colored_line() {
    local tmp_color=$1
    local tmp_text=$2
    printf -- "$(colored_text "${tmp_color}" "${tmp_text}")\n"
}


# print title, and description, title is colored
#
# - <title>: <description>
#
# usage:
#   print_colored_line $color_red "GitHub Url" "www.github.com"
print_colored_ref_line() {
    local tmp_title_color=$1
    local tmp_title=$2
    local tmp_description=$3
    printf -- "- $(colored_text "${tmp_title_color}" "${tmp_title}"): ${tmp_description}\n"
}
