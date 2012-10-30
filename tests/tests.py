from flask import Flask
from nose.tools import assert_equal
from flask_assetslite import Bundle


class TestBundle(object):

    test_css = [
        'tests/test01.css',
        'tests/test02.css',
    ]

    output = 'test.%s.min.css'

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

    def test_combine(self):
        """
        Combined files produce expected output filename.
        """
        assert_equal(self.bundle.output_filename, 'test.7ca3f3a5.min.css')

    def test_dev(self):
        """
        Dev URLs are correct.
        """
        assert_equal(self.bundle.urls(debug=True), ['/tests/test01.css', '/tests/test02.css'])
