import os
import importlib


def list_py_files(folder_path):
    """Return a list of .py filenames (without extensions) in the given folder, excluding __init__.py."""
    with os.scandir(folder_path) as entries:
        return [
            entry.name[:-3]
            for entry in entries
            if entry.is_file()
            and entry.name.endswith(".py")
            and entry.name != "__init__.py"
        ]


def import_module(module_files, module_name):
    """
    Dynamically imports modules in pypricing package using both relative and absolute paths.

    Parameters
    ----------
    module_files : list of str
        List of module names to be imported.
    module_name : str
        String prefix for module.
    """

    for file in module_files:
        relative_import = "." + module_name + "." + file
        absolute_import = module_name + "." + file
        try:
            module = importlib.import_module(
                relative_import, "pypricing"
            )  # (Relative) import needed for the workspace.
            globals().update(
                {k: getattr(module, k) for k in dir(module) if not k.startswith("_")}
            )  # Update the current namespace
        except (ImportError, ModuleNotFoundError, ValueError):
            module = importlib.import_module(absolute_import)  # (Absolute) local import
            globals().update(
                {k: getattr(module, k) for k in dir(module) if not k.startswith("_")}
            )  # Update the current namespace


#  data
try:  # Local path
    folder = os.path.expanduser(r"~/ArfimaTools/pypricing/data")
    module_names = list_py_files(folder)
except FileNotFoundError:  # Workspace path
    folder = "/ArfimaTools/pypricing/data"
    module_names = list_py_files(folder)

import_module(module_names, "data")

#  pricing
try:  # Local path
    folder = os.path.expanduser(r"~/ArfimaTools/pypricing/pricing")
    module_names = list_py_files(folder)
except FileNotFoundError:  # Workspace path
    folder = "/ArfimaTools/pypricing/pricing"
module_names = list_py_files(folder)
import_module(module_names, "pricing")


#  risk
try:  # Local path
    folder = os.path.expanduser(r"~/ArfimaTools/pypricing/risk")
    module_names = list_py_files(folder)
except FileNotFoundError:  # Workspace path
    folder = "/ArfimaTools/pypricing/risk"
module_names = list_py_files(folder)
import_module(module_names, "risk")
