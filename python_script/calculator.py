import math
import time
import decimal

safe_list = [func for func in dir(math) if not func.startswith('__')]

# use the list to filter the local namespace
safe_dict = {}
for k in safe_list:
    safe_dict[k] = eval(f"locals().get('math').{k}")

# add any needed builtins back in.
safe_dict['abs'] = abs


def drange(x, y, jump):
    x, y, jump = decimal.Decimal(x), decimal.Decimal(y), decimal.Decimal(jump)
    while x <= y:
        yield float(x)
        x += jump


def calculate(calculation):
    if ";" not in calculation:
        return eval(calculation, {"__builtins__": None}, safe_dict)
    calculation = calculation.split(";")
    start, value, stop = calculation[1].split("<")[0:3]
    if ',' in stop:
        stop, step = stop.split(",")[0:2]
    else:
        step = "1"
    start, stop, step = float(calculate(start)), float(calculate(stop)), float(calculate(step))
    if abs((stop - start) / step) <= 20:
        return "\n".join(
            f"{value}={x}; " + str(eval(calculation[0], {"__builtins__": None}, {**safe_dict, value: x}))
            for x in drange(start, stop, step)
        )
    import matplotlib.pyplot
    timer = time.time()
    result = []
    for x in drange(start, stop, step):
        result += [eval(calculation[0], {"__builtins__": None}, {**safe_dict, value: x})]
        if time.time() - timer > 0.2:
            raise TimeoutError("Too many calculation")
    figure, _ = matplotlib.pyplot.subplots()
    matplotlib.pyplot.plot(result, color='green', marker='o', linewidth=2, markersize=5)
    figure.savefig("resource/temp/plot.png")
    return True


if __name__ == '__main__':
    print((calculate(input())))
