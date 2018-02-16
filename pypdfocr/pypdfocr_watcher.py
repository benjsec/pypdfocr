"""
Something
"""

import logging
import os
import shutil
import time

from threading import Lock

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class PyPdfWatcher(FileSystemEventHandler):
    """
        Watch a folder for new pdf files.

        If new file event, then add it to queue with timestamp.
        If file mofified event, then change timestamp in queue.
        Every few seconds pop-off queue and if timestamp older than 3 seconds,
        process the file else, push it back onto queue.
    """

    def __init__(self, monitor_dir, config):
        FileSystemEventHandler.__init__(self)

        self.events = {}
        self.events_lock = Lock()

        self.monitor_dir = monitor_dir
        if not config:
            config = {}

        # If no updates in 3 seconds (or option in config file) process file
        self.scan_interval = config.get('scan_interval', 3)
        self.observer = None

    def start(self):
        """Create an oberserver and start it."""
        self.observer = Observer()
        self.observer.schedule(self, self.monitor_dir)
        self.observer.start()
        print("Starting to watch for new pdfs in %s" % (self.monitor_dir))
        while True:
            logging.info("Sleeping for %d seconds", self.scan_interval)
            time.sleep(self.scan_interval)
            newfile = self.check_queue()
            if newfile:
                yield newfile
        self.observer.join()

    def stop(self):
        """Stop the observer."""
        self.observer.stop()

    @staticmethod
    def rename_file_with_spaces(pdf_filename):
        """
            Rename any portion of a filename that has spaces in the basename
            with underscores.
            Does not affect spaces in the directory path.

            :param pdf_filename: Filename to remove spaces
            :type pdf_filename: string
            :returns: Modified filename
            :rtype: string
        """
        filepath, filename = os.path.split(pdf_filename)
        if ' ' in filename:
            newfilename = os.path.join(filepath, filename.replace(' ', '_'))
            logging.debug("Renaming spaces")
            logging.debug("---> %s \n ------> %s", pdf_filename, newfilename)
            shutil.move(pdf_filename, newfilename)
            return newfilename
        return pdf_filename

    def check_for_new_pdf(self, ev_path):
        """
            Called by the file watching api on any file.
            creations/modifications. For any file ending with ".pdf", but not
            "_ocr.pdf", it adds new files to the event queue with the current
            time stamp, or it updates existing files in the queue with the
            current timestamp.  This queue is used to track files and keep
            track of their last "touched" time, so we can start processing a
            file if :func:`check_queue` finds a file that hasn't been touched
            in a while.

            If the file does note exist in the events dict:

                - Add it with the current time

            Otherwise:

                - If the file time is marked as -1, delete it from the dict
                - Else, update the time in the dict to the current time

        """
        if ev_path.endswith(".pdf"):
            if not ev_path.endswith(("_ocr.pdf", "_test.pdf")):
                self.events_lock.acquire()
                if not ev_path in self.events:
                    self.events[ev_path] = time.time()
                    logging.info("Adding %s to event queue", ev_path)
                else:
                    if self.events[ev_path] == -1:
                        logging.info("%s removing from event queue", ev_path)
                        del self.events[ev_path]
                    else:
                        newtime = time.time()
                        logging.debug(
                            "%s already in event queue, updating timestamp to %d",
                            ev_path, newtime)
                        self.events[ev_path] = newtime
                self.events_lock.release()

    def on_created(self, event):
        """Method called when file is created."""
        logging.debug("on_created: %s at time %d", event.src_path, time.time())
        self.check_for_new_pdf(event.src_path)

    def on_moved(self, event):
        """Method called when file is moved."""
        logging.debug("on_moved: %s", event.src_path)
        self.check_for_new_pdf(event.dest_path)

    def on_modified(self, event):
        """Method called when file is modified."""
        logging.debug("on_modified: %s", event.src_path)
        self.check_for_new_pdf(event.src_path)

    def check_queue(self):
        """
            This function is called at regular intervals by :func:`start`.

            Iterate through the events, and if there is any with a timestamp
            greater than the scan_interval, return it and set its timestamp to
            -1 for purging later.

            :returns: Filename if available to process, otherwise None.
        """
        now = time.time()
        self.events_lock.acquire()
        self.events = {file:ts for file, ts in self.events.items() if ts != -1}
        for monitored_file, timestamp in self.events.items():
            if now - timestamp > self.scan_interval:
                logging.info("Processing new file %s", monitored_file)
                # Remove this file from the dict
                del self.events[monitored_file]
                monitored_file = self.rename_file_with_spaces(monitored_file)
                # Add back into queue and mark as not needing further action in the event handler
                self.events[monitored_file] = -1
                self.events_lock.release()
                return monitored_file
        self.events_lock.release()
        return None
