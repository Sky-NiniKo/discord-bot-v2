import math
import re
from decimal import Decimal
from fractions import Fraction

from python_script.utils import exit_after

safe_list = [func for func in dir(math) if not func.startswith('__')]

# use the list to filter the local namespace
safe_dict = {}
for k in safe_list:
    safe_dict[k] = eval(f"locals().get('math').{k}")


def irange(number):
    number = int(number)
    return range(number)


# add any needed builtins back in.
safe_dict['abs'] = abs
safe_dict['range'] = irange
safe_dict['Fraction'] = Fraction


def drange(x, y, jump):
    x, y, jump = Decimal(x), Decimal(y), Decimal(jump)
    while x <= y:
        yield round(float(x), 15)
        x += jump


def evaluate(string: str, additional_dict=None):
    if additional_dict is None:
        additional_dict = safe_dict
    numbers = re.findall("[0-9.j^]+", string)
    for number in numbers:
        try:
            float(number)
        except ValueError:
            numbers.remove(number)
    for number in numbers:
        string = string.replace(number, "PuT@Number", 1)
    for number in numbers:
        string = string.replace("PuT@Number", f"Fraction({number})", 1)
    ret = eval(string, {"__builtins__": None}, additional_dict)
    if isinstance(ret, Fraction):
        if ret.denominator == 1:
            return int(ret)
        elif float(ret) == ret:
            return float(ret)
        else:
            return ret
    return ret


@exit_after(0.3)
def calculate(calculation, raw=False, always_plot=False):
    if ";" not in calculation or raw:
        return evaluate(calculation)
    calculation = calculation.split(";")
    start, value, stop = calculation[1].split("<")[0:3]
    if ',' in stop:
        stop, step = stop.split(",")[0:2]
    else:
        step = "1"
    start, stop, step = evaluate(start), evaluate(stop), evaluate(step)
    if abs((stop - start) / step) <= 30 or always_plot:
        return "\n".join(
            f"{value}={x}; " + str(evaluate(calculation[0], {**safe_dict, value: x}))
            for x in drange(start, stop, step)
        )
    import matplotlib.pyplot
    result = [evaluate(calculation[0], {**safe_dict, value: x}) for x in drange(start, stop, step)]
    figure, _ = matplotlib.pyplot.subplots()
    matplotlib.pyplot.plot(list(drange(start, stop, step)), result, color='green', marker='o', linewidth=2, markersize=5)
    figure.savefig("resource/temp/plot.png")
    return True


if __name__ == '__main__':
    import platform
    if platform.system() == "Windows":
        import os
        os.environ['PATH'] = r'../resource/cairo/Windows' + ';' + os.environ['PATH']
    print((calculate(input())))
