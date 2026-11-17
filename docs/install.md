# Preparing the environment and running from source

**Distribution method selected by the maintainer on 16 November 2026:** source code obtained from GitHub by cloning the repository or downloading the usage ZIP. Run the application from the project folder in a terminal or VS Code, using Python 3.13. Miniforge can provide the Python environment. Installing the PyFracPaQ package is unnecessary; installers, wheels and a wheelhouse are not user deliverables. The technical decision is recorded in docs/decisions/0019-source-distribution.md in the full repository.

Source version: **0.9.0rc1**, November 2026, contact luismauricio@me.com. MATLAB reference: FracPaQ 2.8. Development tests and reports remain in the full repository and are excluded from the usage ZIP. Their absence does not disable any analysis.

## Python and a virtual environment

Obtain the repository or extract the ZIP, then open the folder containing run_gui.py and requirements.txt. With Python 3.13 installed, run these commands from that folder:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python run_gui.py
# Alternative, from the same folder:
.venv/bin/python -m pyfracpaq
```

These commands target the verified macOS environment. Running the application requires neither installing the project with pip nor building a wheel. requirements.txt installs the pinned dependencies. Obtaining source code and dependencies may initially require a network connection; analyses run locally and offline once the environment is ready.

## VS Code and Miniforge

In VS Code, open the project folder, select the Python executable from the prepared environment, then launch run_gui.py or use the configurations in .vscode/launch.json. The interpreter is the executable inside the environment, rather than the .venv directory. VS Code uses that Python to run the code.

With Miniforge, create an environment using `conda create -n pyfracpaq python=3.13 pip`, activate it with `conda activate pyfracpaq`, open a terminal at the project root and run:

```bash
python -m pip install -r requirements.txt
python -m pip check
python run_gui.py
# Alternative:
python -m pyfracpaq
```

In VS Code, select the Python executable from that Miniforge environment. There is no need to create another .venv inside an environment that is already prepared. Documented validation identifies the versions and scenarios checked; it does not certify Windows/Linux.

CPython 3.13.18 in a virtual environment and Python 3.13.13 in a Miniforge environment have been checked on macOS arm64, installing only requirements.txt and running directly from source. The code requires Python >=3.13,<3.14. Windows/Linux remain for the maintainer's later testing, as instructed. MATLAB is not required to use the application.

## Development and references

To run tests and comparison tools, also install requirements-dev.txt. An editable project installation is optional for development, rather than a usage requirement. Specific reference tests require the fracpaq-matlab directory, kept separately and outside Git; it is unnecessary for running the application. A missing reference distribution does not mean the port's functionality is absent.

Reusing a tag replaces files with the same names; different tags coexist, except for intermediates with fixed names. Replacement is atomic per file, without a transaction covering the entire Run. SVG conversions are written alongside the SVG; other outputs use the working directory. Preserve original inputs and check Saved/Replaced messages.

The 0.1.0rc1 packages and 0.9.0rc1 artifacts in dist/ were produced before the GitHub source-distribution decision. They are internal technical evidence, rather than products to install or distribute. Their installation tests do not complete the redefined point 4. Reports from that work remain in docs/parity/ in the full repository. See the [user release notes](release-notes.md).

## Contents of the usage ZIP

Application code and resources in pyfracpaq/, run_gui.py, requirements.txt, examples, VS Code launch settings, manuals, notes and licences. Tests, evidence and internal scripts are excluded. The full clone retains development material for maintenance, but none is needed at runtime. Automatic test discovery in VS Code is disabled; developers may enable it after installing requirements-dev.txt.
