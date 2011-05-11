"""
tests for pyopt
"""

import unittest

import pyopt

class TestSingleParsers(unittest.TestCase):
    def test_single_arg_function(self):
        expose = pyopt.Exposer()

        @expose.args
        def robin(archer:str, boulder:float, magic:int=42):
            """Shows an example positional command-line function.
                archer - is a str
                boulder - should be a float
                magic - a number that is magical"""
            print(repr(archer), repr(boulder), repr(magic))
        
        func, args, kwargs = expose.parse_args("a.py a 1.0")
        self.assertEqual(func, robin)
        self.assertEqual(args, ['a', 1.0])
        self.assertEqual(kwargs, {})
        self.assertRaises(pyopt.PrintHelp, expose.parse_args, "a.py -h")
        self.assertRaises(pyopt.PyoptError, expose.parse_args, "a.py 1 2 3 4")
        
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
    
    def test_single_mixed_function(self):
        expose = pyopt.Exposer()
        @expose.mixed
        def roll_dice(number_of_faces:int, repetitions:int):
            """
            Roll the dice to see if you're lucky or for general D&D pleasure.
            -n --number_of_faces - the max value of the die.
            -r --repititions - the amount of times to throw the dice.
            """
            pass

        func, args, kwargs = expose.parse_args("dice.py 6 2")
        self.assertEqual(roll_dice, func)
        self.assertEqual(args, [6, 2])
        self.assertEqual(kwargs, {})

        func, args, kwargs = expose.parse_args("dice.py -r 2 6")
        self.assertEqual(args, [6])
        self.assertEqual(kwargs, {"repetitions":2})
        
        self.assertRaises(pyopt.PyoptError, expose.parse_args, "dice.py 6 asdf")

    def test_single_kwargs_function(self):
        expose = pyopt.Exposer()
        @expose.kwargs
        def bigfun(brightness:int, nudge:bool, happy:bool, shaft:str='gold'):
            '''QWERTY'''
            pass
            
        func, args, kwargs = expose.parse_args("bf.py -b 13")
        self.assertEqual(bigfun, func)
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"nudge": False, "happy": False, "brightness": 13})

        equivalent_lines = "-b 5", "", ""
        func, args, kwargs = expose.parse_args("bf.py --brightness 5")
        self.assertEqual(bigfun, func)
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"nudge": False, "happy": False, "brightness": 5})

        self.assertRaises(pyopt.PyoptError, expose.parse_args, "dice.py --bright 5")
        
        # multiple bools in one switch
        func, args, kwargs = expose.parse_args("bigfun -nh -s dirt -b 120")
        self.assertEqual(bigfun, func)
        self.assertEqual(args, [])
        # note that "shaft" only appears in kwargs if it's changed.
        self.assertEqual(kwargs, {"nudge": True, "happy": True, "brightness": 120, "shaft": "dirt"})

class TestOtherStuff(unittest.TestCase):
    def test_multiple_parsers(self):
        expose = pyopt.Exposer()
        @expose.kwargs
        def bigfun(brightness:int, nudge:bool, happy:bool, shaft:str='gold'):
            pass
        @expose.mixed
        def roll_dice(number_of_faces:int, repetitions:int):
            pass
        @expose.args
        def robin(archer:str, boulder:float, magic:int=42):
            pass

        func, args, kwargs = expose.parse_args("a.py bigfun -nh -s dirt -b 120")
        self.assertEqual(bigfun, func)
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"nudge": True, "happy": True, "brightness": 120, "shaft": "dirt"})
        
        func, args, kwargs = expose.parse_args("a.py robin a 1.0")
        self.assertEqual(func, robin)
        self.assertEqual(args, ['a', 1.0])
        self.assertEqual(kwargs, {})

        func, args, kwargs = expose.parse_args("x.py roll_dice 6 2")
        self.assertEqual(roll_dice, func)
        self.assertEqual(args, [6, 2])
        self.assertEqual(kwargs, {})

    def test_custom_types(self):
        expose = pyopt.Exposer()
        def high_type(text):
            return text.upper()
        
        @expose.args
        def robin(data:high_type):
            return data

        func, args, kwargs = expose.parse_args("a.py asdf")
        self.assertEqual(robin, func)
        self.assertEqual(args, ['ASDF'])
        self.assertEqual(kwargs, {})
        
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



