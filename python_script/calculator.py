import math
from math import *

try:
    cos(1)
except NameError:
    print("Math library not work as intended")

# make a list of safe functions
safe_list = [func for func in dir(math) if not func.startswith('__')]

# use the list to filter the local namespace
safe_dict = {}
for k in safe_list:
    safe_dict[k] = locals().get(k)

# add any needed builtins back in.
safe_dict['abs'] = abs


def calculate(calculation):
    return eval(calculation, {"__builtins__": None}, safe_dict)


if __name__ == '__main__':
    print((calculate(input())))