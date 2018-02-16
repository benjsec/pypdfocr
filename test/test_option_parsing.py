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
        return conf

    def test_filename(self, pdfocr):
        """Test basic options with just a single filename"""
        opts = ["foo.pdf"]
        config = pdfocr.get_options(opts)
        assert config.pdf_filename == "foo.pdf"
        assert config.enable_filing is False

    def test_debug(self, pdfocr):
        """Debug flag should enable debugging log level"""
        opts = ["foo.pdf", "--debug"]
        config = pdfocr.get_options(opts)
        assert config.debug is True
        assert config.verbose is False

    def test_verbose(self, pdfocr):
        """Verbose flag should enable verbose log level"""
        opts = ["foo.pdf", "-v"]
        config = pdfocr.get_options(opts)
        assert config.debug is False
        assert config.verbose is True

    @pytest.mark.xfail(reason="Config checking not done here anymore")
    def test_email_no_config(self, pdfocr):
        """Should raise error for email filing with no config file"""
        opts = ["foo.pdf", "-m"]
        with pytest.raises(SystemExit):
            pdfocr.get_options(opts)

    def test_email(self, pdfocr, conffile):
        """Send email option should enable sending email"""
        conffile.write("""
            email:
                target: True
            """)
        opts = ["foo.pdf", "--mail", "-c", str(conffile)]
        config = pdfocr.get_options(opts)
        assert config.mail is True
        assert config.email['target']

    def test_config_file_missing(self, pdfocr):
        """Should raise error if config file is missing"""
        opts = ["foo.pdf", "-c", "missing.file"]
        with pytest.raises(IOError):
            pdfocr.get_options(opts)

    def test_watch_dir(self, pdfocr):
        """Watch dir flag should enable watching specified dir"""
        opts = ["-w", "watch_dir"]
        config = pdfocr.get_options(opts)
        assert config.pdf_filename is None
        assert config.watch_dir == "watch_dir"
        # assert pdfocr.watch is True

    def test_preprocess(self, pdfocr):
        """Preprocess flag should disable skip_preprocessing"""
        opts = ["foo.pdf", "--preprocess"]
        config = pdfocr.get_options(opts)
        assert config.skip_preprocess is False

    def test_default_skip_preprocess(self, pdfocr):
        opts = ["foo.pdf"]
        config = pdfocr.get_options(opts)
        assert config.skip_preprocess is True

    def test_skip_preprocess(self, pdfocr):
        """Skip_preprocess is deprecated."""
        opts = ["foo.pdf", "--skip-preprocess"]
        config = pdfocr.get_options(opts)
        assert config.skip_preprocess is True

    @pytest.mark.xfail(reason="Not checking for config yet.")
    def test_filing_no_config(self, pdfocr):
        """Should raise error for filing with no config file passed"""
        opts = ["foo.pdf", "--file"]
        with pytest.raises(SystemExit):
            pdfocr.get_options(opts)

    @pytest.mark.xfail(reason="Not checking for full config yet.")
    def test_filing_incomplete_config(self, pdfocr, conffile):
        """Should raise error for filing with missing sections of conf file"""
        conffile.write("""
            foo: bar
            """)
        opts = ["foo.pdf", "-f", "-c", str(conffile)]
        with pytest.raises(SystemExit):
            pdfocr.get_options(opts)

    def test_filing_options(self, pdfocr, conffile):
        """Check for getting filing options from config file
        """
        conffile.write("""
            target_folder: target
            default_folder: default
            original_move_folder: original
            folder_targets: {}
            """)
        opts = ["foo.pdf", "-f", "-c", str(conffile)]
        options = pdfocr.get_options(opts)
        assert options.target_folder == 'target'
        assert options.default_folder == 'default'
        assert options.original_move_folder == 'original'
        assert options.watch_dir is None

    # def test_filing(self, pdfocr, conffile):
    #     """Filing option should enable filing"""
    #     opts = ["foo.pdf", "-f", "-c", conffile]
    #     pdfocr.get_options(opts)
    #     assert pdfocr.enable_filing is True
    #     assert pdfocr.config

    def test_watch_conflict(self, pdfocr):
        """When pdf file is specified, we don't want to allow watch option"""
        opts = ["blah.pdf", '-w']
        with pytest.raises(SystemExit):
            pdfocr.get_options(opts)

    def test_evernote(self, pdfocr, conffile, monkeypatch):
        """Enabling evernote should enable filing automatically"""
        monkeypatch.setattr('pypdfocr.pypdfocr.evernote_enabled', True)
        conffile.write("foobar: None")
        opts = ["foo.pdf", "--evernote", "-c", str(conffile)]
        options = pdfocr.get_options(opts)
        # assert pdfocr.enable_evernote is True
        assert options.enable_evernote is True
        # assert pdfocr.enable_filing is True
        assert options.enable_filing is True
        # assert pdfocr.watch is False
        assert options.watch_dir is None

    def test_evernote_disabled(self, pdfocr, conffile, monkeypatch):
        """If evernote is not enabled, filing should not enable itself."""
        monkeypatch.setattr('pypdfocr.pypdfocr.evernote_enabled', False)
        # opts = ["foo.pdf", "-e", "-c", conffile]
        opts = ["foo.pdf", "-e"]
        options = pdfocr.get_options(opts)
        # assert pdfocr.enable_evernote is False
        assert options.enable_evernote is False
        # assert pdfocr.enable_filing is False
        assert options.enable_filing is False

    def test_no_evernote_dir_filing(self, pdfocr, conffile, monkeypatch):
        """If evernote disabled, filing should not disable itself."""
        monkeypatch.setattr('pypdfocr.pypdfocr.evernote_enabled', False)
        # opts = ["foo.pdf", "-e", "-f", "-c", conffile]
        opts = ["foo.pdf", "-e", "-f"]
        options = pdfocr.get_options(opts)
        # assert pdfocr.enable_evernote is False
        assert options.enable_evernote is False
        # assert pdfocr.enable_filing is True
        assert options.enable_filing is True

    def test_get_default(self, pdfocr, conffile):
        conffile.write("")
        opts = ["foo.pdf", "-c", str(conffile)]
        config = pdfocr.get_options(opts)
        assert config.lang == 'eng'

    def test_set_config(self, pdfocr, conffile):
        conffile.write("""
            lang: "bar"
            debug: True
            """)
        opts = ["foo.pdf", "-c", str(conffile)]
        config = pdfocr.get_options(opts)
        assert config.debug is True
        assert config.lang == 'bar'

    def test_cmdline_override_config(self, pdfocr, conffile):
        conffile.write("""
            lang: "bar"
            debug: True
            """)
        opts = ["foo.pdf", "--lang", "foo", "-c", str(conffile)]
        config = pdfocr.get_options(opts)
        assert config.debug is True
        assert config.lang == "foo"

    def test_ghostscript_config(self, pdfocr, conffile):
        conffile.write("""
            ghostscript:
                binary: "/foo/bar/gs"
            """)
        opts = ["foo.pdf", "-c", str(conffile)]
        config = pdfocr.get_options(opts)
        assert config.ghostscript == {"binary": "/foo/bar/gs"}

    def test_ghostscript_default(self, pdfocr, conffile):
        conffile.write("")
        opts = ["foo.pdf", "-c", str(conffile)]
        config = pdfocr.get_options(opts)
        assert config.ghostscript == {}
