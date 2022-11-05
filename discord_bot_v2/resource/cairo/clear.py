# clear all not useful file for cairosvg (you must restart until "Finish" is print)

import os
os.environ['PATH'] = r"Windows" + ';' + os.environ['PATH']

try:
    import cairosvg

    with open("exception.txt", "r+") as file:
        exception = file.read().split("\n")
    for file in os.listdir("Windows"):
        if file not in exception:
            os.replace(rf"Windows/{file}", rf"not_useful/{file}")
            with open("move.txt", "a+") as move:
                move.write(file + "\n")
            exit()
    print("Finish")
except OSError:
    with open("move.txt", "r") as move:
        module = move.read().split("\n")[-2]
    os.replace(rf"not_useful/{module}", rf"Windows/{module}")
    with open("exception.txt", "a+") as exception:
        exception.write(module + "\n")
