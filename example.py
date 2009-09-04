
from pyopt import CmdFunction
from pyopt import parse_cmds

@CmdFunction
def ExampleFunc(a:str, b:float, magic:int):
    """Shows an example
        a - is a str
        b - should be a float
        magic - a number that is magical"""
    print(repr(a), repr(b), repr(magic))

@CmdFunction
def eg_func():
    """One liner..."""
    print("What's the speed velocity of an unladen swallow?")



if __name__ == "__main__":
    parse_cmds()

