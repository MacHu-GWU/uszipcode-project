#!/bin/bash
# -*- coding: utf-8 -*-

# Variables from this script:
#
# - DETECTED_OS: Windows | Darwin | Linux
# - OS_IS_WINDOWS: Y | N
# - OS_IS_DARWIN: Y | N
# - OS_IS_LINUX: Y | N
# - OPEN_COMMAND: start in windows, open in Darwin or Linux


if [ "${OS}" = "Windows_NT" ]
then
    detected_os="Windows"
else
    detected_os=$(uname -s)
fi

if [ "${detected_os}" = "Windows" ]
then
    os_is_windows="Y"
    os_is_darwin="N"
    os_is_linux="N"
    open_command="start"
elif [ "${detected_os}" = "Darwin" ]
then
    os_is_windows="N"
    os_is_darwin="Y"
    os_is_linux="N"
    open_command="open"
elif [ "${detected_os}" = "Linux" ]
then
    os_is_windows="N"
    os_is_darwin="N"
    os_is_linux="Y"
    open_command="open"
else
    os_is_windows="N"
    os_is_darwin="N"
    os_is_linux="N"
    open_command="unknown_open_command"
fi
