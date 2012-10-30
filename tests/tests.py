import hashlib
from flask import Flask
from os import unlink
from os.path import isfile
from nose.tools import assert_equal, ok_
from flask_assetslite import Bundle, Filter


class TestBundle(object):

    test_css = [
        'tests/test01.css',
        'tests/test02.css',
    ]

    output = 'tests/test.%s.min.css'

    @classmethod
    def setUp(cls):
        """
        Set up.
        """
        cls.app = Flask(__name__)
        cls.bundle = Bundle(cls.test_css, output=cls.output)

    @classmethod
    def teardown(cls):
        """
        Teardown.
        """
        del cls.bundle

    def test_hash(self):
        """
        Combined files produce expected output filename.
        """
        assert_equal(self.bundle.output_filename, 'tests/test.7ca3f3a5.min.css')

    def test_dev(self):
        """
        Output URLs are correct in debug mode.
        """
        assert_equal(self.bundle.urls(debug=True), ['/tests/test01.css', '/tests/test02.css'])

    def test_prod(self):
        """
        Output URLs are correct when debug is off.
        """
        if isfile(self.bundle.output_filename):
            unlink(self.bundle.output_filename)

        # Bundle must first be built so an output file exists.
        self.bundle.build()

        # Clean up output file
        assert_equal(self.bundle.urls(debug=False), ['/tests/test.7ca3f3a5.min.css'])
        unlink(self.bundle.output_filename)

    def test_current_app(self):
        """
        Default configuration values are picked up from current Flask
        application context.
        """
        with self.app.app_context():
            assert_equal(self.bundle.static_folder, self.app.static_folder)
            assert_equal(self.bundle.static_url_path, self.app.static_url_path)

    def test_filter(self):
        """
        Running data through filter produces expected data hash.
        """
        # Our special filter
        rot13 = Filter(('tests/rot13', '--'))
        bundle = Bundle(['tests/test01.css', 'tests/test02.css'], filters=rot13)

        # Call bundle build, which returns a StringIO handle
        data = bundle.build()

        # Check md5 hash
        h = hashlib.md5()
        h.update(data.getvalue())

        assert_equal(h.hexdigest(), '6d4ab1ec47d4156b519b8ff510b51af3')

    def test_writeout(self):
        """
        Output files written to correct location regardless of current
        working directory.
        """
        # Remove any leftover file from previous test...
        if isfile('tests/_test.css'):
            unlink('tests/_test.css')
        # Even though working directory is the top-level, setting
        # static_folder should make all paths relative to './tests'.
        bundle = Bundle(['test01.css', 'test02.css'], output='_test.css', static_folder='tests')
        bundle.build()
        # Check file is in the right spot.
        ok_(isfile('tests/_test.css'))
        unlink('tests/_test.css')
