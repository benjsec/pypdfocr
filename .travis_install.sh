#!/bin/bash

set -ev # exit on first error, print each command

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then

    # Install requirements on OS X
    brew update || brew update

    brew install tesseract ghostscript poppler imagemagick

    wget http://repo.continuum.io/miniconda/Miniconda3-3.7.0-MacOSX-x86_64.sh -O ~/miniconda.sh

    bash ~/miniconda.sh -b -p $HOME/miniconda
    export PATH="$HOME/miniconda/bin:$PATH"

    conda create --yes --name test_env python=${PYVER} pip
else
    # Install requirements on Linux
    sudo apt-get -qq update
    sudo apt-get install -y tesseract-ocr ghostscript imagemagick poppler-utils
fi;
