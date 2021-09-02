#!/usr/bin/env python

from __future__ import print_function

import argparse
import re
import sys

from pacdb import pacdb

PACKAGE_PREFIXES = {
        "clang32":    "mingw-w64-clang-i686-",
        "clang64":    "mingw-w64-clang-x86_64-",
        "clangarm64": "mingw-w64-clang-aarch64-",
        "mingw32":    "mingw-w64-i686-",
        "mingw64":    "mingw-w64-x86_64-",
        "ucrt64":     "mingw-w64-ucrt-x86_64-"
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compare file lists')
    parser.add_argument('--staging', action='store_true')
    parser.add_argument('first')
    parser.add_argument('second')
    args = parser.parse_args()

    pkgpattern = re.compile(r'mingw-w64-(clang-|ucrt-)?(x86_64|i686|aarch64)-')
    filepattern = re.compile(r'^/?[^/]+/')
    r = {pkgpattern.sub('mingw-w64-', pkg.name): pkg for pkg in pacdb.mingw_db_by_name(args.first, 'files')}
    if args.staging:
        s = {pkgpattern.sub('mingw-w64-', pkg.name): pkg for pkg in pacdb.Database.from_url('staging', 'https://repo.msys2.org/staging', 'files') if pkg.name.startswith(PACKAGE_PREFIXES[args.second])}
    else:
        s = {pkgpattern.sub('mingw-w64-', pkg.name): pkg for pkg in pacdb.mingw_db_by_name(args.second, 'files')}
    for pkg in sorted(r.keys() | s.keys()):
        if pkg not in r:
            print("Only in {1}: {0}".format(pkg, args.second))
        elif pkg not in s:
            if not args.staging:
                print("Only in {1}: {0}".format(pkg, args.first))
        else:
            rf = set(filepattern.sub('', f) for f in r[pkg].files)
            sf = set(filepattern.sub('', f) for f in s[pkg].files)
            symdiff = rf ^ sf
            if symdiff:
                print("diff", r[pkg].name, s[pkg].name)
                print("---", r[pkg].name, r[pkg].version)
                print("+++", s[pkg].name, s[pkg].version)
                for f in sorted(symdiff):
                    sym = '-' if f in rf else '+'
                    print(sym, f, sep='')
