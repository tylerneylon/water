#!/usr/bin/python
#
# dbg.py
#
# Functions to handle debug output for project water.
#


# TEMP Print colors:
#
# printname  color     desc
# --------------------------------------------------
# tree       yellow    Nicely formatted parse tree.
# parse      magenta   Useful function calls
# public     cyan      parse public method calls
# temp       blue      Very temporary stuff
# error      red       Error
# phrase     white     Every phrase parsed
# run        green     Strings sent to run fn
#

from __future__ import print_function
import sys

# This is either 'all' or a list of whitelisted dbg_topic names.
topics = 'all'

# This is a list of writable file-like objects which receive debug output.
# Only sys.stdout is in color.
dst = []

# If true, prints a number before every dprint statement.
# This can be useful for setting a breakpoint for a deterministic error.
showNums = False    # Default: False
breakOnNum = None   # Default: None
_num = 0


# Set up cprint

try:
  from termcolor import colored
except:
  def _cprint(s, color=None): print(s)
  def colored(s, color=None): return s

def cprint(text, color=None, end='\n'):
  global _num, showNums, breakOnNum
  s = text + end
  _num += 1
  if showNums: s = str(_num) + ' ' + s
  for d in dst:
    if d is sys.stdout:
      # red output is redirected to stderr from stdout.
      if color != 'red': d.write(colored(s, color))
    else:
      d.write(s)
  if color == 'red':
    sys.stderr.write(colored(s, color))
  if _num == breakOnNum:
    import pdb; pdb.set_trace()

def dprint(dbg_topic, text, end='\n'):
  color_map = {'tree': 'yellow', 'parse': 'magenta', 'public': 'cyan',
               'temp': 'blue', 'error': 'red', 'phrase': 'white',
               'run': 'green'}
  if not dbg_topic in color_map:
    cprint('Error: dprint called with unknown dbg_topic (%s)' % dbg_topic,
           'red')
    exit(1)
  t = dbg_topic
  if t != 'error' and topics != 'all' and t not in topics: return
  # TODO If I want this back in, I need to get the parse_stack length from
  #      input since the module dependencies will get sticky if I import parse.
  #if dbg_topic == 'parse': text = '  ' * len(parse.parse_stack) + text
  cprint(text, color=color_map[dbg_topic], end=end)

