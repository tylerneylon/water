#!/usr/bin/python
#
# parse.py
#
# The code needed to build, modify, and run a dynamic language parser.
#
# TODO Document public functions.
#

from __future__ import print_function

import re
import traceback # TEMP TODO


# Globals.

rules = None
modes = [{'id': '', 'opts': {}}]
mode = modes[-1]

###############################################################################
#
# Define classes.
#
###############################################################################

class Object(object):
  # Enable parentheses-free method calls, as in: retVal = myObj.method
  # NOTE I added an extra underscore here to disable this next method:
  def ___getattribute__(self, name):
    selfname = '_'
    d = object.__getattribute__(self, '__dict__')
    if 'name' in d: selfname = d['name']
    #print('__getattribute__(%s, %s)' % (selfname, name))
    val = object.__getattribute__(self, name)
    try: return val()
    except (NameError, TypeError): return val
  # Enable bracket-syntax on attributes, as in: retVal = myObj[methodName]
  def __getitem__(self, name):
    selfname = '_'
    if 'name' in self.__dict__: selfname = self.__dict__['name']
    #print('__getitem__(%s, %s)' % (selfname, name))
    #traceback.print_stack()
    return self.__getattribute__(name)
  def __setitem__(self, name, value): self.__dict__[name] = value

class Rule(Object):
  def _run_fn(self, fn_name, fn_code):
    local = {}
    exec fn_code in {}, local
    local[fn_name](self)
  def add_fn(self, fn_name, fn_code):
    fn_code = ('def %s(self):' % fn_name) + fn_code
    def run():
      print('run %s <%s>' % (fn_name, self.name))
      self._run_fn(fn_name, fn_code)
    self[fn_name] = run

class SeqRule(Rule):
  def __init__(self, name, seq):
    self.name = name
    self.seq = seq
  def parse_mode(self, code, pos):
    print('%s parse_mode' % self.name)
    #traceback.print_stack()
    init_num_modes = len(modes)
    if 'start' not in self.__dict__:
      fmt = 'Grammar error: expected rule %s to have a "start" method.'
      print(fmt % self.name)
      exit(1)
    self.start()
    # TODO Handle a StopIteration exception here (it's a user error, but we
    #      should handle it gracefully).
    while len(modes) > init_num_modes: parser.next()
    # TODO HERE Return the parse result.
  def parse(self, code, pos):
    print('%s parse' % self.name)
    self.tokens = []
    self.pieces = {}
    self.startpos = pos
    for rule_name in self.seq:
      print('rule_name=%s' % rule_name)
      if rule_name == '-|': return self.parse_mode(code, pos)
      c = rule_name[0]
      if c == "'": val, pos = parse_exact_str(rule_name[1:], code, pos)
      elif c == '"': val, pos = parse_exact_re(rule_name[1:-1], code, pos)
      else:
        val, pos = rules[rule_name].parse(code, pos)
        if val: pieces[rule_name] = pieces.get(rule_name, []) + [val[rule_name]]
      if val is None: return None, startpos
      self.tokens.append(val)
    for key in self.pieces:
      if len(self.pieces[key]) == 1: self.pieces[key] = self.pieces[key][0]
    results = {'tokens': self.tokens}
    results.update(self.pieces)
    return self.new_match(results), pos
  def debug_print(self, indent='', or_cont=False):
    #print('self.__dict__ = %s' % `self.__dict__`)
    if or_cont: print()  # Print a newline.
    tokens = self.results['tokens']
    for i in range(len(self.seq)):
      print('%s%s -> %s' % (indent, self.seq[i], `tokens[i]`))
  def new_match(self, results):
    match = SeqRule(self.name, self.seq)
    match.results = results
    return match

class OrRule(Rule):
  def __init__(self, name, or_list):
    self.name = name
    self.or_list = or_list
  def parse(self, code, pos):
    for r in self.or_list:
      val, pos = rules[r].parse(code, pos)
      if val:
        results = {'name': r, 'value': val}
        return self.new_match(results), pos
    return None, pos
  def new_match(self, results):
    match = OrRule(self.name, self.or_list)
    match.results = results
    return match
  def debug_print(self, indent='', or_cont=False):
    print('self.results=%s' % `self.results`)
    if not or_cont:
      print('%s%s' % (indent, self.name), end='')
    print(' -> %s' % self.results['name'], end='')
    self.results['value'].debug_print(indent + '  ', or_cont=True)

class FalseRule(Rule):
  def __init__(self, name):
    self.name = name
  def parse(self, code, pos):
    return None, pos


###############################################################################
#
# Public functions.
#
###############################################################################

def or_rule(name, or_list):
  rules[name] = OrRule(name, or_list)
  return rules[name]

def seq_rule(name, seq):
  rules[name] = SeqRule(name, seq)
  return rules[name]

def false_rule(name):
  rules[name] = FalseRule(name)
  return rules[name]

def file(filename):
  f = open(filename)
  code = f.read()
  pos = 0
  f.close()
  tree, pos = rules.phrase.parse(code, pos)
  while tree:
    yield tree
    tree, pos = rules.phrase.parse(code, pos)

###############################################################################
#
# Define functions.
#
###############################################################################

def parse_exact_str(s, code, pos):
  to_escape = list("+()")
  for e in to_escape: s = s.replace(e, "\\" + e)
  return parse_exact_re(s, code, pos)

# TODO Consider ways to do this witout using globals.

err_pos = -1
err_expected = None

def parse_exact_re(s, code, pos):
  s = s.decode('string_escape')
  m = re.match(r"(%s)\s*" % s, code[pos:])
  if m: return m.group(1), pos + len(m.group(0))
  global err_pos, err_expected
  if pos > err_pos: err_expected, err_pos = s, pos
  return None, pos

# TODO TEMP Goal: have rules[mode][rule_name] be the rule object, mode == ''
#                 means the global mode.
def get_base_rules():
  global rules
  rules = Object()

  # Global rules.
  or_rule('phrase', ['statement', 'comment', 'blank', 'grammar'])
  seq_rule('blank', [r'"\n"'])
  seq_rule('comment', [r'"#[^\n]*\n"'])
  false_rule('statement')
  or_rule('grammar', ['global_grammar', 'mode_grammar'])
  r = seq_rule('global_grammar', [r'">\n(?=(\s+))"', '-|'])
  r.add_fn('start', "\n  print('gg_start')\n  parse.push_mode('lang_def', {'indent': tokens[0][1]})")

  return rules

rules = get_base_rules()

