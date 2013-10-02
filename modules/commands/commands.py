#!/usr/bin/python
#
# commands.py
#
# A Water module to extract the low-level commands needed to
# execute a grammar using only >: commands.
#

from __future__ import print_function

import os
import parse
import re
import run

# globals

make_rule_str = None
rule_cmd_strs = []
include_newlines = True
mangle_inner_names = False

# functions

# This filters out newlines if the user requests it.
# This can introduce loss of indent recognition, so it
# requires the input to be one-line-friendly.
def print_out(s, is_command=False):
  s = s.rstrip()
  # Remove newlines when the user requested it *and* it's not a command.
  # One-line commands are left as one-line, but we might break multi-line
  # commands (eg with an if or loop block), so we leave their newlines in.
  if not include_newlines and not is_command:
    m = re.match('\s+', s)
    if m: s = s[m.end():]
    s = s.replace('\n', ';')
  if is_command and re.match(r'\s*(parse\.)?(runfile|command)', s): return
  if mangle_inner_names: s = re.sub(r'_inner_(?=\d)', '__inner_', s)
  print('>:%s%s' % ('' if s.startswith(' ') else ' ', s))

def end_last_rule():
  global make_rule_str, rule_cmd_strs
  if make_rule_str is None: return
  if len(rule_cmd_strs) == 0:
    print_out(make_rule_str)
    make_rule_str = None
    return
  s = '\n  r = %s' % make_rule_str
  for rule_cmd in rule_cmd_strs:
    s += '\n  %s' % rule_cmd
  print_out(s)
  make_rule_str = None
  rule_cmd_strs = []

def hook_command_fn():
  old_fn = parse.command
  def new_fn(cmd):
    end_last_rule()
    print_out(cmd, is_command=True)
    old_fn(cmd)
  parse.command = new_fn

def hook_add_fn_method():
  old_method = parse.Rule.add_fn
  def new_method(self, fn_name, fn_code):
    global rule_cmd_strs
    rule_cmd_strs.append('r.add_fn(%s, %s)' % (`fn_name`, `fn_code`))
    old_method(self, fn_name, fn_code)
  parse.Rule.add_fn = new_method

def hook_prepend_to_or():
  old_method = parse.prepend_to_or
  def new_method(name, or_name, mode=''):
    end_last_rule()
    print_out('prepend_to_or(%s, %s, %s)' % (`name`, `or_name`, `mode`))
    old_method(name, or_name, mode)
  parse.prepend_to_or = new_method

def hook_rule_fn(fn_name):
  old_fn = parse.__dict__[fn_name]
  def new_fn(*args, **kwargs):
    global make_rule_str
    end_last_rule()
    kwargs_str = ''.join([', %s=%s' % (k, `kwargs[k]`) for k in kwargs])
    args_str = ', '.join([`arg` for arg in args])
    make_rule_str = '%s(%s%s)' % (fn_name, args_str, kwargs_str)
    return old_fn(*args, **kwargs)
  parse.__dict__[fn_name] = new_fn

# main

def main(args, self_dir):
  
  if len(args) < 2:
    print('Usage: %s <water_filename>' % args[0])
    exit(2)

  global include_newlines, mangle_inner_names
  include_newlines = not ('--nonewlines' in args)
  mangle_inner_names = ('--mangle' in args)

  in_filename = args[1]
  run.run_code = False

  rule_fns = ['or_rule', 'seq_rule', 'bool_rule']
  for fn_name in rule_fns:
    hook_rule_fn(fn_name)
  hook_command_fn()
  hook_add_fn_method()
  hook_prepend_to_or()

  parse.runfile(in_filename)

  end_last_rule()

