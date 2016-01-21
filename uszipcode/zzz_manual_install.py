#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Install your own package in one seconds! (For Windows, MacOS, Linux system)
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
for the python intepreter you currently using. Basically, it just removes ``.pyc``
file from ``mypackage`` directory. Then create a directory and copy all file in 
``mypackage`` to it:

Windows::

    C:\Python33\Lib\site-packages\mypackage

MacOS::

    /Library/Python/2.7/site-packages/mypackage
    
Linux::

    /usr/lib/python2.7/dist-packages

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


一键安装你的自定义库! (For Windows, MacOS, Linux System)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
本脚用于在一键安装用户自己写的扩展包, 纯python实现。

例如你有一个扩展包叫 mypackage, 文件目录形如: ``C:\project\mypackage``

则只需要把该脚本拷贝到 mypackage 目录下:
``C:\project\mypackage\zzz_manual_install.py``

然后将本脚本以主脚本运行。则会把 ``mypackage`` 文件中所有的 ``.pyc`` 文件清除后, 
安装到你当前运行本脚本时使用的Python的版本下。我们以Python27版本为例, 那么运行
本脚本的结果是创建以下目录并将 ``mypackage`` 目录中的文件拷贝到该目录下:

Windows::

    C:\Python33\Lib\site-packages\mypackage

MacOS::

    /Library/Python/2.7/site-packages/mypackage
    
Linux::

    /usr/lib/python2.7/dist-packages

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
**Copyright (c) 2016 by Sanhe Hu**

- Author: Sanhe Hu
- Email: husanhe@gmail.com
- Lisence: MIT


**Compatibility**

- Python2: Yes
- Python3: Yes
    

**Prerequisites**

- None


Class, method, function, exception
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

from __future__ import print_function, unicode_literals
import hashlib, site, shutil, os 

_ROOT = os.getcwd()
_PACKAGE_NAME = os.path.basename(_ROOT)
_DST = os.path.join(site.getsitepackages()[1], _PACKAGE_NAME)
    
def md5_of_file(abspath):
    """Md5 value of a file.
    """
    chunk_size = 1024 * 1024
    m = hashlib.md5()
    with open(abspath, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            m.update(data)
    return m.hexdigest()

def check_need_install():
    """Check if installed package are exactly the same to this one.
    """
    md5_root, md5_dst = list(), list()
    need_install_flag = False
    for root, _, basename_list in os.walk(_ROOT):
        if os.path.basename(root) != "__pycache__":
            for basename in basename_list:
                src = os.path.join(root, basename)
                dst = os.path.join(root.replace(_ROOT, _DST), basename)
                if os.path.exists(dst):
                    if md5_of_file(src) != md5_of_file(dst):
                        return True
                else:
                    return True
    return need_install_flag
    
def install():
    """Manual install main script.
    """
    # check installed package
    print("Compare to '%s' ..." % _DST)
    need_install_flag = check_need_install()
    if not need_install_flag:
        print("\tpackage is up-to-date, no need to install.")
        return
    print("Difference been found, start installing ...")
    
    # remove __pycache__ folder and *.pyc file
    print("Remove *.pyc file ...")  
    pyc_folder_list = list()
    for root, _, basename_list in os.walk(_ROOT):
        if os.path.basename(root) == "__pycache__":
            pyc_folder_list.append(root)
     
    for folder in pyc_folder_list:
        shutil.rmtree(folder)
    print("\tall *.pyc file has been removed.")
       
    # install this package to all python version
    print("Uninstall %s from %s ..." % (_PACKAGE_NAME, _DST))
    try:
        shutil.rmtree(_DST)
        print("\tSuccessfully uninstall %s" % _PACKAGE_NAME)
    except Exception as e:
        print("\t%s" % e)
       
    print("Install %s to %s ..." % (_PACKAGE_NAME, _DST))
    shutil.copytree(_ROOT, _DST)     
    print("\tComplete!")
        
if __name__ == "__main__":
    install()