import os
import sys

import mock
import pytest

from pypdfocr import pypdfocr_util as utils


class TestRetry:
    def test_simple_call(self):
        m = mock.Mock(return_value="Boo")
        r = utils.Retry(m, tries=1)
        assert r.call_with_retry() == "Boo"
        m.assert_called_once()

    def test_call_fail(self):
        m = mock.Mock(side_effect=ValueError)
        r = utils.Retry(m, tries=2, pause=0)
        with pytest.raises(ValueError):
            r.call_with_retry()
        assert m.call_count == 2

    def test_call_fail_first(self):
        m = mock.Mock(side_effect=[ValueError, "Boo"])
        r = utils.Retry(m, tries=2, pause=0)
        assert r.call_with_retry() == "Boo"
        assert m.call_count == 2