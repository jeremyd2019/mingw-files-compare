#!/usr/bin/env python

from __future__ import print_function

import argparse
import io
import re
import sys
import tarfile
from typing import Dict, List
from urllib.request import urlopen

def parse_desc(t: str) -> Dict[str, List[str]]:
    d: Dict[str, List[str]] = {}
    cat = None
    values: List[str] = []
    for l in t.splitlines():
        l = l.strip()
        if cat is None:
            cat = l
        elif not l:
            d[cat] = values
            cat = None
            values = []
        else:
            values.append(l)
    if cat is not None:
        d[cat] = values
    return d


def parse_repo(url: str) -> Dict[str, Dict[str, List[str]]]:
    sources: Dict[str, Dict[str, List[str]]] = {}
    print("Loading %r" % url, file=sys.stderr)

    with urlopen(url) as u:
        with io.BytesIO(u.read()) as f:
            with tarfile.open(fileobj=f, mode="r:gz") as tar:
                packages: Dict[str, list] = {}
                for info in tar.getmembers():
                    package_name = info.name.split("/", 1)[0]
                    infofile = tar.extractfile(info)
                    if infofile is None:
                        continue
                    with infofile:
                        packages.setdefault(package_name, []).append(
                            (info.name, infofile.read()))

    for package_name, infos in sorted(packages.items()):
        t = ""
        for name, data in sorted(infos):
            if name.endswith("/desc"):
                t += data.decode("utf-8")
            elif name.endswith("/depends"):
                t += data.decode("utf-8")
            elif name.endswith("/files"):
                t += data.decode("utf-8")
        desc = parse_desc(t)
        sources[package_name] = desc
    return sources

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compare file lists')
    parser.add_argument('first')
    parser.add_argument('second')
    args = parser.parse_args()

    pkgpattern = re.compile(r'mingw-w64-(clang-|ucrt-)?(x86_64|i686|aarch64)-')
    filepattern = re.compile(r'^/?[^/]+/')
    r = {pkgpattern.sub('mingw-w64-', key): value for key, value in parse_repo("https://mirror.msys2.org/mingw/{0}/{0}.files".format(args.first)).items()}
    s = {pkgpattern.sub('mingw-w64-', key): value for key, value in parse_repo("https://mirror.msys2.org/mingw/{0}/{0}.files".format(args.second)).items()}
    for pkg in sorted(r.keys() | s.keys()):
        if pkg not in r:
            print("{}: only in {}".format(pkg, args.second))
        elif pkg not in s:
            print("{}: only in {}".format(pkg, args.first))
        else:
            rf = set(filepattern.sub('', f) for f in r[pkg]['%FILES%'])
            sf = set(filepattern.sub('', f) for f in s[pkg]['%FILES%'])
            symdiff = rf ^ sf
            if symdiff:
                print("--- ", r[pkg]['%NAME%'][0])
                print("+++ ", s[pkg]['%NAME%'][0])
                for f in sorted(symdiff):
                    sym = '-' if f in rf else '+'
                    print(sym, " ", f)