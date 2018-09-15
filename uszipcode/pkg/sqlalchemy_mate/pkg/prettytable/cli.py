from __future__ import print_function
import argparse
import sys

from .factory import from_csv
from ._compact import StringIO


def main():
    text_in = sys.stdin.read()
    if text_in:
        print(from_csv(StringIO.StringIO(text_in)))
        return

    parser = argparse.ArgumentParser(description='A simple Python library designed to make it quick and easy to '
                                     'represent tabular data in visually appealing ASCII tables.')
    parser.add_argument('--csv', help='CSV file name')
    args = parser.parse_args()
    with open(args.csv) as fp:
        print(from_csv(fp))


if __name__ == '__main__':
    main()
