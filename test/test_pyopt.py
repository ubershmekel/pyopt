"""
tests for pyopt
"""

import unittest

import pyopt

if str != bytes:
    # py3k
    from test_pyopt_annotations import *

class TestSingleParsers(unittest.TestCase):
    def test_annotations_not_mandatory(self):
        expose = pyopt.Exposer()

        @expose.args
        def robin(archer, boulder, magic=42):
            pass        
        func, args, kwargs = expose.parse_args("a.py a 1.0")
        self.assertEqual(func, robin)
        self.assertEqual(args, ['a', '1.0'])
        self.assertEqual(kwargs, {})
    
    def test_default_cast(self):
        expose = pyopt.Exposer(default_cast=int)

        @expose.args
        def robin(archer, boulder, magic=42):
            pass        
        func, args, kwargs = expose.parse_args("a.py 2 3")
        self.assertEqual(func, robin)
        self.assertEqual(args, [2, 3])
        self.assertEqual(kwargs, {})
    
class TestOtherStuff(unittest.TestCase):
    def test_help_args(self):
        expose = pyopt.Exposer()
        @expose.args
        def robin(data, whatever):
            '''
            This method steals from the rich and gives to the poor

            data - the input
            whatever - anything at all.
            '''
            pass

        expose._setup("a.py")
        help_str = expose._single_usage()
        expected_help_str = 'Usage: a.py data whatever\n' \
            'This method steals from the rich and gives to the poor\n' \
            '\tdata - the input\n' \
            '\twhatever - anything at all.'
        
        self.assertEqual(help_str, expected_help_str)

    def test_help_kwargs(self):
        expose = pyopt.Exposer()
        @expose.kwargs
        def robin(data, whatever):
            '''
            This method steals from the rich and gives to the poor

            data - the input
            whatever - anything at all.
            '''
            pass

        expose._setup("a.py")
        help_str = expose._single_usage()
        expected_help_str = 'Usage: a.py -d data -w whatever\n' \
            'This method steals from the rich and gives to the poor\n' \
            '\t-d --data - the input\n' \
            '\t-w --whatever - anything at all.'
        
        self.assertEqual(help_str, expected_help_str)

    def test_help_mixed(self):
        expose = pyopt.Exposer()
        @expose.mixed
        def robin(data, whatever):
            '''
            This method steals from the rich and gives to the poor

            data - the input
            whatever - anything at all.
            '''
            pass

        expose._setup("a.py")
        help_str = expose._single_usage()
        expected_help_str = 'Usage: a.py -d data -w whatever\n' \
            'This method steals from the rich and gives to the poor\n' \
            '\t-d --data - the input\n' \
            '\t-w --whatever - anything at all.'
        
        self.assertEqual(help_str, expected_help_str)

if __name__ == '__main__':
    unittest.main()



