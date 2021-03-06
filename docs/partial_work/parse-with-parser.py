#!/usr/bin/python
#
# parse.py
#
# Code to parse, compile, and modify a language.
#
# Public interface, usable at compile-time or by other modules:
#
#  * env, a global Object for all user-based compile-time variables.
#
#  * command(cmd)                     Run Python code in compile-time env.
#  * parse_phrase(src, pos)           Get next phrase syntax tree from src.
#
#    The next three methods add new rules to the grammar:
#  * or_rule(name, or_list, mode='')
#  * seq_rule(name, seq, mode='')
#  * bool_rule(name, bool_val, mode='')
#
#    Any rule also accepts the useful method:
#  * rule.add_fn(fn_name, fn_code)
#
#  * iterate(filename)                Get all phrase syntax trees in a for loop.
#  * runfile(filename)                Parse and run the given file.
#  * push_mode(name, params={})       Push a mode to the mode stack.
#  * pop_mode()                       Pop a mode from the mode stack.
#  * error(msg)                       Print an error message and quit.
#  
#

# TODO Items:
#    * Add 'public' output for >: commands.
#

from __future__ import print_function

import os
import re
import sys
import types

import dbg
import iterator
import run

# Globals.

all_rules = {'': {}}
rules = None
modes = []
mode = None
parse = None
env = None

prefix = None
user_prefix = False
parse_stack = []

substs = []  # For use by add_subst.

# parse_info stores parse attempt data so we can display human-friendly error
# information that simplifies debugging grammars and syntax errors alike.
#
# parse_info.attempts = [list of parse_attempt Objects]
# parse_info.main_attempt = the parse_attempt we suspect was intended
# parse_info.code = the code string being parsed
# parse_info.phrase_start_pos = the last pos where a phrase parse began
#
# attempt.stack = list of rule names in the attempt, phrase-first
# attempt.start_pos = byte index of where parse stack began parsing
# attempt.fail_pos = byte index of where the last stack token mismatched
#
# TODO Pull this out into a modules & class that does not depend on parse.
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

# TODO NEXT
# Plan ahead: For every major class here, figure out which globals it
# uses, and think carefully about how to refactor data dependencies nicely.
class Parser(object):
  def __init__(self, filename):
    # TODO This is not done yet.
    #      We probably need many more self.variables.
    self.all_rules = {'': {}}
    self.rules = None
    self.modes = []
    self.mode = None
    self.env = None
    self.prefix = None
    self.user_prefix = None  # TODO Rename to is_user_prefix.
    self.parse_stack = []
    self.substs = []
    self.parse_info = Object()
    self.parse_info.attempts = []
    f = open(filename)
    code = f.read()
    f.close()
    line_nums = dbg.LineNums(code)
    parse_info.code = code
    self.it = iterator.Iterator(code)

  def parse_phrase(self):
    self.user_prefix = False
    self.parse_info.phrase_start_pos = self.it.orig_pos()
    tree = self.rules['phrase'].parse(self.it)
    if tree:
      dbg.dprint('phrase', 'Successful phrase parse:')
      dbg.print_tree(tree)
      parse_info.attempts = []
    return tree

  def run(self):
    while True:
      try:
        tree = self.parse_phrase()
        if tree is None: return
      except ParseError:
        _print_parse_failure()
        raise

class Rule(Object):

  def __init__(self):
    self._unbound_methods_ = {}

  def __str__(self): return self.str()

  def _run_fn(self, fn_name, fn_code):
    # We send in lo as kwargs because exec uses the local context strangely:
    # http://stackoverflow.com/a/1463370
    # http://stackoverflow.com/a/2906198
    lo = {}
    if 'tokens' in self: lo['tokens'] = self.tokens
    if 'or_index' in self: lo['or_index'] = self.or_index
    if 'pieces' in self:
      p = self.pieces
      lo.update({k: p[k][0] if len(p[k]) == 1 else p[k] for k in p})
      # Keep mode result as a list, even if it has 1 element.
      if 'mode_result' in p: lo['mode_result'] = p['mode_result']
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

  def parse(self, it):
    parse_stack.append(self.name)
    tree = self.child().inst_parse(it)
    parse_stack.pop()
    return tree

class SeqRule(Rule):

  def __init__(self, name, seq):
    self.name = name
    self.seq = seq
    Rule.__init__(self)
    self._add_fn('str', ' return self.src()')

  def src(self):
    return ''.join([src(t) for t in self.tokens])

  # Expects self.mode_id to be set, and will push that mode.
  def parse_mode(self, it):
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
      tree = rules['phrase'].parse(it)
      if len(modes) == init_num_modes: break
      if tree is None: return None
      mode_result.append(tree)
    if tree: mode_result.append(tree)
    self.pieces['mode_result'] = mode_result
    return mode_result

  def inst_parse(self, it):
    _dbg_parse_start(self.name, it)
    self.start_text_pos = it.text_pos
    self.start_pos = it.orig_pos()
    self.tokens = []
    self.pieces = {}
    for item in self.seq:
      val, labels = _parse_item(item, it)
      if isinstance(val, _ModeName):
        dbg.dprint('parse', '%s parse reached %s' % (self.name, item))
        self.mode_id = val
        val = self.parse_mode(it)
      if val is None:
        dbg_fmt = '%s parse failed at token %s ~= code %s'
        dbg_snippet = it.text()[it.text_pos:it.text_pos + 10]
        dbg.dprint('parse', dbg_fmt % (self.name, item, `dbg_snippet`))
        it.text_pos = self.start_text_pos
        return self._end_parse(None, it)
      self.tokens.append(val)
      for label in labels: self.pieces.setdefault(label, []).append(val)
    return self._end_parse(self, it)

  def _end_parse(self, tree, it):
    global substs
    self.end_pos = it.orig_pos()
    if tree is None: return tree
    # TODO Think of a way to do this more cleanly. Right now run._state is
    # awkwardly set from both parse and run.
    # For examle, maybe a command could set up its code_block as the body of an
    # add_code fn, and then call run.add on itself.
    run._state = {'start': self.start_pos, 'end': self.end_pos}
    dbg.dprint('parse', '%s parse succeeded' % self.name)
    saved_substs = substs
    substs = []
    if 'parsed' in self.__dict__: self.parsed()
    if substs:
      # TODO(future): When I set up caching, I can update the cache about rules
      #               in the substs list (and add that info to the list).
      it.replace([self.start_text_pos, it.text_pos], ''.join(substs))
      it.text_pos = self.start_text_pos
      # The next two lines are very useful for debugging substitutions.
      #print('After subst, text is:')
      #print(it.text())
      tree = self.parse(it)
    substs = saved_substs
    return tree

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

  def inst_parse(self, it):
    _dbg_parse_start(self.name, it)
    self.start_pos = it.orig_pos()
    for index, item in enumerate(self.or_list):
      val, labels = _parse_item(item, it)
      if isinstance(val, _CommandStr):
        dbg.dprint('parse', '%s parse finishing as or_else clause' % self.name)
        self.run_code(val)
        self.end_pos = it.orig_pos()
        return None
      if val:
        self.result = val
        # We want to delegate the tokens property to val iff val is a Rule.
        if not isinstance(val, Rule): self.tokens = [val]
        self.or_index = index
        self.end_pos = it.orig_pos()
        dbg.dprint('parse', '%s parse succeeded as %s' % (self.name, item))
        if 'parsed' in self.__dict__: self.parsed()
        return self
    dbg.dprint('parse', '%s parse failed' % self.name)
    return None

  def child(self):
    c = OrRule(self.name, self.or_list)
    c.__dict__ = self.__dict__.copy()
    c._bind_all_methods()
    return c

class BoolRule(Rule):

  def __init__(self, name, bool_val):
    self.name = name
    self.bool_val = bool_val

  def parse(self, it):
    return self if self.bool_val else None

class ParseError(Exception):
  pass

#------------------------------------------------------------------------------
#  Public functions.
#------------------------------------------------------------------------------

def command(cmd):
  # We wrap cmd as a function body to make it easier to deal with user indents.
  exec('def _tmp(): ' + cmd)
  _tmp()

# The input is an Iterator that is updated to point to the next parse point
# if the parse is successful. The return value is:
#  * a parse tree   on success
#  * None           if there was a parse error.
def parse_phrase(it):
  global parse_info, user_prefix
  user_prefix = False
  parse_info.phrase_start_pos = it.orig_pos()
  tree = rules['phrase'].parse(it)
  if tree:
    dbg.dprint('phrase', 'Successful phrase parse:')
    dbg.print_tree(tree)
    parse_info.attempts = []
  return tree

def or_rule(name, or_list, mode=''):
  dbg.dprint('public', 'or_rule(%s, %s, %s)' % (name, `or_list`, `mode`))
  return _add_rule(OrRule(name, or_list), mode)

def seq_rule(name, seq, mode=''):
  dbg.dprint('public', 'seq_rule(%s, %s, %s)' % (name, `seq`, `mode`))
  return _add_rule(SeqRule(name, seq), mode)

def bool_rule(name, bool_val, mode=''):
  dbg.dprint('public', 'bool_rule(%s, %s, %s)' % (name, `bool_val`, `mode`))
  return _add_rule(BoolRule(name, bool_val), mode)

def prepend_to_or(name, or_name, mode=''):
  dbg.dprint('public', 'prepend_to_or(%s, %s, %s)' % (name, or_name, `mode`))
  all_rules[mode][name].or_list.insert(0, or_name)

def add_subst(*args):
  for arg in args: _add_subst(arg)

def iterate(filename):
  global parse_info
  parse_info = Object()
  parse_info.attempts = []
  f = open(filename)
  code = f.read()
  f.close()
  line_nums = dbg.LineNums(code)
  parse_info.code = code
  it = iterator.Iterator(code)
  tree = parse_phrase(it)
  while tree:
    yield tree
    tree = parse_phrase(it)
  if it.text_pos < len(it.text()):
    pos = it.orig_pos()
    if 'main_attempt' in parse_info:
      pos = parse_info.main_attempt['fail_pos']
    line_num, char_offset = line_nums.line_num_and_offset(pos)
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

def set_prefix(new_prefix, from_user=True):
  global prefix, user_prefix
  if user_prefix and not from_user: return
  prefix = new_prefix
  if from_user: user_prefix = True

def src(obj):
  if type(obj) == str: return obj
  elif type(obj) == tuple: return src(obj[0])
  elif type(obj) == list: return ''.join([src(elm) for elm in obj])
  elif isinstance(obj, Rule): return obj.src()
  else: dbg.dprint('error', "Error: unexpected obj type '%s' in src" % type(obj))

def error(msg):
  dbg.dprint('error', 'Error: ' + msg)
  exit(1)

#------------------------------------------------------------------------------
#  Internal functions.
#------------------------------------------------------------------------------

def _add_subst(rule_or_text):
  global substs
  if type(rule_or_text) == str or isinstance(rule_or_text, Rule):
    substs.append(src(rule_or_text))
  else:
    error('Illegal input to parse.add_subst; type=%s' % type(rule_or_text))

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

def _dbg_parse_start(name, it):
  m = ' <%s>' % mode.id if len(mode.id) else ''
  text_str = it.text()[it.text_pos:it.text_pos + 30]
  dbg.dprint('parse', '%s %s%s parse at """%s"""' % (`parse_stack`, name, m, `text_str`))

def _add_rule(rule, mode):
  if mode not in all_rules: all_rules[mode] = {}
  all_rules[mode][rule.name] = rule
  return rule

# This is a way to pass around a string with a way to check that it's meant to
# be used as a mode name. Built for use within _parse_item.
class _ModeName(str): pass

# This is a way to indicate a command found in an item.
class _CommandStr(str): pass

# Returns label_free_part, label; label may be None if it's not there.
def _find_label(item):
  must_be_after = 0
  # Don't count a : found within a string.
  if item[0] in ["'", '"']: must_be_after = item.rfind(item[0])
  label_start = item.rfind(':') + 1
  if label_start <= must_be_after: return item, None
  return item[:label_start - 1], item[label_start:]

# Returns val, labels; val is the parsed value, labels are the labels to be used
# in the calling rule's pieces list. val is None on parse failure, and is a
# _ModeName string when a mode name is found -- in that case, the actual parsing
# of the mode is not performed, and is up to the caller to complete.
def _parse_item(item, it):
  global prefix
  saved_prefix = prefix
  is_negated = False
  def _end(val, labels):
    if is_negated: val = None if val else rules['Empty']
    set_prefix(saved_prefix, from_user=False)
    return val, labels
  dbg.dprint('temp', 'item=%s' % item)
  c = item[0]
  if c == ':': return _end(_CommandStr(item[1:]), None)
  if c == '!':
    is_negated = True
    item = item[1:]
    c = item[0]
  if c == '.':
    item = item[1:]
    c = item[0]
    prefix = None
  item, label = _find_label(item)
  labels = [label] if label else []
  if c == '-': return _end(_ModeName(item[1:]), labels)
  if c == "'": val = _parse_exact_str(item[1:-1], it)
  elif c == '"':
    re = item[1:-1] % mode
    dbg.dprint('temp', 're=%s' % `re`)
    val = _parse_exact_re(re, it)
  else:
    val = rules[item].parse(it)
    if val: labels.append(item)
  return _end(val, labels)

def _parse_exact_str(s, it):
  to_escape = list("+()|*.[]")
  for e in to_escape: s = s.replace(e, "\\" + e)
  return _parse_exact_re(s, it)

# Returns val, new_pos; val is the match on success or None otherwise.
def _direct_parse(s, it):
  m = re.match(s, it.tail(), re.MULTILINE)
  if m is None: return None
  it.move(len(m.group(0)))
  return m

def _parse_exact_re(s, it):
  global prefix
  if prefix is not None: m = _direct_parse(prefix, it)
  s = s.decode('string_escape')
  m = _direct_parse(s, it)
  if m:
    num_grp = len(m.groups()) + 1
    val = m.group(0) if num_grp == 1 else m.group(*tuple(range(num_grp)))
    return val
  # Parse fail. Record things for error reporting.
  parse_stack.append(s)
  _store_parse_attempt(it)
  parse_stack.pop()
  return None

def _store_parse_attempt(it):
  global parse_info
  pos = it.orig_pos()
  attempt = Object()
  attempt.stack = parse_stack[:]
  attempt.start_pos = parse_info.phrase_start_pos
  attempt.fail_pos = pos
  parse_info.attempts.append(attempt)
  if 'main_attempt' not in parse_info or parse_info.main_attempt.fail_pos <= pos:
    parse_info.main_attempt = attempt

def _print_parse_failure():
  dbg.print_parse_failure(parse_info)

def _setup_base_rules():
  r = seq_rule('phrase', ["'>:'", '"[^\\n]*\\n"'], mode='')
  r.add_fn('parsed', ' parse.command(tokens[1])\n')
  push_mode('')
  runfile(os.path.join(os.path.dirname(__file__), 'base_grammar.water'))

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
