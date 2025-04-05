import subprocess


def run_flake8():
    try:
        result = subprocess.run(['flake8', '.'], capture_output=True, text=True, check=True)
        return ("Flake8 Output:\n", result.stdout)
    except subprocess.CalledProcessError as e:
        return ("Flake8 returned errors:\n", e.output)


run_flake8()
