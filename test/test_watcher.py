import os
import time
from collections import namedtuple

import pytest
from mock import patch

from pypdfocr import pypdfocr_watcher as P
from pypdfocr import pypdfocr_watcher


class TestWatching:

    filenames = [("test_recipe.pdf", "test_recipe.pdf"),
                 (os.path.join("..", "test_recipe.pdf"),
                  os.path.join("..", "test_recipe.pdf")),
                 (os.path.join("/", "Volumes", "Media", "test_recipe.pdf"),
                  os.path.join("/", "Volumes", "Media", "test_recipe.pdf")),
                 (os.path.join("/", "Volumes", "Media", "test recipe.pdf"),
                  os.path.join("/", "Volumes", "Media", "test_recipe.pdf")),
                 (os.path.join("..", "V olumes", "Media", "test recipe.pdf"),
                  os.path.join("..", "V olumes", "Media", "test_recipe.pdf")),
                ]

    @pytest.fixture
    def watcher(self, tmpdir):
        return pypdfocr_watcher.PyPdfWatcher(
            monitor_dir=str(tmpdir.mkdir("tmp")),
            config={})

    @patch('shutil.move')
    @pytest.mark.parametrize(("filename, expected"), filenames)
    def test_rename(self, mock_move, filename, expected, watcher):
        # First, test code that does not move original
        assert watcher.rename_file_with_spaces(filename) == expected

    def test_check_for_new_pdf(self, watcher):
        # PDFs ending _ocr.pdf should not be added to queue
        watcher.check_for_new_pdf("blah_ocr.pdf")
        assert "blah_ocr.pdf" not in watcher.events
        # Other PDFs should be added to queue
        watcher.check_for_new_pdf("blah.pdf")
        assert "blah.pdf" in watcher.events
        # Set timestamp to expired and check pdf is removed.
        watcher.events['blah.pdf'] = -1
        watcher.check_for_new_pdf("blah.pdf")
        assert "blah.pdf" not in watcher.events
        watcher.check_for_new_pdf("blah.pdf")
        watcher.events['blah.pdf'] = time.time() - 4
        watcher.check_for_new_pdf("blah.pdf")
        # Check that time stamp was updated
        assert watcher.events['blah.pdf'] - time.time() <= 1

    def test_events(self, watcher):

        event = namedtuple('event', 'src_path, dest_path')

        watcher.on_created(event(src_path='temp_recipe.pdf', dest_path=None))
        assert 'temp_recipe.pdf' in watcher.events

        watcher.on_moved(event(src_path=None, dest_path='temp_recipe2.pdf'))
        assert 'temp_recipe2.pdf' in watcher.events

        watcher.on_modified(event(src_path='temp_recipe3.pdf', dest_path=None))
        assert 'temp_recipe3.pdf' in watcher.events

    def test_check_queue(self, watcher):
        # Add item to queue, when first checking should do nothing
        assert watcher.events == {}
        watcher.events['blah.pdf'] = time.time()
        assert watcher.check_queue() is None
        assert 'blah.pdf' in watcher.events
        # Expire timestamp for item, checking queue should return filename
        watcher.events['blah.pdf'] = time.time() - 4
        assert watcher.check_queue() == 'blah.pdf'
        assert watcher.events['blah.pdf'] == -1
        # After returning filename once, check it's removed from the queue
        assert watcher.check_queue() is None
        assert 'blah.pdf' not in watcher.events
