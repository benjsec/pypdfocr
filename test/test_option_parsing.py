from pypdfocr import pypdfocr
import pytest


class TestOptions:

    @pytest.fixture
    def pdfocr(self):
        """Return a PyPDFOCR instance"""
        return pypdfocr.PyPDFOCR()

    @pytest.fixture
    def conffile(self, tmpdir):
        """Create a conf file and return its path"""
        conf = tmpdir.join('conf.txt')
        conf.write('target_folder: "blah"')
        return str(conf)

    def test_filename(self, pdfocr):
        """Test basic options with just a single filename"""
        opts = ["foo.pdf"]
        pdfocr.get_options(opts)
        assert pdfocr.pdf_filename == "foo.pdf"
        assert pdfocr.skip_preprocess is True
        assert pdfocr.enable_filing is False
        assert pdfocr.config == {}

    def test_debug(self, pdfocr):
        """Debug flag should enable debugging log level"""
        opts = ["foo.pdf", "--debug"]
        pdfocr.get_options(opts)
        assert pdfocr.debug is True
        assert pdfocr.verbose is False

    def test_verbose(self, pdfocr):
        """Verbose flag should enable verbose log level"""
        opts = ["foo.pdf", "-v"]
        pdfocr.get_options(opts)
        assert pdfocr.debug is False
        assert pdfocr.verbose is True

    def test_email_no_config(self, pdfocr):
        """Should raise error for email filing with no config file"""
        opts = ["foo.pdf", "-m"]
        with pytest.raises(SystemExit):
            pdfocr.get_options(opts)

    def test_email(self, pdfocr, conffile):
        """Send email option should enable sending email"""
        opts = ["foo.pdf", "--mail", "-c", conffile]
        pdfocr.get_options(opts)
        assert pdfocr.enable_email is True
        assert pdfocr.config

    def test_config_file_missing(self, pdfocr):
        """Should raise error if config file is missing"""
        opts = ["foo.pdf", "-c", "missing.file"]
        with pytest.raises(IOError):
            pdfocr.get_options(opts)

    def test_watch_dir(self, pdfocr):
        """Watch dir flag should enable watching specified dir"""
        opts = ["-w", "watch_dir"]
        pdfocr.get_options(opts)
        assert pdfocr.pdf_filename is None
        assert pdfocr.watch_dir == "watch_dir"
        assert pdfocr.watch is True

    def test_preprocess(self, pdfocr):
        """Preprocess flag should disable skip_preprocessing"""
        opts = ["foo.pdf", "--preprocess"]
        pdfocr.get_options(opts)
        assert pdfocr.skip_preprocess is False

    def test_skip_preprocess(self, pdfocr, caplog):
        """Skip_preprocess is deprecated."""
        opts = ["foo.pdf", "--skip-preprocess"]
        pdfocr.get_options(opts)
        assert '--skip-preprocess' in caplog.text

    def test_filing_no_config(self, pdfocr):
        """Should raise error for filing with no config file passed"""
        opts = ["foo.pdf", "--file"]
        with pytest.raises(SystemExit):
            pdfocr.get_options(opts)

    def test_filing(self, pdfocr, conffile):
        """Filing option should enable filing"""
        opts = ["foo.pdf", "-f", "-c", conffile]
        pdfocr.get_options(opts)
        assert pdfocr.enable_filing is True
        assert pdfocr.config
        assert pdfocr.watch is False

    def test_watch_conflict(self, pdfocr):
        """When pdf file is specified, we don't want to allow watch option"""
        opts = ["blah.pdf", '-w']
        with pytest.raises(SystemExit):
            pdfocr.get_options(opts)

    def test_evernote(self, pdfocr, conffile, monkeypatch):
        """Enabling evernote should enable filing automatically"""
        monkeypatch.setattr('pypdfocr.pypdfocr.evernote_enabled', True)
        opts = ["foo.pdf", "--evernote", "-c", conffile]
        pdfocr.get_options(opts)
        assert pdfocr.enable_evernote is True
        assert pdfocr.enable_filing is True
        assert pdfocr.watch is False

    def test_evernote_disabled(self, pdfocr, conffile, monkeypatch):
        """If evernote is not enabled, filing should not enable itself."""
        monkeypatch.setattr('pypdfocr.pypdfocr.evernote_enabled', False)
        opts = ["foo.pdf", "-e", "-c", conffile]
        pdfocr.get_options(opts)
        assert pdfocr.enable_evernote is False
        assert pdfocr.enable_filing is False

    def test_no_evernote_dir_filing(self, pdfocr, conffile, monkeypatch):
        """If evernote disabled, filing should not disable itself."""
        monkeypatch.setattr('pypdfocr.pypdfocr.evernote_enabled', False)
        opts = ["foo.pdf", "-e", "-f", "-c", conffile]
        pdfocr.get_options(opts)
        assert pdfocr.enable_evernote is False
        assert pdfocr.enable_filing is True
