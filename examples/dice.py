
import random
import pyopt

expose = pyopt.Exposer()

@expose.args
def roll_dice(number_of_faces:int, repetitions:int):
    """
    Roll the dice to see if you're lucky or for general D&D pleasure.
    -n --number_of_faces - the max value of the die.
    -r --repititions - the amount of times to throw the dice.
    """
    for i in range(repetitions):
        print(random.randint(1, number_of_faces))


expose.run()