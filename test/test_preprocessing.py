import os
import shutil

import mock
import pytest

from pypdfocr import pypdfocr_preprocess


@pytest.fixture
def pypre():
    return pypdfocr_preprocess.PyPreprocess({})


@pytest.fixture
def asset_dir(tmpdir):
    """Copy the sample assets to a temporary directory and return path.
    """
    test_dir = str(tmpdir.join('source'))
    assets = os.path.join(os.path.dirname(__file__), 'pdfs')
    shutil.copytree(assets, test_dir)
    return test_dir


def test_config(pypre):
    assert pypre.threads == 4
    pypre = pypdfocr_preprocess.PyPreprocess({'threads': 1})
    assert pypre.threads == 1


def test_functional(pypre, asset_dir):
    """Check a processed file is not the same as it was before"""
    outp = pypre.preprocess([os.path.join(asset_dir, "sample.jpg"), ])
    assert os.path.split(outp[0])[1] == "sample_preprocess.jpg"
    with open(outp[0], 'rb') as outfile:
        with open(os.path.join(asset_dir, "sample.jpg"), 'rb') as infile:
            assert infile.read() != outfile.read()


def test_infile_missing(pypre):
    """If the input file can't be found, the same filename is returned."""
    assert pypre._run_preprocess('infile.jpg') == 'infile.jpg'


def test_keyboard_interrupt(pypre, monkeypatch, caplog):
    """Exceptions should be logged and re-raised"""
    monkeypatch.setattr(
        pypre, 'cmd',
        mock.Mock(side_effect=Exception("Boom!")))
    with pytest.raises(Exception):
        pypre.preprocess(['foo.jpg'])
    assert "keyboard interrupt" in caplog.text
