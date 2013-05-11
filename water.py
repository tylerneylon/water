#!/usr/bin/python
#
# water.py
#
# A fluid compiler.
#
# TODO Add public documentation.
#

from __future__ import print_function

import dbg
import parse
import sys

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print("Usage: %s <water_filename>" % sys.argv[0])
    exit(2)
  if True:
    dbg.dst = [sys.stdout]
    dbg.topics = ['tree', 'parse', 'public']
    dbg.topics = ['run']
  else:
    #dbg.topics = 'all'
    dbg.dst = []
  parse.runfile(sys.argv[1])

