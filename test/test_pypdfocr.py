from collections import namedtuple
import logging
import os
import shutil

import pytest
from mock import patch
from PyPDF2 import PdfFileReader

from pypdfocr import pypdfocr


Spec = namedtuple(
    "TestSpec", ["filename", "target_dir", "expected_ocr"])


class TestPydfocr:

    @pytest.fixture
    def pdfocr(self):
        return pypdfocr.PyPDFOCR()

    @pytest.fixture
    def asset_dir(self, tmpdir):
        """Copy the sample pdfs to a temporary directory and return its path.
        """
        test_dir = str(tmpdir.join('source'))
        pdfs = os.path.join(os.path.dirname(__file__), 'pdfs')
        shutil.copytree(pdfs, test_dir)
        return test_dir

    def _iter_pdf(self, filename):
        """Yield one page of PDF text at a time."""
        with open(filename, 'rb') as f:
            reader = PdfFileReader(f)
            logging.debug("pdf scanner found %d pages in %s",
                          reader.getNumPages(), filename)
            for pgnum in range(reader.getNumPages()):
                text = reader.getPage(pgnum).extractText()
                text = text.replace('\n', ' ')
                yield text

    filepath = os.path.dirname(__file__)
    pdf_tests = [
        Spec("test_recipe.pdf", "recipe", [["Simply Recipes"]]),
        Spec("test_patent.pdf", "patents",
             [
                 ["asynchronous", "Subject to", "20 Claims"],  # Page 1
                 ["FOREIGN PATENT"], ]),                       # Page 2
        Spec("test_sherlock.pdf", "default",
             [
                 ["Bohemia", "Trincomalee"],  # Page 1
                 ["hundreds of times"], ]),   # Page 2
        Spec("test_recipe_sideways.pdf", "recipe",
             [["Simply", "Recipes", "spinach"], ]),
    ]

    # @pytest.mark.skipif(True, reason="Just testing")
    @pytest.mark.parametrize("test_spec", pdf_tests)
    def test_standalone(self, test_spec, asset_dir, pdfocr):
        """
            Test the single file conversion with no filing.
            Checks for that _ocr file is created and keywords found in pdf.
            Modify :attribute:`pdf_tests` for changing keywords, etc

            :param expected: List of keywords lists per page.  expected[0][1]
            is the second keyword to assert on page 1
        """
        # Run a single file conversion

        infile = os.path.join(asset_dir, test_spec.filename)
        opts = [infile, '--skip-preprocess']
        pdfocr.go(opts)

        outfile = infile.replace(".pdf", "_ocr.pdf")
        assert os.path.exists(outfile)

        for pgnum, text in enumerate(self._iter_pdf(outfile)):
            print(u"\n----------------------\nPage {}\n{}".format(pgnum, text))
            for phrase in test_spec.expected_ocr[pgnum]:
                assert phrase in text

    # @pytest.mark.skipif(True, reason="just testing")
    @pytest.mark.parametrize("test_spec", [pdf_tests[0]])
    def test_standalone_email(self, test_spec, asset_dir, pdfocr, tmpdir):
        """
            Get coverage on the email after conversion of a single file.
            Use mock to stub out the smtpllib
        """
        # Run a single file conversion

        # Mock the smtplib to test the email functions
        with patch("smtplib.SMTP") as mock_smtp:

            infile = os.path.join(asset_dir, test_spec.filename)
            conffile = tmpdir.join("test.conf")
            conffile.write("""
                mail_smtp_server: "smtp.gmail.com:587"
                mail_smtp_login: "someone@gmail.com"
                mail_smtp_password: "blah"
                mail_from_addr: "someone#gmail.com"
                mail_to_list:
                    - "someone@gmail.com"
                """)
            opts = [infile, "--preprocess", "--config", str(conffile), "-m"]
            pdfocr.go(opts)

            # Assert the smtp calls
            instance = mock_smtp.return_value
            assert instance.starttls.called
            instance.login.assert_called_once_with("someone@gmail.com",
                                                   "blah")
            assert instance.sendmail.called


    # @pytest.mark.skipif(True, reason="just testing")
    @pytest.mark.parametrize("test_spec", pdf_tests[0:3])
    def test_filing(self, test_spec, asset_dir, pdfocr, tmpdir):
        """
            Test filing of single pdf. 
        """

        infile = os.path.join(asset_dir, test_spec.filename)
        conffile = tmpdir.join("test.conf")
        conffile.write("""
            target_folder: '{target_folder}'
            default_folder: '{default_folder}'

            folders:
                recipe:
                    - recipes
                patents:
                    - patent
            """.format(
                target_folder=os.path.join(str(tmpdir), 'target'),
                default_folder=os.path.join(str(tmpdir), 'target', 'default')))

        opts = [infile, '--skip-preprocess', "--config", str(conffile), "-f"]
        pdfocr.go(opts)

        outfile = test_spec.filename.replace(".pdf", "_ocr.pdf")

        # Assert the file move
        ocr_dest = os.path.join(
            str(tmpdir), "target", test_spec.target_dir, outfile)
        assert os.path.exists(ocr_dest)

    # @pytest.mark.skipif(True, reason="just testing")
    @pytest.mark.parametrize("test_spec", pdf_tests[0:3])
    def test_filing_move_original(self, test_spec, asset_dir, pdfocr, tmpdir):
        """
            Test filing of single pdf as well as moving original file.
        """

        infile = os.path.join(asset_dir, test_spec.filename)
        conffile = tmpdir.join("test.conf")
        conffile.write("""
            target_folder: '{target_folder}'
            default_folder: '{default_folder}'
            original_move_folder: '{original_folder}'

            folders:
                recipe:
                    - recipes
                patents:
                    - patent
            """.format(
                target_folder=os.path.join(str(tmpdir), 'target'),
                default_folder=os.path.join(str(tmpdir), 'target', 'default'),
                original_folder=os.path.join(str(tmpdir), 'original')))

        opts = [infile, "--config", str(conffile), "-f"]
        pdfocr.go(opts)

        outfile = test_spec.filename.replace(".pdf", "_ocr.pdf")

        # Assert the file move
        ocr_dest = os.path.join(
            str(tmpdir), "target", test_spec.target_dir, outfile)
        assert os.path.exists(ocr_dest)

        original_dest = os.path.join(
            str(tmpdir), "original", test_spec.filename)
        assert os.path.exists(original_dest)

    # @pytest.mark.skipif(True, reason="just testing")
    def test_set_binaries(self, pdfocr, tmpdir):
        """ Test the setup_exteral_tools
        """
        conffile = tmpdir.join("conf.yaml")
        conffile.write("""
            ghostscript:
                binary: /usr/bin/ghostscript
            tesseract:
                binary: /usr/bin/tesseract
            """)
        pdfocr.config = pdfocr.get_options(['foo.pdf', '-c', str(conffile)])
        # pdfocr.config["tesseract"] = {"binary":"/usr/bin/tesseract"}
        # pdfocr.config["ghostscript"] = {"binary":"/usr/bin/ghostscript"}
        pdfocr._setup_external_tools()
        if not os.name == 'nt':
            assert pdfocr.ts.binary == "/usr/bin/tesseract"
            assert pdfocr.gs.binary == "/usr/bin/ghostscript"
        else:
            assert pdfocr.ts.binary == '"/usr/bin/tesseract"'
            assert pdfocr.gs.binary == '"/usr/bin/ghostscript"'
