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
# printname  color     desc
# --------------------------------------------------
# tree       yellow    Nicely formatted parse tree.
# parse      magenta   Useful function calls
# public     cyan      parse public method calls
# temp       blue      Very temporary stuff
# error      red       Error
# phrase     white     Every phrase parsed
#

from __future__ import print_function

import re
from StringIO import StringIO
import sys
import traceback
import types

# Globals.

all_rules = {'': {}}
rules = None
modes = []
mode = None
mode_result = None
parse = None
env = None

# Possibly TEMP. I'm using this for debugging.
parse_stack = []

# This is either 'all' or a list of whitelisted dbg_topic names.
dbg_topics = 'all'

# This is a list of writable file-like objects which receive debug output.
# Only sys.stdout is in color.
dbg_dst = [open('tmpout', 'w')]


# Set up cprint

try:
  from termcolor import colored
except:
  def _cprint(s, color=None): print(s)
  def colored(s, color=None): return s

def cprint(text, color=None, end='\n'):
  s = text + end
  for dst in dbg_dst:
    if dst is sys.stdout: s = colored(s, color)
    dst.write(s)

def dprint(dbg_topic, text, end='\n'):
  color_map = {'tree': 'yellow', 'parse': 'magenta', 'public': 'cyan',
               'temp': 'blue', 'error': 'red', 'phrase': 'white'}
  if not dbg_topic in color_map:
    cprint('Error: dprint called with unknown dbg_topic (%s)' % dbg_topic,
           'red')
    exit(1)
  if dbg_topics != 'all' and dbg_topic not in dbg_topics: return
  if dbg_topic == 'parse': text = '  ' * len(parse_stack) + text
  cprint(text, color=color_map[dbg_topic], end=end)

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
    dprint('temp', '__setitem__(self, %s, %s)' % (`name`, `value`))
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

    #cprint('********** in _run_fn, self.__dict__=%s' % `self.__dict__`, 'blue')

    lo = {}
    if 'tokens' in self.__dict__: lo['tokens'] = self.tokens
    if 'pieces' in self.__dict__:
      p = self.pieces
      lo.update({k: p[k][0] if len(p[k]) == 1 else p[k] for k in p})
    if 'mode_result' in self.__dict__: lo['mode_result'] = self.mode_result
    lo['self'] = self

    dprint('temp', 'lo=%s' % `lo`)
    #cprint('mode.__dict__=%s' % `mode.__dict__`, 'blue')
    n = `mode.name` if 'name' in mode.__dict__ else '<None>'
    dprint('temp', 'mode.name=%s' % n)

    arglist = ', '.join(k + '=None' for k in lo.keys())
    prefix = 'def %s(%s): ' % (fn_name, arglist)
    fn_code = prefix + fn_code

    dprint('temp', '(runtime) fn_code:\n%s\n' % fn_code)

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
    dprint('public', 'add_fn(%s, <code below>)' % fn_name)
    dprint('public', fn_code)
    self._add_fn(fn_name, fn_code)

  def _add_fn(self, fn_name, fn_code):
    def run(self):
      dprint('parse', 'run %s <%s>' % (fn_name, self.name))
      return self._run_fn(fn_name, fn_code)
    self._unbound_methods_[fn_name] = run
    self._bound_method(fn_name, run)

  def parse(self, code, pos):
    #return self.child().inst_parse(code, pos)
    parse_stack.append(self.name)
    tree, pos = self.child().inst_parse(code, pos)
    parse_stack.pop()
    if self.name == 'phrase' and tree:
      dprint('phrase', 'Successful phrase parse:')
      _debug_print(tree)
    return tree, pos


class SeqRule(Rule):

  def __init__(self, name, seq):
    self.name = name
    self.seq = seq
    Rule.__init__(self)
    self._add_fn('str', ' return "".join([str(t) for t in tokens])')

  def __getattribute__(self, name):
    try:
      return Rule.__getattribute__(self, name)
    except AttributeError:
      desc = "SeqRule '%s' has no '%s' attribute" % (self.name, name)
      raise AttributeError(desc)

  def parse_mode(self, code, pos):
    dprint('parse', '%s parse_mode' % self.name)
    #traceback.print_stack()
    init_num_modes = len(modes)
    if 'start' not in self.__dict__:
      fmt = 'Grammar error: expected rule %s to have a "start" method.'
      dprint('error', fmt % self.name)
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
      dprint('temp', 'rule_name=%s' % rule_name)
      if rule_name == '-|':
        dprint('parse', '%s parse reached -|' % self.name)
        tree, pos = self.parse_mode(code, pos)
        return self._end_parse(tree, pos)
      c = rule_name[0]
      if c == "'":
        val, pos = _parse_exact_str(rule_name[1:-1], code, pos)
      elif c == '"':
        re = rule_name[1:-1] % mode
        #cprint('mode.__dict__=%s' % `mode.__dict__`, 'blue')
        dprint('temp', 're=%s' % `re`)
        val, pos = _parse_exact_re(re, code, pos)
      else:
        val, pos = rules[rule_name].parse(code, pos)
        if val: self.pieces.setdefault(rule_name, []).append(val)
      if val is None:
        dbg_fmt = '%s parse failed at token %s ~= code %s'
        dprint('parse', dbg_fmt % (self.name, rule_name, code[pos:pos + 10]))
        #cprint('%s parse failed at %s' % (self.name, rule_name), 'magenta')
        return self._end_parse(None, self.startpos)
      self.tokens.append(val)
    #for key in self.pieces:
    #  if len(self.pieces[key]) == 1: self.pieces[key] = self.pieces[key][0]
    return self._end_parse(self, pos)

  def _end_parse(self, tree, pos):
    if tree is None: return tree, pos
    dprint('parse', '%s parse succeeded' % self.name)
    if 'parsed' in self.__dict__: self.parsed()
    return tree, pos

  def debug_print(self, indent='  '):
    dprint('tree', '%s' % self.name)
    for i in range(len(self.seq)):
      dprint('tree', indent, end='')
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
    dprint('temp', 'run_code(%s)' % `code`)
    dprint('temp', 'mode.__dict__=%s' % `mode.__dict__`)
    context = {'parse': parse, 'mode': mode}
    code = 'def or_else():' + code
    exec code in context
    return context['or_else']()

  def inst_parse(self, code, pos):
    _dbg_parse_start(self.name, code, pos)
    for r in self.or_list:
      if r[0] == ':':
        dprint('parse', '%s parse finishing as or_else clause' % self.name)
        tree = self.run_code(r[1:])
        return tree, pos
      val, pos = rules[r].parse(code, pos)
      if val:
        self.result = val
        dprint('parse', '%s parse succeeded as %s' % (self.name, r))
        return self, pos
    dprint('parse', '%s parse failed' % self.name)
    # TODO Factor out all these '  ' * len(parse_stack) instances.
    return None, pos

  def debug_print(self, indent='  '):
    dprint('tree', '%s -> ' % self.name, end='')
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
  dprint('public', 'or_rule(%s, %s, %s)' % (name, `or_list`, `mode`))
  return _add_rule(OrRule(name, or_list), mode)

def seq_rule(name, seq, mode=''):
  dprint('public', 'seq_rule(%s, %s, %s)' % (name, `seq`, `mode`))
  return _add_rule(SeqRule(name, seq), mode)

def false_rule(name, mode=''):
  dprint('public', 'false_rule(%s, %s)' % (name, `mode`))
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
  if pos < len(code):
    raise Exception('Parsing failed at byte %d' % pos)

def push_mode(name, opts={}):
  dprint('public', '    push_mode(%s, %s)' % (`name`, `opts`))
  global rules, mode, modes
  mode = Object()
  if len(modes): mode.__dict__.update(modes[-1].__dict__)
  mode.__dict__.update(opts)
  mode.id = name
  mode.rules = modes[-1].rules.copy() if len(modes) else {}
  mode.rules.update(all_rules[name])
  rules = mode.rules
  modes.append(mode)

def pop_mode(result):
  global rules, mode, modes, mode_result
  if len(modes) == 1:
    dprint('error',
           "Grammar error: pop_mode() when only global mode on the stack")
    exit(1)
  old_mode = modes.pop()
  if len(modes) == 1:
    # Refresh rules if we're at the global context.
    push_mode('', modes.pop().__dict__)
  mode = modes[-1]
  rules = mode.rules
  mode_result = result
  dprint('public', '    pop_mode(_); %s -> %s' % (`old_mode.id`, `mode.id`))
  return result


###############################################################################
#
# Internal functions.
#
###############################################################################

def _dbg_parse_start(name, code, pos):
  m = ' <%s>' % mode.id if len(mode.id) else ''
  dprint('parse', '%s%s parse at """%s"""' % (name, m, `code[pos: pos + 30]`))

def _debug_print(obj, indent='  ', seq_item=None):
  if isinstance(obj, Rule):
    obj.debug_print(indent)
  elif seq_item and seq_item.startswith('-|'):
    dprint('tree', '%s ' % seq_item, end='')
    _debug_print(obj, indent)
  elif seq_item:
    dprint('tree', '%s -> %s' % (seq_item, `obj`))
  elif type(obj) == list:
    dprint('tree', '')
    for i in obj:
      dprint('tree', indent, end='')
      _debug_print(i, indent + '  ')
  else:
    dprint('tree', '%s' % `obj`)
    
def _add_rule(rule, mode):
  if mode not in all_rules: all_rules[mode] = {}
  all_rules[mode][rule.name] = rule
  return rule

def _parse_exact_str(s, code, pos):
  to_escape = list("+()|*")
  for e in to_escape: s = s.replace(e, "\\" + e)
  return _parse_exact_re(s, code, pos)

# TODO Consider ways to do this witout using globals.

err_pos = -1
err_expected = None

def _parse_exact_re(s, code, pos):
  dprint('temp', 's before decode is %s' % `s`)
  s = s.decode('string_escape')

  a = code[pos:pos + 20]
  m = re.match(s, code[pos:], re.MULTILINE)
  if m:
    dprint('temp', 're.match(%s, %s, re.M) gives %s' % (`s`, `a`, `m.group(0)`))

  m = re.match(s, code[pos:], re.MULTILINE)
  if m:
    num_grp = len(m.groups()) + 1
    val = m.group(0) if num_grp == 1 else m.group(*tuple(range(num_grp)))
    return val, pos + len(m.group(0))
  global err_pos, err_expected
  if pos > err_pos: err_expected, err_pos = s, pos
  return None, pos

def _setup_base_rules():
  # Initial mode state.
  mode.indent = ''

  # Global rules.
  or_rule('phrase', ['statement', 'comment', 'blank', 'grammar'])
  seq_rule('blank', [r'"[ \t]*\n"'])
  seq_rule('comment', [r'"#[^\n]*\n"'])
  false_rule('statement')
  or_rule('grammar', ['command', 'global_grammar', 'mode_grammar'])
  r = seq_rule('command', ["'>:'", 'code_block'])
  r.add_fn('parsed', " exec(mode_result)\n")
  r = seq_rule('global_grammar', [r'">\n(?=(\s+))"', '-|'])
  r.add_fn('start', ("\n"
                     "  parse.push_mode('lang_def', {'indent': tokens[0][1],"
                     " 'name': ''})\n  mode.new_rules = []\n"))
  r = seq_rule('mode_grammar', ["'> '", 'word', r'"\n(?=(\s+))"', '-|'])
  r.add_fn('start', ("\n  opts = {'name': word.str(), 'indent': tokens[2][1]}\n"
                     "  parse.push_mode('lang_def', opts)\n"
                     "  mode.new_rules = []\n"))
  seq_rule('word', ['"[A-Za-z_]\w*"'])
  or_rule('code_block', ['indented_code_block', 'rest_of_line'])
  seq_rule('rest_of_line', [r'"[^\n]*\n"'])
  r = seq_rule('indented_code_block', [r'"\s*\n(?=(%(indent)s\s+))"', '-|'])
  r.add_fn('str', " return mode_result")
  r.add_fn('start', ("\n"
                     "  opts = {'indent': tokens[0][1]}\n"
                     "  parse.push_mode('nested_code_block', opts)\n"
                     "  mode.src = ['\\n']\n"))

  # lang_def rules.
  or_rule('phrase', ['indented_rule',
                     ": return parse.pop_mode(mode.new_rules)\n"],
                    mode='lang_def')
  r = seq_rule('indented_rule', ['"%(indent)s"', 'rule'], mode='lang_def')
  r.add_fn('parsed', " mode.new_rules.append(rule)")
  or_rule('rule', ['false_rule', 'or_rule', 'seq_rule'], mode='lang_def')
  r = seq_rule('false_rule', ['word', r'" ->\s+False[ \t]*\n"'], mode='lang_def')
  r.add_fn('parsed', " parse.false_rule(word.str(), mode=mode.name)")
  r = seq_rule('or_rule', ['word', "' -> '", 'or_list'])
  r.add_fn('parsed', (" parse.or_rule(word.str(), or_list.list(), "
                      "mode=mode.name)\n"))
  or_rule('or_list', ['multi_or_list', 'or_list_end'])
  r = seq_rule('or_list_end', ['rule_name', r'"[ \t]*\n"'])
  r.add_fn('list', " return rule_name.list()")
  or_rule('multi_or_list', ['std_multi_or_list', 'else_multi_or_list'])
  r = seq_rule('std_multi_or_list', ['rule_name', "' | '", 'or_list'])
  r.add_fn('list', " return rule_name.list() + or_list.list()")
  r = seq_rule('else_multi_or_list', ['rule_name', "' |: '", 'rest_of_line'])
  r.add_fn('list', " return rule_name.list() + [':' + rest_of_line.str()]")
  r = seq_rule('rule_name', ['word'])
  r.add_fn('list', " return [word.str()]")
  r = seq_rule('seq_rule', ['word', r'" ->\n%(indent)s(\s+)"', 'seq', '-|'])
  r.add_fn('start', ("\n  opts = {'indent': mode.indent + tokens[1][1]}\n"
                     "  parse.push_mode('rule_block', opts)\n"
                     "  mode.rule = parse.seq_rule(word.str(), seq.list(),"
                     " mode=mode.name)\n  mode.items = []\n"))
  or_rule('seq', ['item_end', 'mode_result_end', 'item_list'])
  r = seq_rule('item_end', ['item', r'"[ \t]*\n"'])
  r.add_fn('list', " return item.list()\n")
  r = seq_rule('mode_result_end', ["'-|'", r'"[ \t]*\n"'])
  r.add_fn('list', " return ['-|']\n")
  r = seq_rule('item_list', ['item', "' '", 'seq'])
  r.add_fn('list', " return item.list() + seq.list()\n")
  or_rule('item', ['str', 'rule_name'])
  r = seq_rule('str', ['"[\'\\\"]"', '-|'])  # print(seq[0]) gives "['\"]"
  r.add_fn('start', ("\n"
                     "  parse.push_mode('str', {'endchar': tokens[0][0]})\n"
                     "  global dbg_topics\n"
                     "  mode.dt = dbg_topics\n"
                     "  dbg_topics = []\n"
                     "  mode.chars = [mode.endchar]\n"))
  r.add_fn('list', " return [mode_result]")

  # rule_block rules.
  m = 'rule_block'
  or_rule('phrase', ['indented_rule_item',
                     ": return parse.pop_mode(mode.items)\n"], mode=m)
  r = seq_rule('indented_rule_item', ['"%(indent)s"', 'rule_item'], mode=m)
  r.add_fn('parsed', ' mode.items.append(rule_item)')
  or_rule('rule_item', ['bin_item', 'parse_item', 'method_item'], mode=m)
  r = seq_rule('bin_item', ["'='", 'code_block'], mode=m)
  r.add_fn('parsed', " mode.rule.add_fn('str', 'return ' + code_block.str())\n")
  r = seq_rule('parse_item', ["':'", 'code_block'], mode=m)
  r.add_fn('parsed', " mode.rule.add_fn('parsed', code_block.str())\n")
  r = seq_rule('method_item', ['word', "':'", 'code_block'], mode=m)
  r.add_fn('parsed', " mode.rule.add_fn(word.str(), code_block.str())")

  # str rules.
  or_rule('phrase', ['escape_seq', 'char'], mode='str')
  r = seq_rule('escape_seq', [r'"\\\\(.)"'], mode='str')
  r.add_fn('parsed', ("\n"
                      "  if tokens[0][1] != mode.endchar:\n"
                      "    mode.chars.append('\\\\')\n"
                      "  mode.chars.append(tokens[0][1])\n"))
  r = seq_rule('char', ['"."'], mode='str')
  r.add_fn('parsed', ("\n"
                      "  c = tokens[0][0]\n"
                      "  mode.chars.append(c)\n"
                      "  if c == mode.endchar:\n"
                      "    global dbg_topics\n"
                      "    dbg_topics = mode.dt\n"
                      "    parse.pop_mode(''.join(mode.chars))\n"))

  # nested_code_block rules.
  m = 'nested_code_block'
  or_rule('phrase', ['indented_code_line',
                     ": return parse.pop_mode(''.join(mode.src))"], mode=m)
  seq_rule('indented_code_line', ['"%(indent)s"', 'code_line'], mode=m)
  r = seq_rule('code_line', [r'"[^\n]*\n"'], mode=m)
  r.add_fn('parsed', " mode.src.append('  ' + tokens[0])\n")

  # Temporary hack to force global rules to refresh.
  push_mode('lang_def')
  pop_mode('')


###############################################################################
#
# Set up initial state.
#
###############################################################################

dbg_topics = []

env = Object()
push_mode('')  # Set up the global mode.
_setup_base_rules()


parse = sys.modules[__name__]

#dbg_topics = ['temp', 'public', 'parse']
dbg_topics = ['parse']
#dbg_topics = 'all'


###############################################################################
#
# Tests.
#
###############################################################################

# TODO More human-friendly formatting when a and b are long strings.
def expect(a, cond, b, ctx):
  stack = traceback.extract_stack()
  caller = stack[-2][2]
  a_val = eval(a, ctx)
  b_val = eval(b, ctx)
  eval_str = `a_val` + cond + `b_val`
  if not eval(eval_str, ctx):
    fmt = 'Fail (%s):\n  Expected %s %s %s but:\n  %s = %s\n  %s = %s'
    print(fmt % (caller, a, cond, b, a, `a_val`, b, `b_val`))
    return False
  return True

# Only check if we can parse the complete file, langauge definition3.water.
def test0():
  global dbg_topics, dbg_dst
  dbg_topics = []
  dbg_dst = []
  try: 
    for tree in file('language definition3.water'):
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
  global dbg_topics, dbg_dst
  dbg_topics = ['public']
  out = StringIO()
  dbg_dst = [out]
  try: 
    for tree in file('language definition3.water'):
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

