#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from docfly import Docfly
import os, shutil

package_name = "uszipcode"

try:
    shutil.rmtree(os.path.join("source", package_name))
except Exception as e:
    print(e)
     
docfly = Docfly(
    package_name, 
    dst="source",
    ignore=[
        "%s.zzz_manual_install.py" % package_name,
        "%s.packages" % package_name,
    ]
)
docfly.fly()