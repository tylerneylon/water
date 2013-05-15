#!/usr/bin/python
#
# run.py
#
# Runtime functions for project water.
#

import dbg
import parse

stack = []
indents = ['\n']
stack_end_is_indent = False
_run_ctx = {}

# When this is True, we print out the strings to be run instead of running them.
only_print = False

def _add(rule_or_str):
  if type(rule_or_str) == str:
    s = rule_or_str  # Clarify that it's a string.
    global stack_end_is_indent
    stack_end_is_indent = s.endswith('\n')
    s = indents[-1].join(s.split('\n'))
    stack.append(s)
  elif 'Rule' in str(type(rule_or_str)):
    #elif isinstance(rule_or_str, parse.Rule):
    rule_or_str.add_code()
  else:
    parse.error('Illegal input to run.add; type=%s' % type(rule_or_str))

def add(*args):
  for arg in args: _add(arg)

def run(*args):
  add(*args)
  global stack
  code = ''.join(stack)
  stack = []
  if only_print:
    dbg.dprint('run', code, end='')
  else:
    exec code in _run_ctx

def push_indent(indent):
  indents.append(indents[-1] + indent)
  if stack_end_is_indent: stack.append(indent)

def pop_indent():
  if len(indents) == 1:
    parse.error('Call to pop_indent() when indent stack is empty.')
  else:
    diff = len(indents[-2]) - len(indents[-1])
    indents.pop()
    if stack_end_is_indent:
      stack[-1] = stack[-1][:diff]  # Drop the popped indent.

