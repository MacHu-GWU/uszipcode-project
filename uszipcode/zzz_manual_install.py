#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Install your own package in one seconds! (Windows System Only!)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Put this script in your package directory, for example::

    |---mypackage
        |---subpackage1
            |---__init__.py
        |---subpackage2
            |---__init__.py
        |---__init__.py
        |---module1.py
        |---module2.py
        |---zzz_manual_install.py <=== put it here
        
Run this script as the main script. Then your package is automatically installed 
and replace the old one for all Python versions on your ``WINDOWS`` computer.

This feature is extremely useful when you need refresh your package over and 
over again. But if you want to make an official release, you should make a 
setup.py and build the distribution by yourself. Read the following instruction:
    
- For Python2:

    - https://docs.python.org/2/distutils/setupscript.html
    - https://docs.python.org/2/distutils/builtdist.html

- For Python3:

    - https://docs.python.org/3.3/distutils/setupscript.html
    - https://docs.python.org/3.3/distutils/builtdist.html

**Warning**: with python2, the project directory cannot have non-ascil char.

-------------------------------------------------------------------------------

**中文文档**

本脚用于在Windows系统下傻瓜一键安装用户自己写的扩展包, 纯python实现。

例如你有一个扩展包叫 mypackage, 文件目录形如: ``C:\project\mypackage``

则只需要把该脚本拷贝到 mypackage 目录下:
``C:\project\mypackage\zzz_manual_install.py``

然后将本脚本以主脚本运行。则会把package文件中所有的 .pyc 文件清除后, 安装你所有
已安装的Python版本下。例如你安装了Python27和Python33, 那么就会创建以下目录并将
包里的所有文件拷贝到该目录下::

    C:\Python27\Lib\site-packages\mypackage
    C:\Python33\Lib\site-packages\mypackage
    
然后你就可以用 ``import mypackage`` 调用你写的库了。

这一功能在调试阶段非常方便, 但最终发布时还是要通过写 ``setup.py`` 文件来制作
package的安装包。这一部分可以参考:

- Python2:

    - https://docs.python.org/2/distutils/setupscript.html
    - https://docs.python.org/2/distutils/builtdist.html

- Python3:

    - https://docs.python.org/3.3/distutils/setupscript.html
    - https://docs.python.org/3.3/distutils/builtdist.html

注: 项目目录在python2中不允许有中文路径。

About
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Copyright (c) 2015 by Sanhe Hu**

- Author: Sanhe Hu
- Email: husanhe@gmail.com
- Lisence: MIT


**Compatibility**

- Python2: Yes
- Python3: Yes
    

**Prerequisites**

- None

class, method, func, exception
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

from __future__ import print_function, unicode_literals

def install():
    """Install your package to all Python version you have installed on Windows.
    """
    import os, shutil
    
    _ROOT = os.getcwd()
    _PACKAGE_NAME = os.path.basename(_ROOT)
    
    print("Installing [%s] to all python version..." % _PACKAGE_NAME)
    # find all Python release installed on this windows computer
    installed_python_version = list()
    for root, folder_list, _ in os.walk(r"C:\\"):
        for folder in folder_list:
            if folder.startswith("Python"):
                if os.path.exists(os.path.join(root, folder, "pythonw.exe")):
                    installed_python_version.append(folder)
        break
    print("\tYou have installed: {0}".format(", ".join(installed_python_version)))
    
    # remove __pycache__ folder and *.pyc file
    print("\tRemoving *.pyc file ...")
    pyc_folder_list = list()
    for root, folder_list, _ in os.walk(_ROOT):
        if os.path.basename(root) == "__pycache__":
            pyc_folder_list.append(root)
    
    for folder in pyc_folder_list:
        shutil.rmtree(folder)
    print("\t\tall *.pyc file has been removed.")
    
    # install this package to all python version
    for py_root in installed_python_version:
        dst = os.path.join(r"C:\\", py_root, r"Lib\site-packages", _PACKAGE_NAME)
        try:
            shutil.rmtree(dst)
        except:
            pass
        print("\tRemoved %s." % dst)
        shutil.copytree(_ROOT, dst)
        print("\tInstalled %s." % dst)
    
    print("Complete!")
        
if __name__ == "__main__": 
    install()