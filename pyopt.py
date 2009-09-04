"""
pyopts

A module for command-line options with a pythonic, decorator-centric syntax.

The following example auto-generates help with docstrings, type casting for
arguments and enforcing argument count:
>>>
>>> from pyopt import CmdFunction
>>> from pyopt import parse_cmds
>>>
>>> @CmdFunction
>>> def regular_function(arg1:str, arg2:int):
...    '''docstring'''
...    print(repr(arg1))
...
>>> parse_cmds()

NOTE: This module was specifically designed with python 3 in mind, certain features
can be converted to python 2.x, but the real neat ones can't.
"""

HELP_SET = {"-h", "--help", "/?", "?", "-?"}

FUNCTIONS_DICT = {}

def CmdFunction(function):
    FUNCTIONS_DICT[function.__name__] = function
    return function

def args_repr(func):
    args_list = func.__code__.co_varnames
    return ' '.join(["[%s]" % arg for arg in args_list])

def func_usage(func):
    return "\t%s %s\n%s" % (func.__name__, args_repr(func), indent(func.__doc__, 2))

def print_usage(script_name):
    print("Usage: %s [function_name] [args]" % script_name)
    print("Available functions are:")
    for func in FUNCTIONS_DICT.values():
        print(func_usage(func))

def indent(string, tab_count):
    lines = string.splitlines()
    lines = [("\t" * tab_count) + ln.strip() for ln in lines]
    return '\n'.join(lines)


def parse_cmds():
    import sys
    if (len(sys.argv) == 1) or (sys.argv[1] in HELP_SET):
        try:
            func_name = sys.argv[2]
            func = FUNCTIONS_DICT[func_name]
            print(func_usage(func))
        except Exception as e:
            from os.path import basename
            print_usage(basename(sys.argv[0]))
        return
    
    func_name = sys.argv[1]
    func = FUNCTIONS_DICT[func_name]
    args = sys.argv[2:]
    arg_names = func.__code__.co_varnames
    defaults_count = 0 if (func.__defaults__ is None) else len(func.__defaults__)
    needed_args = len(arg_names) - defaults_count
    if len(args) != needed_args:
        print("%s requires %d arguments, got %d." % (func_name, needed_args, len(args)))
        return
    
    args_to_call_with = []
    for i, var in enumerate(arg_names):
        type_to_cast = func.__annotations__[var]
        parsed_arg = type_to_cast(args[i])
        args_to_call_with.append(parsed_arg)
    
    func(*args_to_call_with)



