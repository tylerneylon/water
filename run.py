#!/usr/bin/python
#
# run.py
#
# Runtime functions for project water.
#

import dbg
import parse
import sys

stack = []
indents = ['\n']
stack_end_is_indent = False
_run_ctx = {}
_state = None
_state_stack = []

# These can be used for meta operations such as printing out line-by-line
# src-to-code translations.
code_list = []
state_list = []

run_code = True
print_code = False

if '--showcode' in sys.argv:
  run_code = False
  print_code= True

def _add(rule_or_str):
  if type(rule_or_str) == str:
    s = rule_or_str  # Clarify that it's a string.
    global stack, stack_end_is_indent, _state, _state_stack
    stack_end_is_indent = s.endswith('\n')
    s = indents[-1].join(s.split('\n'))
    stack.append(s)
    _state_stack.append(_state)
  elif isinstance(rule_or_str, parse.Rule):
    r = rule_or_str  # Clarify that it's a rule.
    _state = {'start': r.start_pos, 'end': r.end_pos}
    r.add_code()
  else:
    parse.error('Illegal input to run.add; type=%s' % type(rule_or_str))

def add(*args):
  for arg in args: _add(arg)

def run(*args):
  add(*args)
  global stack, code_list, state_list, _state_stack
  code_list += stack
  state_list += _state_stack
  code = ''.join(stack)
  stack, _state_stack = [], []
  if print_code: dbg.dprint('run', code, end='')
  if run_code: exec code in _run_ctx

def push_indent(indent):
  indents.append(indents[-1] + indent)
  if stack_end_is_indent: stack[-1] += indent

def pop_indent():
  if len(indents) == 1:
    parse.error('Call to pop_indent() when indent stack is empty.')
  else:
    diff = len(indents[-2]) - len(indents[-1])
    indents.pop()
    if stack_end_is_indent:
      stack[-1] = stack[-1][:diff]  # Drop the popped indent.

