"""
An example module that uses pyopt.

Take note of the current restrictions (might change in the future):
    * Annotations are mandatory, add the type of the argument to EVERY argument.
    * Keyword command-line functions require every argument to start with a
        different letter to avoid collisions.
"""


import pyopt

expose = pyopt.Exposer()

@expose.args
def possy(archer:str, boulder:float, magic:int=42):
    """Shows an example positional command-line function.
        archer - is a str
        boulder - should be a float
        magic - a number that is magical"""
    print(repr(archer), repr(boulder), repr(magic))



@expose.kwargs
def bigfun(brightness:int, nudge:bool, happy:bool, shaft:str='gold'):
    """
    bigfun is a keyword command-line function.
    Switches can be given in any order.
    Also, booleans can be combined ie: -nh
    -b --brightness - how bright is it outside on a scale of 1-10
    -n --nudge - are you nudging me?
    -h --happy - script should be happy.
    -s --shaft - what kind of shaft are you?
    """
    if brightness < 10:
        print("Always look on the bright side of life.")
    
    print("You are a shaft of %s when all around is dark." % shaft)
    
    if nudge:
        print("Wink ;)")
    
    if not happy:
        print("Let's bicker and argue over who killed who.")


import random

@expose.mixed
def roll_dice(number_of_faces:int, repetitions:int):
    """
    Roll the dice to see if you're lucky or for general D&D pleasure.
    -n --number_of_faces - the max value of the die.
    -r --repititions - the amount of times to throw the dice.
    """
    for i in range(repetitions):
        print(random.randint(1, number_of_faces))

if __name__ == "__main__":
    # Now just run whichever functions you exposed, the return value is whatever
    # your function returned.
    expose.run()
    
    # usage for just simplifying optparse:
    #func, args, kwargs = expose.parse_args()

