#!/usr/bin/python
#
# parse.py
#
# The code needed to build, modify, and run a dynamic language parser.
#
# TODO Document public functions.
#

# TEMP Print colors:
#
# Yellow:    Nicely formatted parse tree.
# Magenta:   Useful function calls
# Cyan:      parse public method calls
# Blue:      Very temporary stuff
# Red:       Error
#

from __future__ import print_function

import re
import traceback # TEMP TODO
import types

try:
  from termcolor import cprint
except:
  def cprint(s, color=None): print(s)

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
    cprint('__setitem__(self, %s, %s)' % (`name`, `value`), 'blue')
    self.__dict__[name] = value


# TODO Should add_fn and _run_fn only be available on SeqRule?
class Rule(Object):

  def __init__(self):
    self._unbound_methods_ = {}

  def __str__(self): return self.str()

  def _run_fn(self, fn_name, fn_code):
    # This function is wonky because exec has wonky treatment of locals. See:
    # http://stackoverflow.com/a/1463370
    # http://stackoverflow.com/a/2906198

    #cprint('************** in _run_fn, self.__dict__=%s' % `self.__dict__`, 'blue')

    lo = {}
    if 'tokens' in self.__dict__: lo['tokens'] = self.tokens
    if 'pieces' in self.__dict__: lo.update(self.pieces)
    if 'mode_result' in self.__dict__: lo['mode_result'] = self.mode_result
    lo['self'] = self

    #cprint('lo=%s' % `lo`, 'blue')

    arglist = ', '.join(k + '=None' for k in lo.keys())
    prefix = 'def %s(%s): ' % (fn_name, arglist)
    fn_code = prefix + fn_code

    #cprint('\n\n(runtime) fn_code:\n\n%s\n\n' % fn_code, 'blue')

    fn_lo = {}
    exec fn_code in globals(), fn_lo
    res = fn_lo[fn_name](**lo)
    #cprint('got result=%s' % `res`, 'blue')
    return res

  def _bound_method(self, fn_name, unbound_fn):
    self.__dict__[fn_name] = types.MethodType(unbound_fn, self, self.__class__)

  def _bind_all_methods(self):
    for fn_name in self._unbound_methods_:
      self._bound_method(fn_name, self._unbound_methods_[fn_name])

  def add_fn(self, fn_name, fn_code):
    def run(self):
      cprint('run %s <%s>' % (fn_name, self.name), 'magenta')
      return self._run_fn(fn_name, fn_code)
    self._unbound_methods_[fn_name] = run
    self._bound_method(fn_name, run)

  def parse(self, code, pos):
    return self.child().inst_parse(code, pos)


class SeqRule(Rule):

  def __init__(self, name, seq):
    self.name = name
    self.seq = seq
    Rule.__init__(self)
    self.add_fn('str', ' return "".join([str(t) for t in tokens])')

  def __getattribute__(self, name):
    try:
      return Rule.__getattribute__(self, name)
    except AttributeError:
      desc = "SeqRule '%s' has no '%s' attribute" % (self.name, name)
      raise AttributeError(desc)

  def parse_mode(self, code, pos):
    cprint('%s parse_mode' % self.name, 'magenta')
    #traceback.print_stack()
    init_num_modes = len(modes)
    if 'start' not in self.__dict__:
      fmt = 'Grammar error: expected rule %s to have a "start" method.'
      cprint(fmt % self.name, 'red')
      exit(1)
    self.start()
    self.mode_id = mode.id
    while len(modes) > init_num_modes:
      tree, pos = rules['phrase'].parse(code, pos)
      if tree is None: return None, self.startpos
    self.tokens.append(mode_result)
    self.pieces['mode_result'] = mode_result
    return self, pos

  def inst_parse(self, code, pos):
    _dbg_parse_start(self.name, code, pos)
    self.tokens = []
    self.pieces = {}
    self.startpos = pos
    for rule_name in self.seq:
      cprint('rule_name=%s' % rule_name, 'blue')
      if rule_name == '-|':
        cprint('%s parse reached -|' % self.name, 'magenta')
        tree, pos = self.parse_mode(code, pos)
        return self._end_parse(tree, pos)
      c = rule_name[0]
      if c == "'":
        val, pos = parse_exact_str(rule_name[1:-1], code, pos)
      elif c == '"':
        re = rule_name[1:-1] % mode
        #cprint('mode.__dict__=%s' % `mode.__dict__`, 'blue')
        cprint('re=%s' % `re`, 'blue')
        val, pos = parse_exact_re(re, code, pos)
      else:
        val, pos = rules[rule_name].parse(code, pos)
        if val: self.pieces.setdefault(rule_name, []).append(val)
      if val is None:
        cprint('%s parse failed at %s' % (self.name, rule_name), 'magenta')
        return self._end_parse(None, self.startpos)
      self.tokens.append(val)
    for key in self.pieces:
      if len(self.pieces[key]) == 1: self.pieces[key] = self.pieces[key][0]
    return self._end_parse(self, pos)

  def _end_parse(self, tree, pos):
    if tree is None: return tree, pos
    cprint('%s parse succeeded' % self.name, 'magenta')
    if 'parsed' in self.__dict__: self.parsed()
    return tree, pos

  def debug_print(self, indent='  '):
    cprint('%s' % self.name, 'yellow')
    for i in range(len(self.seq)):
      print(indent, end='')
      item = '-| %s' % self.mode_id if self.seq[i] == '-|' else self.seq[i]
      _debug_print(self.tokens[i], indent + '  ', item)

  def child(self):
    c = SeqRule(self.name, self.seq)
    c.__dict__ = self.__dict__.copy()
    c._bind_all_methods()
    return c


class OrRule(Rule):

  def __init__(self, name, or_list):
    self.name = name
    self.or_list = or_list
    Rule.__init__(self)

  def __getattribute__(self, name):
    try:
      return Rule.__getattribute__(self, name)
    except AttributeError:
      d = Rule.__getattribute__(self, '__dict__')
      if 'result' in d: return d['result'].__getattribute__(name)
      raise

  def run_code(self, code):
    cprint('run_code(%s)' % `code`, 'blue')
    cprint('mode.__dict__=%s' % `mode.__dict__`, 'blue')
    context = {'parse': parse, 'mode': mode}
    code = 'def or_else():' + code
    exec code in context
    return context['or_else']()

  def inst_parse(self, code, pos):
    _dbg_parse_start(self.name, code, pos)
    for r in self.or_list:
      if r[0] == ':':
        cprint('%s parse finishing as or_else clause' % self.name, 'magenta')
        tree = self.run_code(r[1:])
        return tree, pos
      val, pos = rules[r].parse(code, pos)
      if val:
        self.result = val
        cprint('%s parse succeeded as %s' % (self.name, r), 'magenta')
        return self, pos
    cprint('%s parse failed' % self.name, 'magenta')
    return None, pos

  def debug_print(self, indent='  '):
    cprint('%s -> ' % self.name, 'yellow', end='')
    _debug_print(self.result, indent)

  def child(self):
    c = OrRule(self.name, self.or_list)
    c.__dict__ = self.__dict__.copy()
    c._bind_all_methods()
    return c


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
  cprint('or_rule(%s, %s, %s)' % (name, `or_list`, `mode`), 'cyan')
  return _add_rule(OrRule(name, or_list), mode)

def seq_rule(name, seq, mode=''):
  cprint('seq_rule(%s, %s, %s)' % (name, `seq`, `mode`), 'cyan')
  return _add_rule(SeqRule(name, seq), mode)

def false_rule(name, mode=''):
  cprint('false_rule(%s, %s)' % (name, `mode`), 'cyan')
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
  cprint('push_mode(%s, %s)' % (`name`, `opts`), 'cyan')
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
  global rules, mode, modes, mode_result
  if len(modes) == 1:
    cprint("Grammar error: pop_mode() when only global mode on the stack",
           'red')
    exit(1)
  modes.pop()
  mode = modes[-1]
  rules = mode.rules
  mode_result = result
  cprint('pop_mode(_); new mode is %s' % `mode.id`, 'cyan')
  return result

###############################################################################
#
# Define functions.
#
###############################################################################

def _dbg_parse_start(name, code, pos):
  cprint('%s parse at """%s"""' % (name, `code[pos: pos + 30]`), 'magenta')

def _debug_print(obj, indent='  ', seq_item=None):
  if isinstance(obj, Rule):
    obj.debug_print(indent)
  elif seq_item and seq_item.startswith('-|'):
    cprint('%s ' % seq_item, 'yellow', end='')
    _debug_print(obj, indent)
  elif seq_item:
    cprint('%s -> %s' % (seq_item, `obj`), 'yellow')
  elif type(obj) == list:
    print('')
    for i in obj:
      print(indent, end='')
      _debug_print(i, indent + '  ')
  else:
    cprint('%s' % `obj`, 'yellow')
    
def _add_rule(rule, mode):
  if mode not in all_rules: all_rules[mode] = {}
  all_rules[mode][rule.name] = rule
  return rule

def parse_exact_str(s, code, pos):
  to_escape = list("+()|*")
  for e in to_escape: s = s.replace(e, "\\" + e)
  return parse_exact_re(s, code, pos)

# TODO Consider ways to do this witout using globals.

err_pos = -1
err_expected = None

def parse_exact_re(s, code, pos):
  cprint('s before decode is %s' % `s`, 'blue')
  s = s.decode('string_escape')

  a = code[pos:pos + 20]
  m = re.match(s, code[pos:], re.MULTILINE)
  if m:
    cprint('re.match(%s, %s, re.M) gives %s' % (`s`, `a`, `m.group(0)`), 'blue')

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
  r.add_fn('start', ("\n  print('gg_start')\n  print('tokens=%s' % `tokens`)\n"
                     "  parse.push_mode('lang_def', {'indent': tokens[0][1],"
                     " 'name': ''})\n  mode.new_rules = []\n"))
  r = seq_rule('mode_grammar', ["'> '", 'word', r'"\n(?=(\s+))"', '-|'])
  r.add_fn('start', ("\n  opts = {'name': word.str(), 'indent': tokens[2][1]}\n"
                     "  parse.push_mode('lang_def', opts)\n"
                     "  mode.new_rules = []\n"))
  seq_rule('word', ['"[A-Za-z_]\w*"'])

  # lang_def rules.
  or_rule('phrase', ['indented_rule', (":\n  print('popping from lang_def')\n"
                                       "  return parse.pop_mode("
                                       "mode.new_rules)\n")], mode='lang_def')
  r = seq_rule('indented_rule', ['"%(indent)s"', 'rule'], mode='lang_def')
  r.add_fn('parsed', " mode.new_rules.append(rule)")
  or_rule('rule', ['false_rule', 'or_rule', 'seq_rule'], mode='lang_def')
  r = seq_rule('false_rule', ['word', r'"->\s+False"'], mode='lang_def')
  r.add_fn('parsed', " parse.false_rule(word.str(), mode=mode.name)")
  r = seq_rule('or_rule', ['word', "' -> '", 'or_list'])
  r.add_fn('parsed', " parse.or_rule(word.str(), or_list.list(), mode=mode.name)\n")
  or_rule('or_list', ['multi_or_list', 'or_list_end'])
  r = seq_rule('or_list_end', ['rule_name', r'"[ \t]*\n"'])
  r.add_fn('list', " return rule_name.list()")
  or_rule('multi_or_list', ['std_multi_or_list', 'else_multi_or_list'])
  r = seq_rule('std_multi_or_list', ['rule_name', "' | '", 'or_list'])
  r.add_fn('list', " return rule_name.list() + or_list.list()")
  r = seq_rule('else_multi_or_list', ['rule_name', "' |: '", 'command', r'"[ \t]*\n"'])
  r.add_fn('list', " return rule_name.list() + [{'else': command.str()}]")
  r = seq_rule('rule_name', ['word'])
  r.add_fn('list', " return [word.str()]")
  seq_rule('command', [r'"[^\n]*\n"'])
  r = seq_rule('seq_rule', ['word', r'" ->\n%(indent)s(\s+)"', 'seq', '-|'])
  r.add_fn('start', ("\n  opts = {'indent': mode.indent + tokens[1][1]}\n"
                     "  parse.push_mode('rule_block', opts)\n"
                     "  mode.rule = parse.seq_rule(word.str(), seq.list(),"
                     " mode=mode.name)\n  mode.items = []\n"))
  or_rule('seq', ['item_list', 'item', 'mode_result'])
  or_rule('item', ['str', 'rule_name'])
  r = seq_rule('str', ['"[\'\\\"]"', '-|'])  # print(seq[0]) gives "['\"]"
  r.add_fn('start', ("\n  parse.push_mode('str', {'endchar': tokens[0][0]})\n"
                     "  mode.chars = []\n"))
  r.add_fn('list', " return [mode_result]")
  r = seq_rule('item_list', ['item', "' '", 'seq'])
  r.add_fn('list', " return item.list() + seq.list()")
  r = seq_rule('mode_result', ["'-|'"])
  r.add_fn('list', " return ['-|']")



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

###############################################################################
#
# Temp code for debugging / init development.
#
###############################################################################

def test():
  for tree in file('language definition3.water'):
    tree.debug_print()

