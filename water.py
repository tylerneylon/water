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
import os
from os import path
import parse
import sys

_module_dir = None
_module_names = []

def _get_module_names():
  global _module_dir, _module_names
  base_dir = path.dirname(path.realpath(sys.argv[0]))
  _module_dir = path.join(base_dir, 'modules')
  _module_names = os.listdir(_module_dir)
  def is_mod(m): return path.isdir(path.join(_module_dir, m))
  _module_names = filter(is_mod, _module_names)

def _get_module(mod_name):
  # We'll load <mod_dir>/<mod_name>/<mod_name>.py
  # Temporarily modify sys.path since Python uses it to find modules.
  sys.path.insert(0, path.join(_module_dir, mod_name))
  m = __import__(mod_name)
  sys.path.pop(0)
  return m

def _run_module(mod_name):
  if mod_name not in _module_names:
    fmt = "Uknown module '%s'; known modules are installed in %s"
    print(fmt % (mod_name, _module_dir))
    exit(2)
  mod = _get_module(mod_name)
  mod_dir = path.dirname(path.abspath(mod.__file__))
  # This translation gives args to the command that feel shell-native-ish to it.
  mod.main([' '.join(sys.argv[0:2])] + sys.argv[2:], mod_dir)

if __name__ == '__main__':
  _get_module_names()
  sys.argv[0] = path.basename(sys.argv[0])
  if len(sys.argv) < 2:
    my_name = os.path.basename(sys.argv[0])
    print("Usage: %s <water_filename> [options]" % my_name)
    exit(2)
  if True:
    dbg.dst = [sys.stdout]
    dbg.topics = ['tree', 'parse', 'public', 'temp']
    dbg.topics = ['run']
  else:
    #dbg.topics = 'all'
    dbg.dst = []
  if sys.argv[1].startswith('-'):  # It's a module request.
    # The first arg will be a single string like "water -<mod_name>".
    _run_module(sys.argv[1][1:])
  else:
    parse.runfile(sys.argv[1])
