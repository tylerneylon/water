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
import run
import sys

# This function is here since it doesn't belong directly in the core. The core
# is only responsible for making this function possible.
def showwork(filename):
  run.run_code = False
  parse.runfile(filename)

  f = open(filename)
  src = f.read()
  # TODO I just realized I'm not using the terms src & code consistently.
  #      Go back and change many uses of code -> src.
  #      To be clear to myself: 'src' means the input, 'code' is the output
  #      sent to the runtime during normal operation.
  f.close()
  src_lines = src.split('\n')

  next_src_idx = 0
  next_line_idx = 0
  next_code_idx = 0
  
  # TODO NEXT  Print this stuff out side-by-side.

  print(run.state_list)
  print(run.code_list)

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print("Usage: %s <water_filename> [options]" % sys.argv[0])
    exit(2)
  if True:
    dbg.dst = [sys.stdout]
    dbg.topics = ['tree', 'parse', 'public']
    dbg.topics = ['run']
  else:
    #dbg.topics = 'all'
    dbg.dst = []
  if '--showwork' in sys.argv:
    showwork(sys.argv[1])
  else:
    parse.runfile(sys.argv[1])

