#!/usr/bin/python
#
# water.py
#
# A fluid compiler.
#
# TODO Add public documentation.
#

import dbg
import parse
import sys

###############################################################################
#
# Tests.
#
###############################################################################

def expect(a, cond, b, ctx):
  stack = traceback.extract_stack()
  caller = stack[-2][2]
  a_val = eval(a, ctx)
  b_val = eval(b, ctx)
  eval_str = `a_val` + cond + `b_val`
  # Special handling for == on long strings.
  if (cond == '==' and type(a_val) == type(b_val) == str and
      len(a_val + b_val) > 100):
    ls = enumerate(zip(a_val, b_val))
    i = next((i for i in ls if i[1][0] != i[1][1]), None)
    if i:
      i = i[0]
      a_val = '..' + a_val[max(0, i - 10):min(len(a_val), i + 10)] + '..'
      b_val = '..' + b_val[max(0, i - 10):min(len(b_val), i + 10)] + '..'
    elif len(a) != len(b):
      a_val = a_val[:20] + ' + %d more chars' % (len(a_val) - 20)
      b_val = b_val[:20] + ' + %d more chars' % (len(b_val) - 20)
  else:
    a_val = `a_val`
    b_val = `b_val`
  if not eval(eval_str, ctx):
    fmt = 'Fail (%s):\n  Expected %s %s %s but:\n  %s = %s\n  %s = %s'
    print(fmt % (caller, a, cond, b, a, a_val, b, b_val))
    return False
  return True

# Only check if we can parse the complete file, langauge definition3.water.
def test0():
  dbg.topics = ['public']
  dbg.dst = [sys.stdout]
  try: 
    for tree in iterate('language definition3.water'):
      pass
      #tree.debug_print()
  except Exception as e:
    print('Fail (test0): %s: %s' % (type(e).__name__, e))
    return False
  return True

def test1(return_out_str=False):
  # Check the following conditions:
  # * We parse the whole file.
  # * We get the right number of parse calls.
  # * The first and last parse calls look correct.
  dbg.topics = ['public']
  out = StringIO()
  dbg.dst = [out]
  try: 
    for tree in iterate('language definition3.water'):
      tree.debug_print()
  except Exception as e:
    print('Fail (test1): %s: %s' % (type(e).__name__, e))
    return False
  out.seek(0)
  out_str = out.read()
  lines = out_str.split('\n')
  if not expect('len(lines)', '==', '318', locals()): return False
  first_line = "    push_mode('lang_def', {'indent': '  ', 'name': ''})"
  if not expect('lines[0]', '==', 'first_line', locals()): return False
  last_line = "    pop_mode(_); 'lang_def' -> ''"
  if not expect('lines[-2]', '==', 'last_line', locals()): return False
  return out_str if return_out_str else True

def test2():
  # Check the following conditions:
  # * Both parses succeed.
  # * The parse calls are the same both times.
  out1 = test1(True)
  out2 = test1(True)
  return expect('out1', '==', 'out2', locals())

def test3():
  runfile('sample12.water')


###############################################################################
#
# Ability to run directly.
#
###############################################################################

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

