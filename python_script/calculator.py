from decimal import Decimal

import requests
from sympy import sympify, symbols, plot, pretty, SympifyError, latex, solveset, Eq, simplify, zoo
from sympy.plotting import plot3d

from python_script.utils import exit_after


result_file = "resource/temp/result.png"


def latex_need(c):
    if c == zoo:
        return True
    try:
        sympify(pretty(c))
        return False
    except SympifyError:
        return True


def drange(x, y, jump):
    x, jump = Decimal(x), Decimal(jump)
    while x <= y:
        yield round(float(x), 15)
        x += jump


def graph(calculation, **kwargs):
    result = plot(sympify(calculation), show=False, **kwargs)
    result.save(result_file)


def graph3d(calculation, **kwargs):
    result = plot3d(sympify(calculation), show=False, **kwargs)
    result.save(result_file)


def raw_calculate(calculation, return_str=False, return_approx=False):
    ret = sympify(calculation, evaluate=False)
    if return_approx:
        approximation = ret.evalf()
    else:
        try:  # si Rationnel enlever la multiplication
            approximation = ret.evalf() if (simplify(ret) == ret or ret.evalf() != ret) else None
        except AttributeError:
            approximation = None
    ret = simplify(ret)
    if latex_need(ret) and not return_str:
        latex_str = latex(ret) if approximation is None else latex(ret) + r"\approx" + str(approximation)
        with open(result_file, "wb") as file:
            file.write(requests.get(f"https://latex.codecogs.com/png.download?{latex_str}").content)
        return True
    return pretty(ret) if approximation is None else pretty(ret) + " ≈ " + str(approximation)


@exit_after(10)
def calculate(calculation: str, raw=False, plot_2d=False, plot_3d=False, equation_solve=False, return_str=False, return_approx=False):
    if not raw:  # regarde si il n'y a pas un argument
        if calculation.startswith("solve"):
            equation_solve = True
            calculation = calculation[6:]
        elif calculation.startswith("graph3d"):
            plot_3d = True
            calculation = calculation[8:]
        elif calculation.startswith("graph"):
            plot_2d = True
            calculation = calculation[6:]
        elif calculation.startswith("appr"):
            return_approx = True
            calculation = calculation[6:]
        else:
            raw = True
    if ";" not in calculation:
        if raw or return_approx:
            return raw_calculate(calculation, return_str, return_approx)
        if plot_2d:
            graph(calculation)
            return True
        if plot_3d:
            graph3d(calculation)
            return True
        if equation_solve:
            right, left = map(sympify, calculation.split("=")[0:2])
            solution = solveset(Eq(right, left))
            if latex_need(solution) and not return_str:
                with open(result_file, "wb") as file:
                    file.write(requests.get(f"https://latex.codecogs.com/png.download?{latex(solution)}").content)
                return True
            return pretty(solution)
    calculation = calculation.split(";")
    start, value, stop = calculation[1].split("<")[0:3]
    if ',' in stop:
        stop, step = stop.split(",")[0:2]
    else:
        step = "1"
    start, stop, step = float(sympify(start)), float(sympify(stop)), float(sympify(step))
    if plot_2d:
        graph(calculation[0], xlim=(start, stop))
        return True
    if abs((stop - start) / step) <= 30:
        return "\n".join(
            f"{value}={x}; " + str(float(sympify(calculation[0]).subs(symbols(value), x)))
            for x in drange(start, stop, step)
        )
    raise NotImplementedError


if __name__ == '__main__':
    import platform

    if platform.system() == "Windows":
        import os

        os.environ['PATH'] = r'../resource/cairo/Windows' + ';' + os.environ['PATH']
    result_file = "../" + result_file
    print((calculate(input())))
