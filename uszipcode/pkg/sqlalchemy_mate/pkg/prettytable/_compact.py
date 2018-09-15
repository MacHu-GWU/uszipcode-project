import sys


py3k = sys.version_info[0] >= 3

if py3k:
    str_types = (str, )
    unicode_ = str
    basestring_ = str
    itermap = map
    iterzip = zip
    uni_chr = chr
    from html.parser import HTMLParser
    import io as StringIO
else:
    unicode_ = unicode
    basestring_ = basestring
    str_types = (unicode, str)
    import itertools
    itermap = itertools.imap
    iterzip = itertools.izip
    uni_chr = unichr
    from HTMLParser import HTMLParser
    import StringIO

HTMLParser, StringIO


if py3k and sys.version_info[1] >= 2:
    from html import escape
else:
    from cgi import escape
escape
