import os
import pytest
import shutil
import subprocess

from pypdfocr import pypdfocr_gs as P
from pypdfocr import pypdfocr_gs

from mock import patch
import mock


class TestGS:

    @pytest.mark.skipif(os.name != 'nt', reason="Not on NT")
    @patch('os.name')
    @patch('subprocess.check_output')
    def test_gs_set_nt(self, mock_subprocess, mock_os_name):
        """
            Check that we have a exe on windows
        """
        mock_os_name.__str__.return_value = 'nt'
        p = P.PyGs({})

        assert 'gswin' in p.binary

    @pytest.mark.skipif(os.name != 'nt', reason="Not on NT")
    @patch('os.name')
    @patch('subprocess.call')
    def test_gs_run_nt(self, mock_subprocess, mock_os_name, capsys):
        """
            Stupid test because Windows Tesseract only returns 3.02 instead
            of 3.02.02
        """
        mock_os_name.__str__.return_value = 'nt'
        p = P.PyGs({})

        mock_subprocess.return_value = -1
        p.binary = 'gsblah.exe'
        with pytest.raises(SystemExit):
            p._run_gs("", "", "")

        out, err = capsys.readouterr()
        assert p.msgs['GS_FAILED'] in out

    @pytest.fixture
    def pygs(self):
        return pypdfocr_gs.PyGs({})

    @pytest.fixture
    def asset_dir(self, tmpdir):
        """Copy the sample assets to a temporary directory and return path.
        """
        test_dir = str(tmpdir.join('source'))
        assets = os.path.join(os.path.dirname(__file__), 'pdfs')
        shutil.copytree(assets, test_dir)
        return test_dir

    def test_gs_pdf_missing(self, pygs, caplog):
        with pytest.raises(SystemExit):
            pygs.make_img_from_pdf("missing123.pdf")
        assert pygs.msgs['GS_MISSING_PDF'] in caplog.text

    def test_override_binary_nt(self, monkeypatch):
        monkeypatch.setattr('os.name', 'nt')
        pygs = pypdfocr_gs.PyGs({'binary': "c:\\foo\\bar\\bin"})
        assert pygs.binary == '"c:\\\\foo\\\\bar\\\\bin"'

    def test_override_binary_posix(self, monkeypatch):
        monkeypatch.setattr('os.name', 'posix')
        pygs = pypdfocr_gs.PyGs({'binary': "/foo/bar/bin/gs"})
        assert pygs.binary == '/foo/bar/bin/gs'

    def test_get_dpi_pdf_missing(self, pygs):
        with pytest.raises(SystemExit):
            pygs._get_dpi("/foo/bar.pdf")

    def test_get_dpi_fail(self, pygs, asset_dir, monkeypatch, caplog):
        monkeypatch.setattr(
            'subprocess.check_output',
            mock.Mock(side_effect=subprocess.CalledProcessError(returncode=2,
                                                                cmd=['bad'])))
        pygs._get_dpi(os.path.join(asset_dir, "test_recipe.pdf"))
        assert "not execute" in caplog.text

    def test_empty_pdf(self, pygs, asset_dir, caplog):
        pygs._get_dpi(os.path.join(asset_dir, "blank.pdf"))
        assert "Empty pdf" in caplog.text

    def test_pdfimages_malformed_output(
        self, pygs, asset_dir, monkeypatch, caplog):
        """This isn't a good test - should make a better one"""
        monkeypatch.setattr("subprocess.check_output",
                            mock.Mock(return_value="0\n1\n2 3 None"))
        """
        1     0 image    1692  2194  icc     1   8  jpeg   no         8  0   200   201  228K 6.3%
        """
        pygs._get_dpi(os.path.join(asset_dir, "test_recipe.pdf"))
        assert "Could not understand" in caplog.text

    def test_function_hi_dpi(self, pygs, asset_dir, caplog):
        pygs._get_dpi(os.path.join(asset_dir, "test_sherlock.pdf"))
        assert pygs.output_dpi == 400

    def test_function_low_dpi(self, pygs, asset_dir, caplog):
        pygs._get_dpi(os.path.join(asset_dir, "test_patent.pdf"))
        assert pygs.output_dpi == 300

    def test_functional_mismatched_dpi(self, pygs, asset_dir, caplog):
        pygs._get_dpi(os.path.join(asset_dir, "test.pdf"))
        assert pygs.output_dpi == 300
        assert "mismatch" in caplog.text

    def test_run_gs_error(self, pygs, caplog, monkeypatch):
        monkeypatch.setattr(
            "subprocess.check_output",
            mock.Mock(side_effect=subprocess.CalledProcessError(
                returncode=2, cmd=['bad'], output="ErrorOutput")))
        with pytest.raises(SystemExit):
            pygs._run_gs('foo', "out.pdf", "in.pdf")
        assert 'execution failed' in caplog.text

    def test_run_gs_error2(self, pygs, caplog, monkeypatch):
        monkeypatch.setattr(
            "subprocess.check_output",
            mock.Mock(side_effect=subprocess.CalledProcessError(
                returncode=2, cmd=['bad'],
                output="undefined in .getdeviceparams")))
        with pytest.raises(SystemExit):
            pygs._run_gs('foo', "out.pdf", "in.pdf")
        assert 'out of date' in caplog.text

    def test_functional_make_img(self, pygs, asset_dir):
        out = pygs.make_img_from_pdf(os.path.join(asset_dir, "test.pdf"))
        assert out == (300, os.path.join(asset_dir, "test_*.jpg"))

    def test_existing_img(self, pygs, asset_dir):
        """Existing jpg files in folder should be removed."""
        for fname in ["test_1.jpg", "test_A.jpg"]:
            with open(os.path.join(asset_dir, fname), 'w') as f:
                f.write("")
        out = pygs.make_img_from_pdf(os.path.join(asset_dir, "test.pdf"))
        assert out == (300, os.path.join(asset_dir, "test_*.jpg"))
        with open(os.path.join(asset_dir, "test_1.jpg"), 'rb') as f:
            assert f.read()
        assert not os.path.exists(os.path.join(asset_dir, "test_A.jpg"))
