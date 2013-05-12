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

def push(rule_or_str):
  if type(rule_or_str) == str:
    s = rule_or_str  # Clarify that it's a string.
    global stack_end_is_indent
    stack_end_is_indent = s.endswith('\n')
    s = indents[-1].join(s.split('\n'))
    stack.append(s)
  # TODO Avoid parse.py being main so that we can do this correctly.
  elif 'Rule' in str(type(rule_or_str)):
    #elif isinstance(rule_or_str, parse.Rule):
    rule_or_str.push_code()
  else:
    parse.error('Illegal input to run.push; type=%s' % type(rule_or_str))

def read_all():
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

