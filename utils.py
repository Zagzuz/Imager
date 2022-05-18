import os

def envar(varname: str):
    return os.environ.get(varname, None)

