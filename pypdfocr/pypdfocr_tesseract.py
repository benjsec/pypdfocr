#!/usr/bin/env python2.7

# Copyright 2013 Virantha Ekanayake All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
   Run Tesseract to generate hocr file
"""

import logging
import os
import subprocess
import sys

from multiprocessing import Pool
from packaging import version
from .pypdfocr_interrupts import init_worker


class TesseractException(Exception):
    """Exception raised for problems with tesseract."""


def error(text):
    """Print `text` as error and terminate process."""
    logging.error(text)
    sys.exit(-1)


def unwrap_self(arg, **kwarg):
    """
    Ugly hack to pass in object method to the multiprocessing library
    From http://www.rueckstiess.net/research/snippets/show/ca1d7d90
    Basically gets passed in a pair of (self, arg), and calls the method
    """
    return PyTesseract.make_hocr_from_pnm(*arg, **kwarg)


class PyTesseract(object):
    """Class to wrap all the tesseract calls"""
    def __init__(self, config):
        """
           Detect windows tesseract location.
        """
        self.lang = 'eng'
        if str(os.name) == 'nt':
            # NT reports v3.02.02 as 3.02
            self.required = "3.02"
        else:
            self.required = "3.02.02"
        self.threads = config.get('threads', 4)
        self._ts_version = None

        if "binary" in config:  # Override location of binary
            binary = config['binary']
            if os.name == 'nt':
                binary = '"%s"' % binary
                binary = binary.replace("\\", "\\\\")
            logging.info("Setting location for tesseract executable to %s", binary)
        else:
            if str(os.name) == 'nt':
                # Explicit str here to get around some MagicMock stuff for
                # testing that I don't quite understand.
                binary = '"c:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe"'
            else:
                binary = "tesseract"

        self.binary = binary

        self.msgs = {
            'TS_MISSING': """
                Could not execute %s
                Please make sure you have Tesseract installed correctly
                """ % self.binary,
            'TS_VERSION':'Tesseract version is too old',
            'TS_img_MISSING':'Cannot find specified tiff file',
            'TS_FAILED': 'Tesseract-OCR execution failed!',
        }

    @property
    def ts_version(self):
        """Return the tesseract version string"""
        if self._ts_version is None:
            self._ts_version = self._get_ts_version()
        return self._ts_version

    def _get_ts_version(self):
        """Return the tesseract version string"""
        logging.info("Checking tesseract version")
        cmd = "%s -v" % self.binary
        logging.debug(cmd)
        try:
            ret_output = subprocess.check_output(
                cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        except subprocess.CalledProcessError:
            # Could not run tesseract
            error(self.msgs['TS_MISSING'])

        for line in ret_output.splitlines():
            if 'tesseract' in line:
                return line.split(' ')[1]
        error(self.msgs['TS_MISSING'])

    def assert_version(self):
        """Raise an exception if the tesseract version is too old."""
        if version.parse(self.required) > version.parse(self.ts_version):
            raise TesseractException(
                "Tesseract version too old. Required {} Found {}".format(
                self.required, self.ts_version))

    def _is_version_uptodate(self):
        """
            Make sure the version is current.
        """
        # Aargh, in windows 3.02.02 is reported as version 3.02.
        try:
            self.assert_version()
        except TesseractException:
            return False, self.ts_version
        return True, self.ts_version

    def make_hocr_from_pnms(self, fns):
        """Run OCR on multiple files."""
        uptodate, ver = self._is_version_uptodate()
        if not uptodate:
            error(self.msgs['TS_VERSION'] + " (found %s, required %s)" % (ver, self.required))

        logging.debug("Making pool for tesseract")
        pool = Pool(processes=self.threads, initializer=init_worker)

        try:
            hocr_filenames = pool.map(unwrap_self,
                                      list(zip([self]*len(fns), fns)))
            pool.close()
        except (KeyboardInterrupt, Exception):
            logging.info("Caught keyboard interrupt... terminating")
            pool.terminate()
            raise
        finally:
            pool.join()

        return list(zip(fns, hocr_filenames))


    def make_hocr_from_pnm(self, img_filename):
        """Run OCR on single file."""
        basename = os.path.splitext(img_filename)[0]
        if version.parse(self.ts_version) < version.parse("3.03"):
            # Output format is html for old versions of tesseract
            hocr_filename = "%s.html" % basename
        else:
            # Change extension to .hocr for tesseract 3.03 and higher
            hocr_filename = "%s.hocr" % basename

        if not os.path.exists(img_filename):
            error(self.msgs['TS_img_MISSING'] + " %s" % (img_filename))

        logging.info("Running OCR on %s to create %s",
                     img_filename, hocr_filename)
        cmd = '%s "%s" "%s" -psm 1 -c hocr_font_info=1 -l %s hocr' % (
            self.binary, img_filename, basename, self.lang)
        logging.debug(cmd)
        try:
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as err:
            # Could not run tesseract
            logging.error(err.output)
            logging.warning(self.msgs['TS_FAILED'])

        if os.path.isfile(hocr_filename):
            logging.info("Created %s", hocr_filename)
            return hocr_filename
        error(self.msgs['TS_FAILED'])
