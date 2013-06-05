#!/usr/bin/python
#
# parse.py
#
# Code to parse, compile, and modify a language.
#
# TODO Document public functions.
#
# TODO Add 'public' output for >: commands.
#


from __future__ import print_function

import bisect
import dbg
import os
import re
import run
import sys
import types

# Globals.

all_rules = {'': {}}
rules = None
modes = []
mode = None
parse = None
env = None

parse_stack = []
start_pos = 0
line_starts = []

# parse_info stores parse attempt data so we can display human-friendly error
# information that simplifies debugging grammars and syntax errors alike.
#
# parse_info.attempts = [list of parse_attempt Objects]
# parse_info.main_attempt = the parse_attempt we suspect was intended
# parse_info.code = the code string being parsed
#
# attempt.stack = list of rule names in the attempt, phrase-first
# attempt.start_pos = byte index of where parse stack began parsing
# attempt.fail_pos = byte index of where the last stack token mismatched
#
parse_info = None


#------------------------------------------------------------------------------
#  Define classes.
#------------------------------------------------------------------------------

class Object(object):
  def __getitem__(self, name):
    return self.__getattribute__(name)
  def __setitem__(self, name, value):
    self.__dict__[name] = value
  def __contains__(self, name):
    try: self.__getitem__(name)
    except AttributeError: return False
    return True
  def __repr__(self): return repr(self.__dict__)


class Rule(Object):

  def __init__(self):
    self._unbound_methods_ = {}

  def __str__(self): return self.str()

  def _run_fn(self, fn_name, fn_code):
    # We send in lo as kwargs because exec uses the local context strangely:
    # http://stackoverflow.com/a/1463370
    # http://stackoverflow.com/a/2906198
    lo = {}
    if 'tokens' in self.__dict__: lo['tokens'] = self.tokens
    if 'pieces' in self.__dict__:
      p = self.pieces
      lo.update({k: p[k][0] if len(p[k]) == 1 else p[k] for k in p})
    if 'mode_result' in self.__dict__: lo['mode_result'] = self.mode_result
    lo['self'] = self

    arglist = ', '.join(k + '=None' for k in lo.keys())
    prefix = 'def %s(%s): ' % (fn_name, arglist)
    fn_code = prefix + fn_code

    fn_lo = {}
    try:
      exec fn_code in globals(), fn_lo
      return fn_lo[fn_name](**lo)
    except:
      msg = 'Exception running a user-level function. Code:\n%s\n' % fn_code
      dbg.dprint('error', msg)
      raise

  def _bound_method(self, fn_name, unbound_fn):
    self.__dict__[fn_name] = types.MethodType(unbound_fn, self, self.__class__)

  def _bind_all_methods(self):
    for fn_name in self._unbound_methods_:
      self._bound_method(fn_name, self._unbound_methods_[fn_name])

  def add_fn(self, fn_name, fn_code):
    dbg.dprint('public', 'add_fn(%s, <code below>)' % fn_name)
    dbg.dprint('public', fn_code)
    self._add_fn(fn_name, fn_code)

  def _add_fn(self, fn_name, fn_code):
    def run(self):
      dbg.dprint('parse', 'run %s <%s>' % (fn_name, self.name))
      return self._run_fn(fn_name, fn_code)
    self._unbound_methods_[fn_name] = run
    self._bound_method(fn_name, run)

  def parse(self, code, pos):
    parse_stack.append(self.name)
    tree, pos = self.child().inst_parse(code, pos)
    parse_stack.pop()
    return tree, pos


class SeqRule(Rule):

  def __init__(self, name, seq):
    self.name = name
    self.seq = seq
    Rule.__init__(self)
    self._add_fn('str', ' return self.src()')

  def __getattribute__(self, name):
    try:
      return Rule.__getattribute__(self, name)
    except AttributeError:
      desc = "SeqRule '%s' has no '%s' attribute" % (self.name, name)
      raise AttributeError(desc)

  def src(self):
    return ''.join([_src(t) for t in self.tokens])

  # Expects self.mode_id to be set, and will push that mode.
  def parse_mode(self, code, pos):
    dbg.dprint('parse', '%s parse_mode %s' % (self.name, self.mode_id))
    init_num_modes = len(modes)
    params = {}
    push_mode(self.mode_id)
    if 'mode_params' in self.__dict__: _set_mode_params(self.mode_params())
    mode_result = []
    # A mode is popped from either a successful parse or a |: clause. The |:
    # is a special case where the returned tree is None, but it is not a parse
    # error; that case is the reason for the if clause after this while loop.
    while True:
      tree, pos = rules['phrase'].parse(code, pos)
      if len(modes) == init_num_modes: break
      if tree is None: return None, self.startpos
      mode_result.append(tree)
    if tree: mode_result.append(tree)
    self.tokens.append(mode_result)
    self.pieces['mode_result'] = mode_result
    return self, pos

  def inst_parse(self, code, pos):
    _dbg_parse_start(self.name, code, pos)
    self.start_pos = pos
    self.tokens = []
    self.pieces = {}
    self.startpos = pos
    for rule_name in self.seq:
      dbg.dprint('temp', 'rule_name=%s' % rule_name)
      c = rule_name[0]
      if c == '-':
        dbg.dprint('parse', '%s parse reached %s' % (self.name, rule_name))
        self.mode_id = rule_name[1:]
        tree, pos = self.parse_mode(code, pos)
        return self._end_parse(tree, pos)
      elif c == "'":
        val, pos = _parse_exact_str(rule_name[1:-1], code, pos)
      elif c == '"':
        re = rule_name[1:-1] % mode
        #cprint('mode.__dict__=%s' % `mode.__dict__`, 'blue')
        dbg.dprint('temp', 're=%s' % `re`)
        val, pos = _parse_exact_re(re, code, pos)
      else:
        val, pos = rules[rule_name].parse(code, pos)
        if val: self.pieces.setdefault(rule_name, []).append(val)
      if val is None:
        dbg_fmt = '%s parse failed at token %s ~= code %s'
        dbg.dprint('parse', dbg_fmt % (self.name, rule_name, code[pos:pos + 10]))
        #cprint('%s parse failed at %s' % (self.name, rule_name), 'magenta')
        return self._end_parse(None, self.startpos)
      self.tokens.append(val)
    #for key in self.pieces:
    #  if len(self.pieces[key]) == 1: self.pieces[key] = self.pieces[key][0]
    return self._end_parse(self, pos)

  def _end_parse(self, tree, pos):
    self.end_pos = pos
    if tree is None: return tree, pos
    # TODO Think of a way to do this more cleanly. Right now run._state is
    # awkwardly set from both parse and run.
    # For examle, maybe a command could set up its code_block as the body of an
    # add_code fn, and then call run.add on itself.
    run._state = {'start': self.start_pos, 'end': self.end_pos}
    dbg.dprint('parse', '%s parse succeeded' % self.name)
    if 'parsed' in self.__dict__: self.parsed()
    return tree, pos

  def debug_print(self, indent='  '):
    dbg.dprint('tree', '%s' % self.name)
    for i in range(len(self.seq)):
      dbg.dprint('tree', indent, end='')
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
    #dbg.dprint('temp', 'run_code(%s)' % `code`)
    #dbg.dprint('temp', 'mode.__dict__=%s' % `mode.__dict__`)
    context = {'parse': parse, 'mode': mode}
    code = 'def or_else():' + code
    exec code in context
    return context['or_else']()

  def inst_parse(self, code, pos):
    _dbg_parse_start(self.name, code, pos)
    self.start_pos = pos
    for r in self.or_list:
      if r[0] == ':':
        dbg.dprint('parse', '%s parse finishing as or_else clause' % self.name)
        self.run_code(r[1:])
        self.end_pos = pos
        return None, pos
      val, pos = rules[r].parse(code, pos)
      if val:
        self.result = val
        self.end_pos = pos
        dbg.dprint('parse', '%s parse succeeded as %s' % (self.name, r))
        return self, pos
    dbg.dprint('parse', '%s parse failed' % self.name)
    # TODO Factor out all these '  ' * len(parse_stack) instances.
    return None, pos

  def debug_print(self, indent='  '):
    dbg.dprint('tree', '%s -> ' % self.name, end='')
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


class ParseError(Exception):
  pass


#------------------------------------------------------------------------------
#  Public functions.
#------------------------------------------------------------------------------

def command(cmd):
  # We wrap cmd as a function body to make it easier to deal with user indents.
  exec('def _tmp(): ' + cmd)
  _tmp()

def parse_phrase(code, pos):
  global start_pos
  start_pos = pos
  tree, pos = rules['phrase'].parse(code, pos)
  if tree:
    dbg.dprint('phrase', 'Successful phrase parse:')
    _debug_print(tree)
    parse_info.attempts = []
  return tree, pos

def or_rule(name, or_list, mode=''):
  dbg.dprint('public', 'or_rule(%s, %s, %s)' % (name, `or_list`, `mode`))
  return _add_rule(OrRule(name, or_list), mode)

def seq_rule(name, seq, mode=''):
  dbg.dprint('public', 'seq_rule(%s, %s, %s)' % (name, `seq`, `mode`))
  return _add_rule(SeqRule(name, seq), mode)

def false_rule(name, mode=''):
  dbg.dprint('public', 'false_rule(%s, %s)' % (name, `mode`))
  return _add_rule(FalseRule(name), mode)

def iterate(filename):
  global parse_info
  parse_info = Object()
  parse_info.attempts = []
  f = open(filename)
  code = f.read()
  f.close()
  _get_line_starts(code)
  parse_info.code = code
  pos = 0
  tree, pos = parse_phrase(code, pos)
  while tree:
    yield tree
    tree, pos = parse_phrase(code, pos)
  if pos < len(code):
    if 'main_attempt' in parse_info:
      pos = parse_info.main_attempt['fail_pos']
    line_num, char_offset = _get_line_of_byte_index(pos)
    error_fmt = 'Parsing failed on line %d, character %d'
    raise ParseError(error_fmt % (line_num, char_offset))

def runfile(filename):
  try:
    for tree in iterate(filename):
      pass
  except ParseError:
    _print_parse_failure()
    raise

# TODO Rename opts to params everywhere in this file.
def push_mode(name, params={}):
  dbg.dprint('public', '    push_mode(%s, %s)' % (`name`, `params`))
  _push_mode(name, params)

def pop_mode():
  global rules, mode, modes
  if len(modes) == 1:
    dbg.dprint('error',
           "Grammar error: pop_mode() when only global mode on the stack")
    exit(1)
  old_mode = modes.pop()
  # Refresh rules if we're at the global context.
  if len(modes) == 1: _push_mode('', modes.pop().__dict__)
  mode = modes[-1]
  rules = mode.rules
  dbg.dprint('public', '    pop_mode(_); %s -> %s' % (`old_mode.id`, `mode.id`))

def error(msg):
  dbg.dprint('error', 'Error: ' + msg)
  exit(1)


#------------------------------------------------------------------------------
#  Internal functions.
#------------------------------------------------------------------------------

def _get_line_starts(code):
  global line_starts
  line_starts = []
  pos = code.find('\n')
  while pos > 0:
    line_starts.append(pos)
    pos = code.find('\n', pos + 1)

def _get_line_of_byte_index(byte_idx):
  # We send in byte_idx - 1 since bisect returns the first list index *after*
  # all list indices with values <= what we send in.
  line_starts_idx = bisect.bisect(line_starts, byte_idx - 1)
  line_start_byte = line_starts[line_starts_idx - 1] if line_starts_idx else 0
  char_offset = byte_idx - line_start_byte
  return line_starts_idx + 1, char_offset  # These are 1-indexed coordinates.

# TODO Maybe push_mode should not be public?
def _push_mode(name, params):
  global rules, mode, modes
  mode = Object()
  if len(modes): mode.__dict__.update(modes[-1].__dict__)
  mode.id = name
  mode.rules = modes[-1].rules.copy() if len(modes) else {}
  mode.rules.update(all_rules[name])
  rules = mode.rules
  modes.append(mode)
  _set_mode_params(params)

def _set_mode_params(params):
  global mode
  protected_keys = ['id', 'rules']
  params = {k: params[k] for k in params if k not in protected_keys}
  mode.__dict__.update(params)

def _src(obj):
  if type(obj) == str: return obj
  elif type(obj) == tuple: return _src(obj[0])
  elif type(obj) == list: return ''.join([_src(elm) for elm in obj])
  elif isinstance(obj, Rule): return obj.src()
  else: dbg.dprint('error', "Error: unexpected obj type '%s' in _src" % type(obj))

def _dbg_parse_start(name, code, pos):
  m = ' <%s>' % mode.id if len(mode.id) else ''
  dbg.dprint('parse', '%s%s parse at """%s"""' % (name, m, `code[pos: pos + 30]`))

def _debug_print(obj, indent='  ', seq_item=None):
  if isinstance(obj, Rule):
    obj.debug_print(indent)
  elif seq_item and seq_item.startswith('-|'):
    dbg.dprint('tree', '%s ' % seq_item, end='')
    _debug_print(obj, indent)
  elif seq_item:
    # TODO Improve how this works for mode results.
    val = '[...]' if type(obj) is list else `obj`
    dbg.dprint('tree', '%s -> %s' % (seq_item, val))
  elif type(obj) == list:
    dbg.dprint('tree', '')
    for i in obj:
      dbg.dprint('tree', indent, end='')
      _debug_print(i, indent + '  ')
  else:
    dbg.dprint('tree', '%s' % `obj`)

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
  dbg.dprint('temp', 's before decode is %s' % `s`)
  s = s.decode('string_escape')

  a = code[pos:pos + 20]
  m = re.match(s, code[pos:], re.MULTILINE)
  if m:
    dbg.dprint('temp', 're.match(%s, %s, re.M) gives %s' % (`s`, `a`, `m.group(0)`))

  m = re.match(s, code[pos:], re.MULTILINE)
  if m:
    num_grp = len(m.groups()) + 1
    val = m.group(0) if num_grp == 1 else m.group(*tuple(range(num_grp)))
    return val, pos + len(m.group(0))
  # Parse fail. Record things for error reporting.

  parse_stack.append(s)
  global err_pos, err_expected
  if pos > err_pos: err_expected, err_pos = s, pos
  _store_parse_attempt(pos)
  parse_stack.pop()

  return None, pos

def _store_parse_attempt(pos):
  attempt = Object()
  attempt.stack = parse_stack[:]
  attempt.start_pos = start_pos
  attempt.fail_pos = pos
  parse_info.attempts.append(attempt)
  if 'main_attempt' not in parse_info or parse_info.main_attempt.fail_pos < pos:
    parse_info.main_attempt = attempt

def _print_parse_failure():
  dbg.print_parse_failure(parse_info)

def _setup_base_rules():
  r = seq_rule('phrase', ["'>:'", '"[^\\n]*\\n"'], mode='')
  r.add_fn('parsed', ' parse.command(tokens[1])\n')
  push_mode('')
  runfile(os.path.join(os.path.dirname(__file__), 'base_grammar.cmd.water'))


#------------------------------------------------------------------------------
#  Set up initial state.
#------------------------------------------------------------------------------

def _setup():
  global parse_info, env, parse
  dbg.topics = []
  env = Object()
  parse = sys.modules[__name__]
  _setup_base_rules()
  dbg.topics = ['parse']  # Choices: 'public', 'parse'; see dbg.py for others.

_setup()
