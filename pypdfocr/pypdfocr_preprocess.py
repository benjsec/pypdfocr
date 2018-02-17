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
    Wrap ImageMagick calls.  Yes, this is ugly.
"""

import logging
import os
import subprocess

from multiprocessing import Pool
from .pypdfocr_interrupts import init_worker


def unwrap_self(arg, **kwarg):
    """
    Ugly hack to pass in object method to the multiprocessing library
    From http://www.rueckstiess.net/research/snippets/show/ca1d7d90
    Basically gets passed in a pair of (self, arg), and calls the method
    """
    return PyPreprocess._run_preprocess(*arg, **kwarg)


class PyPreprocess(object):
    """Class to wrap all the ImageMagick convert calls"""
    def __init__(self, config):
        self.msgs = {
            'CV_FAILED': 'convert execution failed', }
        self.threads = config.get('threads', 4)

    def cmd(self, cmd_list):
        """Run command as subprocess and return output."""
        if isinstance(cmd_list, list):
            cmd_list = ' '.join(cmd_list)
        logging.debug("Running cmd: %s", cmd_list)
        try:
            out = subprocess.check_output(
                cmd_list, stderr=subprocess.STDOUT, shell=True)
            logging.debug(out)
            return out
        except subprocess.CalledProcessError as err:
            logging.debug(err.output)
            logging.warning("Could not run command %s", cmd_list)

    def _run_preprocess(self, in_filename):
        basename, filext = os.path.splitext(in_filename)
        out_filename = '%s_preprocess%s' % (basename, filext)
        # When using Windows, can't use backslash parenthesis in the shell
        if str(os.name) == 'nt':
            backslash = ''
        else:
            backslash = '\\'

        cmd_list = [
            'convert',
            '"%s"' % in_filename,
            '-respect-parenthesis',
            backslash + '(',
            '-clone 0',
            '-colorspace gray',
            '-negate',
            '-lat 15x15+5%',
            '-contrast-stretch 0',
            backslash + ')',
            '-compose copy_opacity',
            '-composite',
            '-opaque none +matte',
            '-modulate 100,100',
            #'-adaptive-blur 1.0',
            '-blur 1x1',
            #'-selective-blur 4x4+5%',
            '-adaptive-sharpen 0x2',
            '-negate -define morphology:compose=darken '
            '-morphology Thinning Rectangle:1x30+0+0 -negate ',
            # Removes vertical lines >=60 pixes, reduces width of >30
            # (otherwise tesseract < 3.03 completely ignores text close to
            # vertical lines in a table)
            '"%s"' % (out_filename)
            ]
        if str(os.name) == 'nt':
            cmd_list = ['magick'] + cmd_list
        logging.info("Preprocessing image %s for better OCR", in_filename)
        res = self.cmd(cmd_list)
        if res is None:
            return in_filename
        return out_filename

    def preprocess(self, in_filenames):
        """Preprocess multiple files."""
        fns = in_filenames

        pool = Pool(processes=self.threads, initializer=init_worker)
        try:
            logging.info("Starting preprocessing parallel execution")
            preprocessed_filenames = pool.map(
                unwrap_self, zip([self]*len(fns), fns))
            pool.close()
        except (KeyboardInterrupt, Exception):
            logging.error("Caught keyboard interrupt... terminating")
            pool.terminate()
            raise
        finally:
            pool.join()

        logging.info("Completed preprocessing")
        logging.debug("Output filenames: %s", preprocessed_filenames)
        return preprocessed_filenames
