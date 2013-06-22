#!/usr/bin/python
#
# tests.py
#
# Automated tests for project water.
#
# TODO Add public documentation.
#

# How to add a new test:
#  * Make a function that runs the test and returns True/False to indicate
#    success or failure.
#  * The function should take a final **kwargs parameter, and should suppress
#    all (non-failure) output when run_silent=True.
#  * Add the function to the all_tests list in the main block at the bottom
#    of this file.
#

from __future__ import print_function
from StringIO import StringIO

import dbg
import iter
import parse
import run
import sys
import traceback

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
def test0(run_silent=False, **kwargs):
  dbg.topics = ['public']
  dbg.dst = [] if run_silent else [sys.stdout] 
  try: 
    for tree in parse.iterate('base_grammar.water'):
      pass
      #dbg.print_tree(tree)
  except Exception as e:
    print('Fail (test0): %s: %s' % (type(e).__name__, e))
    return False
  return True

def test1(return_out_str=False, **kwargs):
  # Check the following conditions:
  # * We parse the whole file.
  # * We get the right number of parse calls.
  # * The first and last parse calls look correct.
  dbg.topics = ['public']
  out = StringIO()
  dbg.dst = [out]
  try: 
    for tree in parse.iterate('base_grammar.water'):
      dbg.print_tree(tree)
  except Exception as e:
    print('Fail (test1): %s: %s' % (type(e).__name__, e))
    return False
  out.seek(0)
  out_str = out.read()
  lines = out_str.split('\n')
  if not expect('len(lines)', '==', '293', locals()): return False
  first_line = "    push_mode('lang_def', {})"
  if not expect('lines[0]', '==', 'first_line', locals()): return False
  last_line = "    pop_mode(_); 'lang_def' -> ''"
  if not expect('lines[-2]', '==', 'last_line', locals()): return False
  return out_str if return_out_str else True

def test2(**kwargs):
  # Check the following conditions:
  # * Both parses succeed.
  # * The parse calls are the same both times.
  out1 = test1(True)
  out2 = test1(True)
  return expect('out1', '==', 'out2', locals())

def test3(run_silent=False, **kwargs):
  dbg.topics = ['tree']
  dbg.dst = [] if run_silent else [sys.stdout] 
  run_code = run.run_code
  run.run_code = False
  did_succeed = True
  try: 
    parse.runfile('../samples/12.water')
  except Exception as e:
    if not run_silent: print('Fail (test3): %s: %s' % (type(e).__name__, e))
    did_succeed = False
  run.run_code = run_code
  return did_succeed

def test4(**kwargs):  # Test iter.Iterator.
  orig = 'a line 1\nb line 2\nc line 3\n'
  it = iter.Iterator(orig)
  expectations = [['it.text()', '==', 'orig'],
                  ['it.tail()', '==', 'orig'],
                  ['it.version', '==', '0'],
                  ['it.text_pos', '==', '0']]
  for exp in expectations:
    if not expect(*(exp + [locals()])): return False
  it.replace([0, 1], 'abc')
  text = 'abc' + orig[1:]
  expectations = [['it.text()', '==', 'text'],
                  ['it.tail()', '==', 'text'],
                  ['it.version', '==', '1']]
  for exp in expectations:
    if not expect(*(exp + [locals()])): return False
  it.move(2)
  expectations = [['it.text_pos', '==', '2'],
                  ['it.orig_pos_of_text_pos(2)', '==', '0'],
                  ['it.orig_pos_of_text_pos(3)', '==', '1'],
                  ['it.tail()', '==', 'text[2:]']]
  for exp in expectations:
    if not expect(*(exp + [locals()])): return False
  it.replace([len(text) - 1, len(text)], 'new ending')
  text = text[:-1] + 'new ending'
  expectations = [['it.version', '==', '2'],
                  ['it.text()', '==', 'text'],
                  ['it.tail()', '==', 'text[2:]'],
                  ['it.orig_pos_of_text_pos(3)', '==', '1'],
                  ['it.orig_pos_of_text_pos(len(text))', '==', 'len(orig)']]
  # Now try a replacement overlapping a previous replacement.
  it.replace([1, 3], 'X')
  text = text[0] + 'X' + text[3:]
  expectations = [['it.version', '==', '3'],
                  ['it.text()', '==', 'text'],
                  ['it.tail()', '==', 'text[2:]'],
                  ['it.orig_pos_of_text_pos(0)', '==', '0'],
                  ['it.orig_pos_of_text_pos(1)', '==', '0'],
                  ['it.orig_pos_of_text_pos(2)', '==', '1']]
  for exp in expectations:
    if not expect(*(exp + [locals()])): return False
  return True

if __name__ == '__main__':
  all_tests = [test0, test1, test2, test3, test4]
  kwargs = {'run_silent': True}
  for t in all_tests:
    print('Running %s ' % t.__name__, end='')
    result = t(**kwargs)
    print('PASS' if result else 'FAIL')

    

