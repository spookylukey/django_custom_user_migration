#!/usr/bin/env python

import os
import sys

if __name__ == '__main__':
    if len(sys.argv) > 1:
        tests = sys.argv[1:]
    else:
        tests = ['discover tests']

    os.system("python -m unittest " + " ".join(tests))
