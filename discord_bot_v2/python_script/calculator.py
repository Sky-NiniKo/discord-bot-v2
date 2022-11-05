import subprocess
import os

if __name__ == '__main__':
    from utils import exit_after
else:
    from .utils import exit_after


if os.environ.get("nix"):
    QALC_PATH = ["nix-shell", "-p", "qalc"]
else:
    QALC_PATH = [os.environ.get('QALC_PATH', "/usr/bin/qalc")]


@exit_after(10)
def calculate(*args, calculation: str) -> str:
    if calculation:
        p = subprocess.Popen([*QALC_PATH, calculation], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        p = subprocess.Popen([*QALC_PATH, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.stdout.read().decode().strip()


if __name__ == '__main__':
    import platform

    if platform.system() == "Windows":
        import os

        os.environ['PATH'] = r'../resource/cairo/Windows' + ';' + os.environ['PATH']
    # result_file = "../" + result_file
    print((calculate(calculation=input())))
