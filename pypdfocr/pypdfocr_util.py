
# Copyright 2015 Virantha Ekanayake All Rights Reserved.
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
import logging
import os
import time
"""
    Various utility classes
"""

class Retry(object):
    """Class to wrap function allowing for multiple attempts before failure
    """
    def __init__(self, func, tries=3, pause=1):
        self.func = func
        self.tries = tries
        self.pause = pause

    def call_with_retry(self):
        tries = self.tries

        val = None
        while tries > 0:
            try:
                val = self.func()
                tries = 0
            except Exception as err:
                logging.exception("intermediate failure")
                logging.info("Retrying (tries left %d)", tries-1)
                time.sleep(self.pause)
                tries -= 1
                if tries == 0:
                    raise err

        return val
