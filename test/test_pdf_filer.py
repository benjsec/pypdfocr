import os
import shutil

import pytest

from pypdfocr import pypdfocr


class TestPDFFiler:

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

    def test_file_by_filename(self, tmpdir, pdfocr, asset_dir):
        """
            Test filing of single pdf based on filename.
        """

        infile = os.path.join(asset_dir, "test_super_long_keyword.pdf")
        conffile = tmpdir.join("test.conf")
        conffile.write("""
            target_folder: "{dirpath}/target"
            default_folder: "{dirpath}/target/default"
            original_move_folder: "{dirpath}/original"

            folders:
                recipe:
                    - recipes
                patents:
                    - patent
            """.format(dirpath=str(tmpdir)))
        opts = [infile, "--config", str(conffile), "-f", "-n"]
        pdfocr.go(opts)

        outfile = infile.replace(".pdf", "_ocr.pdf")
        # File should not be in original location anymore
        assert not os.path.exists(outfile)

        # Assert the file move
        ocr_dest = os.path.join(
            str(tmpdir), "target", "recipe", os.path.basename(outfile))
        assert os.path.exists(ocr_dest)
