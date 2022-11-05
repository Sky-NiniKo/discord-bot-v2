import subprocess
import os
from pathlib import Path

import lui_calculator

if __name__ == '__main__':
    from utils import exit_after
else:
    from .utils import exit_after


QALC_PATH = [os.environ.get('QALC_PATH', "/usr/bin/qalc")]


@exit_after(10)
def calculate(*args, calculation: str, output: str | Path = "output.png") -> str:
    try:
        if calculation:
            p = subprocess.Popen([QALC_PATH, calculation], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            p = subprocess.Popen([QALC_PATH, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return p.stdout.read().decode().strip()
    except FileNotFoundError:
        return lui_calculator.calc(calculation, latex=None, output=output)


if __name__ == '__main__':
    import platform

    if platform.system() == "Windows":
        import os

        os.environ['PATH'] = r'../resource/cairo/Windows' + ';' + os.environ['PATH']
    # result_file = "../" + result_file
    print((calculate(calculation=input())))
