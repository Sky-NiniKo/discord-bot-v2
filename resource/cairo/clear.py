# clear all not useful file for cairosvg (you must restart until "Finish" is print

import os
os.environ['PATH'] = r"bin" + ';' + os.environ['PATH']

try:
    import cairosvg

    with open("exeption.txt", "r+") as file:
        exeption = file.read().split("\n")
    for file in os.listdir("bin"):
        if file not in exeption:
            os.replace(rf"bin/{file}", rf"not_useful/{file}")
            with open("move.txt", "a+") as move:
                move.write(file + "\n")
            exit()
    print("Finish")
except:
    with open("move.txt", "r") as move:
        module = move.read().split("\n")[-2]
    os.replace(rf"not_useful/{module}", rf"bin/{module}")
    with open("exeption.txt", "a+") as exeption:
        exeption.write(module + "\n")
