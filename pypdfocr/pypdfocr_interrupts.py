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

"""Handle keyboard interrupts in multiprocess workers gracefully."""

import signal
import logging

# Used for handling keyboard interrupts in Pools.
# Basically, throw an Exception when we see the ctrl-c, so that it
# actually is propagated to the parent class.


class KeyboardInterruptError(Exception):
    """Exception to raise for KeyboardInterrupt."""


def signal_handle(_signal, frame):
    """Handle signal interrupt by raising KeyboardInterruptError."""
    logging.debug("Stopping job")
    raise KeyboardInterruptError()


def init_worker():
    """Used for catching ctrl-c"""
    signal.signal(signal.SIGINT, signal_handle)
