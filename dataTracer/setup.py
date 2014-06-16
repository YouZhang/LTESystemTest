#conding = utf-8
#author : You Zhang
from distutils.core import setup

import py2exe


options = {"py2exe":

    {"compressed": 1,
     "optimize": 2,
     "ascii": 1,
     "bundle_files": 1 }
    }
setup(
    options = options,
    zipfile=None,
    console=[{"script": "dataTrace.py", "icon_resources": [(0, "sbell.ico")] }]
    )