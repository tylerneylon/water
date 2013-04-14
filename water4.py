#!/usr/bin/python
#
# water4.py
#
# Goal: Improving from water3, be able to read in a language definition file
#       and then parse another file written in that language. Also, to do so
#       in a way that includes source-to-output translation rules, and doesn't
#       just produce a parse tree.
#       
# In particular, take steps in writing this file:
# 0. Get read_lang_def to parse and understand language definition3.water.
# 1. Get read_lang_def to parse and understand language definition2.water.
# 2. Use the output of 1 to parse the statements at the bottom of that file.
#
# Future steps:
# 3. Actually execute sample1.water.
# 4. Begin work to unify how these two files are read in, so that they are no
#    longer separate steps.
#

import parse


###############################################################################
#
# Begin high-level goal code.
#
###############################################################################

def exec_file(filename):
  for tree in parse.file(filename):
    tree.debug_print()

if __name__ == '__main__':
  exec_file('language definition3.water')

