import os

from pypdfocr import pypdfocr_filer


def test_class_methods():
    pf = pypdfocr_filer.PyFiler()

    assert not pf.target_folder
    pf.target_folder = "Target"
    assert pf.target_folder == "Target"

    assert not pf.default_folder
    pf.default_folder = "Default"
    assert pf.default_folder == "Default"

    assert not pf.original_move_folder
    pf.original_move_folder = "Original"
    assert pf.original_move_folder == "Original"

    assert not pf.folder_targets
    pf.folder_targets = "Targets"
    assert pf.folder_targets == "Targets"


def test_split_filename():
    path, name, ext = pypdfocr_filer.PyFiler._split_filename_dir_filename_ext(
        "/home/user/Documents/foobar.ext")
    assert path == "/home/user/Documents"
    assert name == "foobar"
    assert ext == ".ext"


def test_get_filename(tmpdir):
    pf = pypdfocr_filer.PyFiler()
    fpath = tmpdir.join("file.ext")
    newpath = pf._get_unique_filename_by_appending_version_integer(str(fpath))
    assert newpath == fpath


def test_get_filename_conflict(tmpdir):
    pf = pypdfocr_filer.PyFiler()
    fpath = tmpdir.join("file.ext")
    fpath.write("foobar")
    newpath = pf._get_unique_filename_by_appending_version_integer(str(fpath))
    assert newpath != fpath
    assert os.path.split(newpath)[0] == os.path.split(fpath)[0]
    assert os.path.splitext(newpath)[1] == os.path.splitext(fpath)[1]


def test_get_filename_conflict2(tmpdir):
    pf = pypdfocr_filer.PyFiler()
    fnames = ["file.ext", "file_1.ext", "file_2.ext"]
    fpaths = [tmpdir.join(fname) for fname in fnames]
    for fpath in fpaths:
        fpath.write("foobar")
    newpath = pf._get_unique_filename_by_appending_version_integer(
        str(fpaths[0]))
    assert newpath not in fpaths
    assert os.path.split(newpath)[0] == os.path.split(fpath)[0]
    assert os.path.splitext(newpath)[1] == os.path.splitext(fpath)[1]
