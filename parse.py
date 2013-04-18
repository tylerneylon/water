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

all_rules = {}
rules = None
modes = []
mode = None
mode_result = None
parse = None

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
  def __setitem__(self, name, value):
    print('__setitem__(self, %s, %s)' % (`name`, `value`))
    self.__dict__[name] = value


# TODO Should add_fn and _run_fn only be available on SeqRule?
class Rule(Object):

  def _run_fn(self, fn_name, fn_code):

    # We temporarily define variables for user code as globals since Python has
    # weird behavior for scoping in exec calls. See:
    # http://stackoverflow.com/a/2906198/3561
    global tokens
    tokens = self.tokens

    lo = {}
    exec fn_code in globals(), lo
    lo[fn_name](self)

    del tokens

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
    while len(modes) > init_num_modes:
      tree, pos = rules['phrase'].parse(code, pos)
      if tree is None: return None, self.startpos
    self.tokens.append(mode_result)
    results = {'tokens': self.tokens, 'mode_result': mode_result}
    results.update(self.pieces)
    return self.new_match(results), pos

  def parse(self, code, pos):
    print('%s parse' % self.name)
    self.tokens = []
    self.pieces = {}
    self.startpos = pos
    for rule_name in self.seq:
      print('rule_name=%s' % rule_name)
      if rule_name == '-|': return self.parse_mode(code, pos)
      c = rule_name[0]
      if c == "'":
        val, pos = parse_exact_str(rule_name[1:-1], code, pos)
      elif c == '"':
        re = rule_name[1:-1] % mode
        print('mode.__dict__=%s' % `mode.__dict__`)
        print('re=%s' % `re`)
        val, pos = parse_exact_re(re, code, pos)
      else:
        val, pos = rules[rule_name].parse(code, pos)
        if val: self.pieces.setdefault(rule_name, []).append(val)
      if val is None: return None, self.startpos
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

  def run_code(self, code):
    print('run_code(%s)' % `code`)
    print('mode.__dict__=%s' % `mode.__dict__`)
    context = {'parse': parse, 'mode': mode}
    code = 'def or_else():' + code
    exec code in context
    return context['or_else']()

  def parse(self, code, pos):
    print('%s parse' % self.name)
    for r in self.or_list:
      if r[0] == ':':
        tree = self.run_code(r[1:])
        return tree, pos
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
    #print('self.results=%s' % `self.results`)
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

def or_rule(name, or_list, mode=''):
  return _add_rule(OrRule(name, or_list), mode)

def seq_rule(name, seq, mode=''):
  return _add_rule(SeqRule(name, seq), mode)

def false_rule(name, mode=''):
  return _add_rule(FalseRule(name), mode)

def file(filename):
  f = open(filename)
  code = f.read()
  pos = 0
  f.close()
  tree, pos = rules['phrase'].parse(code, pos)
  while tree:
    yield tree
    tree, pos = rules['phrase'].parse(code, pos)

def push_mode(name, opts):
  print('push_mode(%s, %s)' % (name, `opts`))
  global rules, mode, modes
  mode = Object()
  mode.__dict__.update(opts)
  mode.id = name
  mode.opts = opts
  mode.rules = modes[-1].rules.copy() if len(modes) else {}
  mode.rules.update(all_rules[name])
  rules = mode.rules
  modes.append(mode)

def pop_mode(result):
  print('pop_mode(_)')
  global rules, mode, modes, mode_result
  if len(modes) == 1:
    print("Grammar error: pop_mode() when only global mode on the stack")
    exit(1)
  modes.pop()
  mode = modes[-1]
  rules = mode.rules
  mode_result = result
  return result

###############################################################################
#
# Define functions.
#
###############################################################################

def _add_rule(rule, mode):
  if mode not in all_rules: all_rules[mode] = {}
  all_rules[mode][rule.name] = rule
  return rule

def parse_exact_str(s, code, pos):
  to_escape = list("+()")
  for e in to_escape: s = s.replace(e, "\\" + e)
  return parse_exact_re(s, code, pos)

# TODO Consider ways to do this witout using globals.

err_pos = -1
err_expected = None

def parse_exact_re(s, code, pos):
  print('s before decode is %s' % `s`)
  s = s.decode('string_escape')

  a = code[pos:pos + 20]
  m = re.match(s, code[pos:], re.MULTILINE)
  if m: print('re.match(%s, %s, re.M) gives %s' % (`s`, `a`, `m.group(0)`))

  m = re.match(s, code[pos:], re.MULTILINE)
  if m:
    num_grp = len(m.groups()) + 1
    val = m.group(0) if num_grp == 1 else m.group(*tuple(range(num_grp)))
    return val, pos + len(m.group(0))
  global err_pos, err_expected
  if pos > err_pos: err_expected, err_pos = s, pos
  return None, pos

def setup_base_rules():
  # Global rules.
  or_rule('phrase', ['statement', 'comment', 'blank', 'grammar'])
  seq_rule('blank', [r'"\n"'])
  seq_rule('comment', [r'"#[^\n]*\n"'])
  false_rule('statement')
  or_rule('grammar', ['global_grammar', 'mode_grammar'])
  r = seq_rule('global_grammar', [r'">\n(?=(\s+))"', '-|'])
  r.add_fn('start', "\n  print('gg_start')\n  print('tokens=%s' % `tokens`)\n  parse.push_mode('lang_def', {'indent': tokens[0][1]})\n  mode.rules = []\n")
  seq_rule('word', ['"[A-Za-z_]\w*"'])

  # lang_def rules.
  or_rule('phrase', ['indented_rule', ': return parse.pop_mode(mode.rules)'], mode='lang_def')
  r = seq_rule('indented_rule', ['"%(indent)s"', 'rule'], mode='lang_def')
  r.add_fn('parsed', " mode.rules.append(rule)")
  or_rule('rule', ['false_rule', 'or_rule', 'seq_rule'], mode='lang_def')
  r = seq_rule('false_rule', ['word', "' -> '", 'or_list'], mode='lang_def')
  r.add_fn('parsed', " parse.false_rule(word.str(), mode=mode.name)")
  r = seq_rule('or_rule', ['word', "' -> '", 'or_list'])
  r.add_fn('parsed', " parse.or_rule(word.str(), or_list.list(), mode=mode.name)\n")
  or_rule('or_list', ['rule_name', 'multi_or_list'])
  or_rule('multi_or_list', ['std_multi_or_list', 'else_multi_or_list'])
  r = seq_rule('std_multi_or_list', ['rule_name', "' | '", 'or_list'])
  r.add_fn('list', " return rule_name.list() + or_list.list()")
  r = seq_rule('rule_name', ['word'])
  r.add_fn('list', " return [word.str()]")


###############################################################################
#
# Set up initial state.
#
###############################################################################

setup_base_rules()
push_mode('', {})  # Set up the global mode.

parse = Object()
public_fns = [or_rule, seq_rule, false_rule, file, push_mode, pop_mode]
for fn in public_fns: parse[fn.__name__] = fn


