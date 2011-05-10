"""
An example module that uses pyopt.

Take note of the current restrictions (might change in the future):
    * Annotations are mandatory, add the type of the argument to EVERY argument.
    * Keyword command-line functions require every argument to start with a
        different letter to avoid collisions.
"""


import pyopt
import random

expose = pyopt.Exposer()



@expose.mixed
def roll_dice(number_of_faces:int, repetitions:int):
    """
    Roll the dice to see if you're lucky or for general D&D pleasure.
    -n --number_of_faces - the max value of the die.
    -r --repititions - the amount of times to throw the dice.
    """
    results = (random.randint(1, number_of_faces) for i in range(repetitions))
    for res in results:
        print(res, end=' ')

if __name__ == "__main__":
    # Now just run whichever functions you exposed, the return value is whatever
    # your function returned.
    expose.run()
    
    # usage for just simplifying optparse:
    #func, options, args = expose.parse_args()

