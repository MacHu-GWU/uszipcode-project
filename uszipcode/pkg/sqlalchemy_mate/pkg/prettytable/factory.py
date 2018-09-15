"""
Table factories
"""
import csv
from .prettytable import PrettyTable
from ._compact import py3k, HTMLParser
from ..sixmini import binary_type


def from_csv(fp, field_names=None, **kwargs):
    fmtparams = {}
    for param in ["delimiter", "doublequote", "escapechar", "lineterminator",
                  "quotechar", "quoting", "skipinitialspace", "strict"]:
        if param in kwargs:
            fmtparams[param] = kwargs.pop(param)
    if fmtparams:
        reader = csv.reader(fp, **fmtparams)
    else:
        dialect = csv.Sniffer().sniff(fp.read(1024))
        fp.seek(0)
        reader = csv.reader(fp, dialect)

    table = PrettyTable(**kwargs)
    if field_names:
        table.field_names = field_names
    else:
        if py3k:
            table.field_names = [x.strip() for x in next(reader)]
        else:
            table.field_names = [x.strip() for x in reader.next()]

    for row in reader:
        table.add_row([x.strip() for x in row])

    return table


def ensure_str(v):
    if isinstance(v, binary_type):
        v = v.decode("utf-8")
    return v


def from_db_cursor(cursor, **kwargs):
    if cursor.description:
        table = PrettyTable(**kwargs)
        table.field_names = [ensure_str(col[0]) for col in cursor.description]
        for row in cursor.fetchall():
            table.add_row(row)
        return table


class TableHandler(HTMLParser):
    def __init__(self, **kwargs):
        HTMLParser.__init__(self)
        self.kwargs = kwargs
        self.tables = []
        self.last_row = []
        self.rows = []
        self.max_row_width = 0
        self.active = None
        self.last_content = ""
        self.is_last_row_header = False
        self.colspan = 0

    def handle_starttag(self, tag, attrs):
        self.active = tag
        if tag == "th":
            self.is_last_row_header = True
        for (key, value) in attrs:
            if key == "colspan":
                self.colspan = int(value)

    def handle_endtag(self, tag):
        if tag in ["th", "td"]:
            stripped_content = self.last_content.strip()
            self.last_row.append(stripped_content)
            if self.colspan:
                for i in range(1, self.colspan):
                    self.last_row.append("")
                self.colspan = 0

        if tag == "tr":
            self.rows.append(
                (self.last_row, self.is_last_row_header))
            self.max_row_width = max(self.max_row_width, len(self.last_row))
            self.last_row = []
            self.is_last_row_header = False
        if tag == "table":
            table = self.generate_table(self.rows)
            self.tables.append(table)
            self.rows = []
        self.last_content = " "
        self.active = None

    def handle_data(self, data):
        self.last_content += data

    def generate_table(self, rows):
        """
        Generates from a list of rows a PrettyTable object.
        """
        table = PrettyTable(**self.kwargs)
        for row in self.rows:
            if len(row[0]) < self.max_row_width:
                appends = self.max_row_width - len(row[0])
                for i in range(1, appends):
                    row[0].append("-")

            if row[1] is True:
                self.make_fields_unique(row[0])
                table.field_names = row[0]
            else:
                table.add_row(row[0])
        return table

    def make_fields_unique(self, fields):
        """
        iterates over the row and make each field unique
        """
        for i in range(0, len(fields)):
            for j in range(i + 1, len(fields)):
                if fields[i] == fields[j]:
                    fields[j] += "'"


def from_html(html_code, **kwargs):
    """
    Generates a list of PrettyTables from a string of HTML code. Each <table> in
    the HTML becomes one PrettyTable object.
    """

    parser = TableHandler(**kwargs)
    parser.feed(html_code)
    return parser.tables


def from_html_one(html_code, **kwargs):
    """
    Generates a PrettyTables from a string of HTML code which contains only a
    single <table>
    """

    tables = from_html(html_code, **kwargs)
    try:
        assert len(tables) == 1
    except AssertionError:
        raise Exception(
            "More than one <table> in provided HTML code!  Use from_html instead.")
    return tables[0]
