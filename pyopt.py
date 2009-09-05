"""
pyopt

A module for command-line options with a pythonic, decorator-centric syntax.

The following example auto-generates help with docstrings, type casting for
arguments and enforcing argument count:

    from pyopt import CmdPos
    from pyopt import parse_cmds

    @CmdPos
    def regular_function(arg1:str, arg2:int):
        '''docstring'''
        # bla, etc, foobar spam...
        print(repr(arg1), repr(arg2))

    if __name__ == "__main__":
        parse_cmds()

There are 2 modes of operation:
    1. CmdPos - A decorator for positional arguments.
    2. CmdKw - A decorator for keyword arguments.

Currently known compromises that are open to discussion, e-mail me:
    1. This module was specifically designed with python 3 in mind, certain features
        can be converted to python 2.x, but the awesome ones can't.
    2. Keyword command-line functions require every argument to start with a
        different letter to avoid collisions.
    3. Annotations are mandatory, I don't know if this is the right way to go,
        it's an explicity vs convenience issue.
    4. Booleans can't default to false. I couldn't think of a use case for this
        so tell me if you did.

License: whatever, I don't mind. Google Code made me choose so I went with
the "New BSD". If somebody has a better idea, e-mail, comment or whatnot.
Hearing from whoever uses this code would be nice, but you really shouldn't
feel obliged: ubershmekel at gmail.com
"""


import sys
from os.path import basename
import types

class PyoptError(Exception): pass

HELP_SET = {"-h", "--help", "/?", "?", "-?"}

POS_FUNCTIONS_DICT = {}
KW_FUNCTIONS_DICT = {}


# DBG
import pdb, sys, traceback
def info(type, value, tb):
    traceback.print_exception(type, value, tb)
    pdb.pm()
sys.excepthook = info
# DBG

def CmdPos(function):
    """
    A decorator that exposes the given function as a command-line function.
    Arguments will be passed by their order, without "switches" or options.
    """
    POS_FUNCTIONS_DICT[function.__name__] = function
    return function

def CmdKw(function):
    """
    A decorator that gives the getopt/optparse functionality and exposes
    the given function. Some notes:
    
    1. All arguments to the function are passed using hyphens and can be shortened.
    2. Arguments with default values will be optional arguments.
    3. Arguments marked as bool don't take a parameter (just "-d" as opposed to "-d something")
    """
    KW_FUNCTIONS_DICT[function.__name__] = function
    return function


def func_anal(func):
    """
    Gives all the needed information about a function and puts it in
    attributes on the function. ie:
    func.required == [list of required arguments]
    
    NOTE: set() calculations weren't used in order to preserve order
        for positional arguments.
    """
    if hasattr(func, 'booleans'):
        # we already analyzed this one
        return
    
    
    arg_names = func.__code__.co_varnames
    # __defaults__ should have been an empty list, come on Guido...
    defaults_count = 0 if (func.__defaults__ is None) else len(func.__defaults__)
    not_default_count = len(arg_names) - defaults_count
    not_defaulted = arg_names[:not_default_count]
    booleans = [arg for arg in arg_names if func.__annotations__[arg] is bool]
    required = [arg for arg in not_defaulted if arg not in booleans]
    
    # pass around the information
    func.arg_names = arg_names
    func.required = required
    func.optional = set(arg_names) - set(required)
    func.booleans = booleans
    func.defaults_count = defaults_count


def globalize_dict(dictionary):
    globals().update(dictionary)

def pos_args_repr(func):
    func_anal(func)
    req_str = ' '.join(["%s" % arg for arg in func.required])
    opt_str = ' '.join(["[%s]" % arg for arg in func.optional])
    
    return " ".join([req_str, opt_str])



def kw_args_repr(func):
    func_anal(func)
    req_str = ' '.join(["-%s %s" % (arg[0], arg) for arg in func.required])
    opt_str = ' '.join(["[-%s %s]" % (arg[0], arg) for arg in func.optional if arg not in func.booleans])
    bools_str = ' '.join(["[-%s]" % arg[0] for arg in func.booleans])
    
    return " ".join([req_str, opt_str, bools_str])


def pos_func_usage(func):
    return "\t%s %s\n%s" % (func.__name__, pos_args_repr(func), get_doc(func))

def kw_func_usage(func):
    return "\t%s %s\n%s" % (func.__name__, kw_args_repr(func), get_doc(func))

def get_doc(func):
    if func.__doc__ is None:
        return ""
    else:
        # strip for the docstring guys that don't want text on the same line with '''
        return indent(func.__doc__.strip(), 2)

def print_usage_single_func(script_name, func, is_kw):
    if is_kw:
        args_repr = kw_args_repr(func)
    else:
        args_repr = pos_args_repr(func)
    print("Usage: %s %s" % (script_name, args_repr))
    if func.__doc__ is not None:
        # strip for the docstring guys that don't want text on the same line with '''
        print(indent(func.__doc__.strip(), 1))
    
def indent(string, tab_count):
    lines = string.splitlines()
    lines = [("\t" * tab_count) + ln.strip() for ln in lines]
    return '\n'.join(lines)


def parse_kwargs(func, raw_args):
    short_name_name = [(name[0], name) for name in func.arg_names]
    short_to_name = dict(short_name_name)
    
    args_dict = {}
    
    # default all bools to false
    for name in func.booleans:
        args_dict[name] = False
    
    
    # parse the rest
    i = 0
    while i < len(raw_args):
        argument = raw_args[i]
        if argument.startswith("--"):
            name = argument[2:]
        elif argument.startswith("-"):
            if len(argument) == 2:
                name = short_to_name[argument[1]]
            elif len(argument) > 2:
                # many boolean options
                for short in argument[1:]:
                    name = short_to_name[short]
                    if name not in func.booleans:
                        raise PyoptError("Illegal option '%s' given as boolean." % short)
                    args_dict[name] = True
                i += 1
                continue
        else:
            raise PyoptError("Options must start with '-' or '--'.")
        
        if name not in func.__annotations__:
            raise PyoptError("Illegal option '%s' given." % name)
        
        val_type = func.__annotations__[name]
        if val_type == bool:
            val = True
        else:
            # if not a bool then the next arg is the value of this option
            val = val_type(raw_args[i + 1])
            i += 1
        
        args_dict[name] = val
        
        i += 1
    
    # make sure all non-boolean, non-defaulted args were given
    not_given = [arg for arg in func.required if arg not in args_dict]
    
    if len(not_given) > 0:
        raise PyoptError("The following options are required: %s." % ', '.join(not_given))
    
    return args_dict

def parse_posargs(func, args=[]):
    # NOTE: not len(required) because no need to mix with kw_parse boolean logic.
    needed_args = len(func.arg_names) - func.defaults_count
    if len(args) < needed_args:
        raise PyoptError("%d arguments required, got only %d." % (needed_args, len(args)))
    if len(args) > len(func.arg_names):
        raise PyoptError("Got %d arguments and expected at most %d." % (len(args), len(func.arg_names)))
    
    args_to_call_with = []
    for arg, arg_name in zip(args, func.arg_names):
        type_to_cast = func.__annotations__[arg_name]
        parsed_arg = type_to_cast(arg)
        args_to_call_with.append(parsed_arg)
    
    return args_to_call_with

def get_any_pair(*dictionaries):
    for d in dictionaries:
        if len(d) > 0:
            key = next(iter(d))
            return key, d[key]
    raise PyoptError("No functions were decorated.")

class CmdParser:
    def __init__(self, kw_funcs={}, pos_funcs={}):
        total_funcs = len(kw_funcs) + len(pos_funcs)
        self.kw_funcs = kw_funcs
        self.pos_funcs = pos_funcs
        
        if total_funcs == 0:
            raise NotImplementedError("No functions were decorated for command-line usage.")
        
        if total_funcs == 1:
            self.is_single = True
            if len(kw_funcs) == 1:
                self.func = next(iter(kw_funcs.values()))
                self.is_kw = True
            if len(pos_funcs) == 1:
                self.func = next(iter(pos_funcs.values()))
                self.is_kw = False
            func_anal(self.func)
        else:
            self.is_single = False
        

   
    def parse(self, cmd_args):
        self.cmd_args = cmd_args
        self.script_name = basename(cmd_args[0])
        if self.is_single:
            # if there is only one function, only get args
            self.args = cmd_args[1:]
        else:
            # the first arg should be the function name or help
            # Find out which function and what kind this is.
            #TODO#func_name = cmd_args[1]
            self.args = cmd_args[2:]
            if len(cmd_args) < 2:
                # not single so must be given a function name.
                return self.print_complete_usage()
            if cmd_args[1] in HELP_SET:
                return self.give_help()
            if cmd_args[1] in self.kw_funcs:
                self.is_kw = True
                self.func = self.kw_funcs[cmd_args[1]]
            else:
                self.is_kw = False
                self.func = self.pos_funcs[cmd_args[1]]
            func_anal(self.func)
        
        
        if (self.is_single) and (len(cmd_args) > 1):
            if cmd_args[1] in HELP_SET:
                return print_usage_single_func(basename(cmd_args[0]), self.func, self.is_kw)
        
        # call
        if self.is_kw:
            self.call_args = parse_kwargs(self.func, self.args)
            self.func(**self.call_args)
        else:
            self.call_args = parse_posargs(self.func, self.args)
            self.func(*self.call_args)
   
    def print_complete_usage(self):
        print("Usage: %s [function_name] [args]" % self.script_name)
        print("Available functions are:")
        for func in self.pos_funcs.values():
            print(pos_func_usage(func))
        for func in self.kw_funcs.values():
            print(kw_func_usage(func))

    
    def give_help(self):
        try:
            # give help to a specific func, if an index error occurs, give complete usage.
            func_name = self.cmd_args[2]
            if func_name in self.kw_funcs:
                self.func = self.kw_funcs[func_name]
                func_anal(self.func)
                print(kw_func_usage(self.func))
            else:
                # in case the function isn't found, a KeyError is thrown so
                # the complete usage will be printed.
                self.func = self.pos_funcs[func_name]
                func_anal(self.func)
                print(pos_func_usage(self.func))
        except (IndexError, KeyError) as e:
            # print usage for this script
            self.print_complete_usage()  

def parse_cmds():
    try:
        cp = CmdParser(KW_FUNCTIONS_DICT, POS_FUNCTIONS_DICT)
        cp.parse(sys.argv)
    except PyoptError as e:
        print(e, "Run with ? or -h for more help.")

