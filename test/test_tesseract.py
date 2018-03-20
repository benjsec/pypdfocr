import os
import shutil
import subprocess

import pytest
import mock

from pypdfocr import pypdfocr_tesseract


class TestTesseract:

    @pytest.fixture
    def pyts(self):
        return pypdfocr_tesseract.PyTesseract({})

    @pytest.mark.skipif(os.name == 'nt', reason='Does not work on Windows')
    def test_version_shorter_older(self, pyts):
        pyts._ts_version = "3.02"
        pyts.required = "3.02.02"
        with pytest.raises(pypdfocr_tesseract.TesseractException):
            pyts.assert_version()

    def test_version_minor_older(self, pyts):
        pyts._ts_version = "3.02.01"
        pyts.required = "3.02.02"
        with pytest.raises(pypdfocr_tesseract.TesseractException):
            pyts.assert_version()

    def test_version_major_older(self, pyts):
        pyts._ts_version = "2.03.03"
        pyts.required = "3.02.02"
        with pytest.raises(pypdfocr_tesseract.TesseractException):
            pyts.assert_version()

    @pytest.mark.skipif(os.name == 'nt', reason='Does not work on Windows')
    def test_version_major_equal(self, pyts):
        pyts._ts_version = "3.02.02"
        pyts.required = "3.02.02"
        pyts.assert_version()

    def test_version_major_newer(self, pyts):
        pyts._ts_version = "4.01"
        pyts.required = "3.02.02"
        pyts.assert_version()

    def test_version_minor_newer(self, pyts):
        pyts._ts_version = "3.02"
        pyts.required = "3.01.02"
        pyts.assert_version()
        assert (pyts._is_version_uptodate()) == (True, "3.02")

    def test_get_actual_version(self, pyts):
        assert pyts.ts_version

    def test_tesseract_presence(self, pyts, caplog):
        pyts.binary = "tesserac"  # Misspell it and make sure we get an error
        with pytest.raises(SystemExit):
            assert pyts.ts_version
        assert pyts.msgs['TS_MISSING'] in caplog.text

    def test_tesseract_version(self, pyts, caplog):
        pyts.required = "100.01"
        with pytest.raises(SystemExit):
            pyts.make_hocr_from_pnms("")
        assert pyts.msgs['TS_VERSION'] in caplog.text

    def test_tiff_file_check(self, pyts, caplog):
        with pytest.raises(SystemExit):
            pyts.make_hocr_from_pnm("DUMMY_NOTPRESENT.tiff")
        assert pyts.msgs['TS_img_MISSING'] in caplog.text

    def test_override_binary(self):
        pyts = pypdfocr_tesseract.PyTesseract({'binary': '/foo/bar/bin'})
        assert '/foo/bar/bin' in pyts.binary

    def test_override_binary_nt(self, monkeypatch):
        monkeypatch.setattr("os.name", "nt")
        pyts = pypdfocr_tesseract.PyTesseract({'binary': '\\foo\\bar\\bin'})
        assert pyts.binary == '"\\\\foo\\\\bar\\\\bin"'

    def test_tesseract_malformed_output(self, monkeypatch, pyts, caplog):
        # Test if version string not found in tesseract output
        monkeypatch.setattr("subprocess.check_output",
                            mock.Mock(return_value="foobar 04.01"))
        with pytest.raises(SystemExit):
            assert pyts.ts_version is None
        assert "not execute" in caplog.text

    def test_tesseract_version_nt(self, monkeypatch):
        """
            Stupid test because Windows Tesseract only returns 3.02 instead
            of 3.02.02
        """
        monkeypatch.setattr('os.name', 'nt')
        monkeypatch.setattr('subprocess.check_output',
                            mock.Mock(return_value="tesseract 3.02"))
        pyts = pypdfocr_tesseract.PyTesseract({})
        pyts.assert_version()

    def test_tesseract_4alpha(self, monkeypatch, tmpdir):
        monkeypatch.setattr('subprocess.check_output',
                            mock.Mock(return_value="tesseract 4.00.00alpha"))
        pyts = pypdfocr_tesseract.PyTesseract({})
        pyts.assert_version()

    def test_force_Nt(self, monkeypatch, tmpdir):
        monkeypatch.setattr('os.name', 'nt')
        monkeypatch.setattr('os.path.exists', mock.Mock(return_value=True))
        pyts = pypdfocr_tesseract.PyTesseract({})
        pyts._ts_version = "4.01"
        assert 'tesseract.exe' in pyts.binary
        
        # force a bad tesseract on windows
        pyts.binary = "blah"
        with pytest.raises(SystemExit):
            pyts.make_hocr_from_pnm(str(tmpdir.join('blah.tiff')))

    def test_tesseract_fail(self, caplog, monkeypatch, tmpdir):
        """
            Get all the checks passed and make sure we report the case where
            tesseract returns a non-zero status.
        """
        monkeypatch.setattr('os.name', 'nt')
        monkeypatch.setattr('os.path.exists', mock.Mock(return_value=True))
        monkeypatch.setattr('subprocess.check_output', mock.Mock(side_effect=subprocess.CalledProcessError(-1 , 'Boom')))
        pyts = pypdfocr_tesseract.PyTesseract({})
        pyts._ts_version = "4.01"
        assert 'tesseract.exe' in pyts.binary

        with pytest.raises(SystemExit):
            pyts.make_hocr_from_pnm(str(tmpdir.join('blah.tiff')))
        assert pyts.msgs['TS_FAILED'] in caplog.text

    @pytest.mark.parametrize(
        ("version", "ext"), [("3.02.02", "html"), ("3.03.01", "hocr")])
    def test_tesseract_old_output(self, version, ext, monkeypatch):
        """Test that correct extension is used based on tesseract version

        Old versions of tesseract (before 3.03) created .html files, whereas
        more recent versions create .hocr files.
        """
        monkeypatch.setattr('os.path.exists', mock.Mock(return_value=True))
        monkeypatch.setattr('os.path.isfile', mock.Mock(return_value=True))
        monkeypatch.setattr('subprocess.call', mock.Mock(return_value=0))
        pyts = pypdfocr_tesseract.PyTesseract({})
        pyts._ts_version = version
        assert pyts.make_hocr_from_pnm('foo.tiff') == 'foo.{}'.format(ext)

    @pytest.mark.skipif(os.name=='nt', reason='Stalls on Windows')
    def test_make_hocrs_pool(self, monkeypatch, pyts):
        """Test parsing multiple tiff in a batch.

        Need to compare sets as pool can return in any order.
        This may be patching a bit too much out, but don't want to ocr
        multiple files for a test.
        """
        monkeypatch.setattr('os.path.exists', mock.Mock(return_value=True))
        monkeypatch.setattr('os.path.isfile', mock.Mock(return_value=True))
        monkeypatch.setattr('subprocess.call', mock.Mock(return_value=0))
        assert set(pyts.make_hocr_from_pnms(['foo.tiff', 'bar.tiff'])) == \
            set([("foo.tiff", "foo.hocr"), ("bar.tiff", "bar.hocr")])

    @pytest.fixture
    def asset_dir(self, tmpdir):
        """Copy the sample assets to a temporary directory and return path.
        """
        test_dir = str(tmpdir.join('source'))
        assets = os.path.join(os.path.dirname(__file__), 'pdfs')
        shutil.copytree(assets, test_dir)
        return test_dir

    def test_functional(self, pyts, asset_dir):
        """Test actually running tesseract."""
        outp = pyts.make_hocr_from_pnm(os.path.join(asset_dir, 'sample.jpg'))
        assert outp == os.path.join(asset_dir, "sample.hocr")
        assert os.path.exists(outp)
        with open(outp) as f:
            assert 'Lorum' in f.read()
