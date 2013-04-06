#!/usr/bin/python
#
# water4.py
#
# Goal: Improving from water3, be able to read in a language definition file
#       and then parse another file written in that language. Also, to do so
#       in a way that includes source-to-output translation rules, and doesn't
#       just produce a parse tree.
#       
# In particular, take two steps in writing this file:
# 1. Get read_lang_def to parse and understand language definition2.water.
# 2. Use the output of 1 to parse sample1.water.
#
# Future steps:
# 3. Actually execute sample1.water.
# 4. Begin work to unify how these two files are read in, so that they are no
#    longer separate steps.
#

import sys

class Object(object):
  # Enable parentheses-free method calls, as in: retVal = myObj.method
  def __getattribute__(self, name):
    val = object.__getattribute__(self, name)
    try: return val()
    except: return val
  # Enable bracket-syntax on attributes, as in: retVal = myObj[methodName]
  def __getitem__(self, name): return self.__getattribute__(name)
  def __setitem__(self, name, value): self.__dict__[name] = value

###############################################################################
#
# Begin high-level goal code.
#
###############################################################################

def read_lang_def(filename):
  pass

def exec_file(filename):
  pass

if __name__ == '__main__':
  read_lang_def('langauge definition2.water')
  exec_file('sample1.water')

