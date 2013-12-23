import pep8
import unittest
from glob import glob


class TestCodeFormat(unittest.TestCase):
    def test_pep8_conformance_core(self):
        files = glob('rgkit/*.py')

        pep8style = pep8.StyleGuide()
        result = pep8style.check_files(files)
        self.assertEqual(
            result.total_errors, 0, "Found code style errors (and warnings).")

    def test_pep8_conformance_tests(self):
        files = glob('test/*.py')

        pep8style = pep8.StyleGuide()
        pep8style.options.ignore += ('E501',)
        result = pep8style.check_files(files)
        self.assertEqual(
            result.total_errors, 0, "Found code style errors (and warnings).")
