import pytest

from pypdfocr import pypdfocr_pdffiler
from pypdfocr import pypdfocr_filer_dirs


class MockReader:
    def __init__(self, filepath):
        self.filepath = filepath

    def getNumPages(self):
        return 1

    def getPage(self, pgnum):
        return self

    def extractText(self):
        with open(self.filepath) as f:
            return f.read()


class TestPDFFiler2:

    @pytest.fixture
    def pdffiler(self, tmpdir):
        """Create an instance of pdffiler with appropriate settings"""
        filer = pypdfocr_filer_dirs.PyFilerDirs()
        filer.add_folder_target("keyword", ["keyword", ])
        filer.default_folder = "default"
        filer.target_folder = str(tmpdir.join("target"))
        return pypdfocr_pdffiler.PyPdfFiler(filer)

    @pytest.fixture(autouse=True)
    def mock_reader(self, monkeypatch):
        """Mock the pdf reader to allow reading our txt file instead."""
        monkeypatch.setattr(
            "pypdfocr.pypdfocr_pdffiler.PdfFileReader", MockReader)

    def test_file_to_default(self, tmpdir, pdffiler):
        """Test filing a single pdf to the default folder."""
        infile = tmpdir.join("test.txt")
        infile.write("Lorum Ipsum")
        outpath = pdffiler.move_to_matching_folder(str(infile))
        assert outpath == str(tmpdir.join("target/default/test.txt"))

    def test_file_by_filename(self, tmpdir, pdffiler):
        """Test filing a single pdf based on filename."""
        pdffiler.file_using_filename = True
        infile = tmpdir.join("keyword.txt")
        infile.write("Lorum Ipsum")
        outpath = pdffiler.move_to_matching_folder(str(infile))
        assert outpath == str(tmpdir.join("target/keyword/keyword.txt"))

    def test_file_by_keyword(self, tmpdir, pdffiler):
        """Test filing a single pdf based on keyword."""
        infile = tmpdir.join("test.txt")
        infile.write("Lorum Keyword Ipsum")
        outpath = pdffiler.move_to_matching_folder(str(infile))
        assert outpath == str(tmpdir.join("target/keyword/test.txt"))
