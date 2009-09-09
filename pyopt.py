"""
pyopt

A module for command-line options with a pythonic, decorator-centric syntax.

The following example auto-generates help with docstrings, type casting for
arguments and enforcing argument count:

    import pyopt

    expose = pyopt.Exposer()

    @expose.args
    def regular_function(arg1:str, arg2:int):
        '''docstring'''
        # bla, etc, foobar spam...
        print(repr(arg1), repr(arg2))

    if __name__ == "__main__":
        expose.run()

There are 2 modes of operation:
    1. expose.args - A decorator for positional arguments.
    2. expose.kwargs - A decorator for keyword arguments.

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
feel obliged.

Contact me at: ubershmekel at gmail
"""


import sys
from os.path import basename
import types
import getopt
import inspect

class PyoptError(Exception): pass
class PrintHelp(PyoptError): pass

HELP_SET = {"-h", "--help", "/?", "?", "-?"}


# DBG
#import pdb, sys, traceback
#def info(type, value, tb):
#    traceback.print_exception(type, value, tb)
#    pdb.pm()
#sys.excepthook = info
# DBG



def print_usage_single_func(script_name, func):
    args_repr = func.parameters_repr()
    print("Usage: %s %s" % (script_name, args_repr))
    if func.function.__doc__ is not None:
        # strip for the docstring guys that don't want text on the same line with '''
        print(indent(func.function.__doc__.strip(), 1))
    
def indent(string, tab_count):
    lines = string.splitlines()
    lines = [("\t" * tab_count) + ln.strip() for ln in lines]
    return '\n'.join(lines)




class FunctionWrapper:
    def __init__(self, function):
        """
        Gives all the needed information about a function and puts it in
        attributes on the function. ie:
        function.required == [list of required arguments]
        
        NOTE: set() calculations weren't used in order to preserve order
            for positional arguments.
        """
        
        args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations = inspect.getfullargspec(function)
        
        arg_names = args
        # __defaults__ should have been an empty list, come on Guido...
        defaults_count = 0 if (defaults is None) else len(defaults)
        not_default_count = len(arg_names) - defaults_count
        not_defaulted = arg_names[:not_default_count]
        casts = {name: function.__annotations__.get(name, str) for name in arg_names}
        booleans = [arg for arg in arg_names if casts[arg] is bool]
        required = [arg for arg in not_defaulted if arg not in booleans]
        
        # pass around the information
        self.function = function
        self.arg_names = arg_names
        self.name = function.__name__
        self.required = required
        self.optional = set(arg_names) - set(required)
        self.booleans = booleans
        self.defaults_count = defaults_count
        self.needed_args = len(self.arg_names) - self.defaults_count
        
        # get all the casts from the annotations, default to str
        self.casts = casts
        
    
    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)
    
    def get_doc(self):
        if self.function.__doc__ is None:
            return ""
        else:
            # strip for the docstring guys that don't want text on the same line with '''
            return indent(self.function.__doc__.strip(), 2)
    
    def get_usage(self):
        return "\t%s %s\n%s" % (self.name, self.parameters_repr(), self.get_doc())
    
    def parameters_repr(self):
        """
        This function should be implemented by subclasses to return a string
        that represents the parameters with which to call the function
        from a command line or shell.
        """
        raise NotImplementedError
        
    def parse(self, raw_args=[]):
        """
        raw_args - a list of arguments and options as would be given by sys.argv
        
        This function should be implemented by subclasses and must return
        a list and a dictionary, args and kwargs, that way it's easy to call
        the function.
        """
        raise NotImplementedError


class ArgsFunction(FunctionWrapper):
    def parameters_repr(self):
        req_str = ' '.join(["%s" % arg for arg in self.required])
        opt_str = ' '.join(["[%s]" % arg for arg in self.optional])
        
        return " ".join([req_str, opt_str])
    
    def parse(self, raw_args=[]):
        # NOTE: not len(required) because no need to mix with kw_parse boolean logic.
        
        if len(raw_args) < self.needed_args:
            raise PyoptError("%d arguments required, got only %d." % (self.needed_args, len(raw_args)))
        if len(raw_args) > len(self.arg_names):
            raise PyoptError("Got %d arguments and expected at most %d." % (len(raw_args), len(self.arg_names)))
        
        args_to_call_with = []
        for arg, arg_name in zip(raw_args, self.arg_names):
            type_to_cast = self.casts[arg_name]
            parsed_arg = type_to_cast(arg)
            args_to_call_with.append(parsed_arg)
        
        return args_to_call_with, {}

class MixedFunction(FunctionWrapper):
    def parameters_repr(self):
        # self.arg_names is the authorative order
        # todo: fix this
        req_str = ' '.join(["-%s %s" % (arg[0], arg) for arg in self.required])
        opt_str = ' '.join(["[-%s %s]" % (arg[0], arg) for arg in self.optional if arg not in self.booleans])
        bools_str = ' '.join(["[-%s]" % arg[0] for arg in self.booleans])
        
        return " ".join([req_str, opt_str, bools_str])

    def parse(self, raw_args=[]):
        short_to_name = {name[0]: name for name in self.arg_names}
        
        shorts_str = ''
        shorts_str += ''.join([[name][0] for name in self.booleans])
        shorts_str += ''.join(["%s:" % name[0] for name in self.required])
        long_opts = []
        long_opts += [name for name in self.booleans]
        long_opts += ["%s=" % name for name in self.required]
        
        optlist, uncasted_args_list = getopt.getopt(raw_args, shorts_str, long_opts)
        
        arg_names = list(self.arg_names)
        kwargs_dict = {}
        for opt, val in optlist:
            if opt.startswith('--'):
                name = opt[2:]
            elif opt.startswith('-'):
                short = opt[1]
                name = short_to_name[short]
            
            kwargs_dict[name] = self.casts[name](val)
            # remove all the arguments which came from switches, the remainder
            # will be used for positional arguments 
            arg_names.remove(name)
        
        args_list = []
        for name, val in zip(arg_names, uncasted_args_list):
            args_list.append(self.casts[name](val))
        
        return args_list, kwargs_dict

class KwargsFunction(FunctionWrapper):
    def parameters_repr(self):
        req_str = ' '.join(["-%s %s" % (arg[0], arg) for arg in self.required])
        opt_str = ' '.join(["[-%s %s]" % (arg[0], arg) for arg in self.optional if arg not in self.booleans])
        bools_str = ' '.join(["[-%s]" % arg[0] for arg in self.booleans])
        
        return " ".join([req_str, opt_str, bools_str])

    def parse(self, raw_args=[]):
        short_to_name = {name[0]: name for name in self.arg_names}
        
        # where all the parsed arguments will be stored {name:value}
        args_dict = {}
        
        # default all bools to false
        for name in self.booleans:
            args_dict[name] = False
        
        
        # parse the rest
        i = 0
        while i < len(raw_args):
            argument = raw_args[i]
            # find out the name of the argument
            if argument.startswith("--"):
                name = argument[2:]
            elif argument.startswith("-"):
                if len(argument) == 2:
                    name = short_to_name[argument[1]]
                elif len(argument) > 2:
                    # many boolean options
                    for short in argument[1:]:
                        name = short_to_name[short]
                        if name not in self.booleans:
                            raise PyoptError("Illegal option '%s' given as boolean." % short)
                        args_dict[name] = True
                    i += 1
                    continue
            else:
                raise PyoptError("Options must start with '-' or '--'.")
            
            if name not in self.arg_names:
                raise PyoptError("Illegal option '%s' given." % name)
            
            val_type = self.casts[name]
            if val_type == bool:
                val = True
            else:
                # if not a bool then the next arg is the value of this option
                val = val_type(raw_args[i + 1])
                i += 1
            
            args_dict[name] = val
            
            i += 1
        
        # make sure all non-boolean, non-defaulted args were given
        not_given = [arg for arg in self.required if arg not in args_dict]
        
        if len(not_given) > 0:
            raise PyoptError("The following options are required: %s." % ', '.join(not_given))
        
        return [], args_dict

class Exposer:
    def __init__(self, kw_funcs_list=[], pos_funcs_list=[], mixed_funcs_list=[]):
        """
        Instead of decorators, you can pass functions to expose as a list.
        """
        self.functions_dict = {}
        
        for function in kw_funcs_list:
            self.kwargs(function)
        for function in pos_funcs_list:
            self.args(function)
        for function in mixed_funcs_list:
            self.mixed(function)
        
    
    def args(self, function):
        """
        A decorator that exposes the given function as a command-line function.
        Arguments will be passed by their order, without "switches" or options.
        """
        self.functions_dict[function.__name__] = ArgsFunction(function)
        return function
    
    def kwargs(self, function):
        """
        A decorator that gives the getopt/optparse functionality and exposes
        the given function. Some notes:
        
        1. All arguments to the function are passed using hyphens and can be shortened.
        2. Arguments with default values will be optional arguments.
        3. Arguments marked as bool don't take a parameter (just "-d" as opposed to "-d something")
        """
        self.functions_dict[function.__name__] = KwargsFunction(function)
        return function
    
    def mixed(self, function):
        """
        A decorator that gives the getopt/optparse functionality and exposes
        the given function. Some notes:
        
        1. The first arguments to the function are passed using ie: -f or --fullname.
        2. Arguments with default values will be optional arguments.
        3. Arguments marked as bool don't take a parameter (just "-d" as opposed to "-d something")
        4. The first argument without a hyphen is the first positional argument.
            from then on, no more options, just positional args.
        """
        self.functions_dict[function.__name__] =  MixedFunction(function)
        return function
    
    def parse_args(self, cmd_args):
        self.cmd_args = cmd_args
        self.script_name = basename(cmd_args[0])
        total_funcs = len(self.functions_dict)
        
        if total_funcs == 0:
            raise NotImplementedError("No functions were decorated for command-line usage.")
        
        if total_funcs == 1:
            self.is_single = True
            self.func = next(iter(self.functions_dict.values()))
        else:
            self.is_single = False
    
        if self.is_single:
            # if there is only one function, only get args
            self.raw_args = cmd_args[1:]
        else:
            # Multiple functions decorated :)
            # the first arg must be either the function name or help.
            # Find out which function this is.
            self.raw_args = cmd_args[2:]
            if len(cmd_args) < 2:
                # not single so must be given a function name.
                raise PrintHelp(self.print_complete_usage())
            if cmd_args[1] in HELP_SET:
                raise PrintHelp(self.give_help())
            
            if cmd_args[1] in self.functions_dict:
                func_name = cmd_args[1]
                self.func = self.functions_dict[func_name]
            else:
                raise PyoptError("Unkown function '%s'." % cmd_args[1])
        
        
        if (self.is_single) and (len(cmd_args) > 1):
            if cmd_args[1] in HELP_SET:
                raise PrintHelp(print_usage_single_func(basename(cmd_args[0]), self.func))
        
        args, kwargs = self.func.parse(self.raw_args)
        return self.func, args, kwargs
        
    def run(self, cmd_args=sys.argv):
        try:
            func, args, kwargs = self.parse_args(cmd_args)
            func(*args, **kwargs)
        except PrintHelp as e:
            print(e)
        except ValueError as e:
            print("%s. Run with ? or -h for more help." % e)
        except PyoptError as e:
            print(e, "Run with ? or -h for more help.")
    
    
    def print_complete_usage(self):
        print("Usage: %s [function_name] [args]" % self.script_name)
        print("Available functions are:")
        for func in self.functions_dict.values():
            print(func.get_usage())
    
    
    def give_help(self):
        try:
            # give help to a specific func, if an index error occurs, give complete usage.
            func_name = self.cmd_args[2]
            if func_name in self.functions_dict:
                # in case the function isn't found, a KeyError is thrown so
                # the complete usage will be printed.
                self.func = self.functions_dict[func_name]
                raise PrintHelp(self.func.get_usage())
                # todo: erase this comment
                #kw_func_usage(self.func))
        except (IndexError, KeyError) as e:
            # print usage for this script
            self.print_complete_usage()  


