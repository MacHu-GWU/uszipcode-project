#!/usr/bin/env python
# -*- coding: utf-8 -*-

import docfly

# Uncomment this if you follow Sanhe's Sphinx Doc Style Guide
#--- Manually Made Doc ---
# doc = docfly.DocTree("source")
# doc.fly(table_of_content_header="Table of Content (目录)")

#--- Api Reference Doc ---
package_name = "uszipcode"

doc = docfly.ApiReferenceDoc(
    package_name,
    dst="source",
    ignore=[
        "%s.packages" % package_name,
        "%s.zzz_manual_install.py" % package_name,
    ]
)
doc.fly()