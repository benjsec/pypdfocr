
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
    Provides capability to search PDFs and file to a specific folder based
    on keywords
"""

import logging

from PyPDF2 import PdfFileReader

from .pypdfocr_filer import PyFiler
from .pypdfocr_filer_dirs import PyFilerDirs


class PyPdfFiler(object):
    """Class for filing pdf files after OCR."""
    def __init__(self, filer):

        assert isinstance(filer, PyFiler)
        self.filer = filer  # Must be a subclass of PyFiler

        # Whether to fall back on filename for matching keywords against
        # if there is no match in the text
        self.file_using_filename = False
        self.file_original = self.filer.file_original

    @staticmethod
    def iter_pdf_page_text(filename):
        """Generator to return text from a pdf file."""
        reader = PdfFileReader(filename)
        logging.info("pdf scanner found %d pages in %s",
                     reader.getNumPages(), filename)
        for pgnum in range(reader.getNumPages()):
            text = reader.getPage(pgnum).extractText()
            text = text.replace('\n', ' ')
            yield text

    def _get_matching_folder(self, pdf_text):
        search_text = pdf_text.lower()
        for folder, strings in self.filer.folder_targets.items():
            for string in strings:
                logging.debug("Checking string %s", string)
                if string in search_text:
                    logging.info("Matched keyword '%s'", string)
                    return folder
        # No match found, so return
        return None

    def move_to_matching_folder(self, filename):
        """File the original based on keyword matching in text body."""
        for page_text in self.iter_pdf_page_text(filename):
            tgt_folder = self._get_matching_folder(page_text)
            if tgt_folder:
                # Stop searching through pdf pages as soon as we find a match
                break

        if not tgt_folder and self.file_using_filename:
            tgt_folder = self._get_matching_folder(filename)

        tgt_file = self.filer.move_to_matching_folder(filename, tgt_folder)
        return tgt_file


if __name__ == '__main__':
    FILER = PyPdfFiler(PyFilerDirs())
    for pg_text in FILER.iter_pdf_page_text("scan_ocr.pdf"):
        print(pg_text)
