#!/bin/bash

ESC_SEQ="\x1b["
COL_RESET=$ESC_SEQ"39;49;00m"
COL_RED=$ESC_SEQ"31;01m"
COL_GREEN=$ESC_SEQ"32;01m"
COL_YELLOW=$ESC_SEQ"33;01m"
COL_BLUE=$ESC_SEQ"34;01m"
COL_MAGENTA=$ESC_SEQ"35;01m"
COL_CYAN=$ESC_SEQ"36;01m"
_ANY_ERROR="NO"

red(){ echo -e "${COL_RED}$@${COL_RESET}";}
green(){ echo -e "${COL_GREEN}$@${COL_RESET}";}
yellow(){ echo -e "${COL_YELLOW}$@${COL_RESET}";}
blue(){ echo -e "${COL_BLUE}$@${COL_RESET}";}
magenta(){ echo -e "${COL_MAGENTA}$@${COL_RESET}";}
cyan(){ echo -e "${COL_CYAN}$@${COL_RESET}";}

## -- code --
yell() { echo -e "${COL_RESET}${COL_YELLOW}";}
si() {
    is "bad" $@
}

is() {
    local _now=$(date +%Y-%m-%d\ %H:%M:%S)
    local _is=$1
    shift
    echo -e $COL_RESET
    if [[ "${_is}" == "good" ]]; then
        _ANY_ERROR="NO"
        [[ $# > 0 ]] && green $now $@ || green $now "All good"
        return 0;
    elif [[ "${_is}" == "bad" ]]; then
        _ANY_ERROR="YES"
        [[ $# > 0 ]] && red $now $@ || red $now "did something break somewhere?"
        return 1
    else
        [[ ${_ANY_ERROR} == "NO" ]] && green $now ${_is:-"All ok, continuing"} $@ && return 0;
        red $now "ERROR:" ${_is:-""} $@ && return 1;
    fi
}


set -x
export NAME=python
export PREFIX=$(cd ~ && pwd)/local
export TMPDIR=$(mktemp -d)
cd $TMPDIR || si "Error cd to $TMPDIR" && exit 1


MSG="Downloading python, ez_setup, pip"
ERR="Failed downloding"
is $MSG && \
    (
        yell
        (\wget --no-check-certificate http://www.python.org/ftp/python/2.7.6/Python-2.7.6.tgz && tar -zxf *ython* && rm Python*tgz) &&\
        (\wget --no-check-certificate https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py) && \
        (\wget --no-check-certificate https://raw.github.com/pypa/pip/master/contrib/get-pip.py)
    ) || si $ERR


MSG="compiling python"
ERR="compiling failed"
is $MSG && \
    (
        cd *ython*/ && \
            ./configure --prefix=$PREFIX && \
            make && \
            make install
    ) || si $ERR


MSG="compiling python"
ERR="compiling failed"
is $MSG && \
    (
        PIP_DOWNLOAD_CACHE=$TMPDIR
        unset PIP_REQUIRE_VIRTUALENV
        unset PIP_VIRTUALENV_BASE
        cd $TMPDIR/$NAME && \
        $PREFIX/bin/python ez_setup.py && \
        $PREFIX/bin/python get-pip.py
    ) || si $ERR


MSG="pip installing sillyfacter "
ERR="pip installation failed"
is $MSG && \
    (
            $PREFIX/bin/pip install --allow-all-external --allow-unverified netifaces sillyfacter
    ) || si $ERR

green "Installed at $PREFIX/bin/sillyfacter"
