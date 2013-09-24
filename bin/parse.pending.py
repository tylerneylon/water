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

# Each entry is a stack of prefixes. E.g. entry ['a', 'b', 'c'] means to look
# for the prefix 'abacaba'. More commonly, [" *", '+'] means " *\+ *".
prefixes = [[]]

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

# Temp debug stuff.
# TODO Make these available via command-line args.
show_extra_dbg = False

#------------------------------------------------------------------------------
#  Define classes.
#------------------------------------------------------------------------------

class AttrStr(str): pass  # A string that can have attributes.

class AttrTuple(tuple): pass  # A tuple that can have attributes.

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

  def __init__(self, name, seq, list_of=None):
    self.name = name
    self.seq = seq
    self.list_of = list_of
    Rule.__init__(self)
    self._add_fn('str', ' return self.src()')

  def __getattribute__(self, name):
    try:
      return Rule.__getattribute__(self, name)
    except AttributeError:
      d = Rule.__getattribute__(self, '__dict__')
      if name in d['pieces']: return d['pieces'][name]
      if d['name'] == name: return self
      t = d['tokens']
      if len(t) == 1: return t[0].__getattribute__(name)
      raise

  def src(self, incl_prefix=True):
    parts = [src(t, incl_prefix or i) for i, t in enumerate(self.tokens)]
    return ''.join(parts)

  def parse_mode(self, mode_name, it):
    dbg.dprint('parse', '%s parse_mode %s' % (self.name, mode_name))
    init_num_modes = len(modes)
    params = {}
    push_mode(mode_name)
    if mode_name.may_have_params and 'mode_params' in self.__dict__:
      _set_mode_params(self.mode_params())
    mode_result = []
    # A mode is popped from either a successful parse or a |: clause. The |:
    # is a special case where the returned tree is None, but it is not a parse
    # error; that case is the reason for the if clause after this while loop.
    while True:
      tree = _rule('phrase').parse(it)
      if len(modes) == init_num_modes: break
      if tree is None:
        pop_mode()
        return None
      mode_result.append(tree)
    if tree: mode_result.append(tree)
    if not mode_name.may_have_params and len(mode_result) == 0: return None
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
        val = self.parse_mode(val, it)
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
      if show_extra_dbg:
        print('After subst, text is:')
        print(it.text())
      tree = self.parse(it)
    substs = saved_substs
    return tree if self.list_of is None else _list_of(self)

  def child(self):
    c = SeqRule(self.name, self.seq)
    c.__dict__ = self.__dict__.copy()
    c._bind_all_methods()
    return c

class OrRule(Rule):

  def __init__(self, name, or_list, list_of=None):
    self.name = name
    self.or_list = or_list
    self.list_of = list_of
    Rule.__init__(self)

  def __getattribute__(self, name):
    try:
      return Rule.__getattribute__(self, name)
    except AttributeError:
      d = Rule.__getattribute__(self, '__dict__')
      if 'result' in d: return d['result'].__getattribute__(name)
      raise

  # We need this because result could be a non-Rule without its own src method.
  def src(self, incl_prefix=True):
    return src(self.result, incl_prefix)

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
        return self if self.list_of is None else _list_of(self)
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

  def src(self, incl_prefix=True): return ''

class ParseError(Exception):
  pass

#------------------------------------------------------------------------------
#  Public functions.
#------------------------------------------------------------------------------

def command(cmd):
  # We wrap cmd as a function body to make it easier to deal with user indents.
  exec('def _tmp(): ' + cmd)
  _tmp()

def parse_string(s):
  # I'm leaving in a {push,pop}_mode pair to show where we can
  # alter the mode if we wanted to.
  if show_extra_dbg:
    print('parse_string:')
    print(s)
  if False: push_mode('')
  line_nums = dbg.LineNums(s)
  it = iterator.Iterator(s)
  result = []
  while True:
    tree = _rule('phrase').parse(it)
    if not tree or it.text_pos == len(it.text()): break
    result.append(tree)
  if False: pop_mode('')
  if it.text_pos < len(it.text()):
    pos = it.orig_pos()
    line_num, char_offset = line_nums.line_num_and_offset(pos)
    error_fmt = 'Parsing failed on line %d, character %d'
    raise ParseError(error_fmt % (line_num, char_offset))
  return result

# The input is an Iterator that is updated to point to the next parse point
# if the parse is successful. The return value is:
#  * a parse tree   on success
#  * None           if there was a parse error.
def parse_phrase(it):
  global parse_info
  parse_info.phrase_start_pos = it.orig_pos()
  tree = _rule('phrase').parse(it)
  if tree:
    dbg.dprint('phrase', 'Successful phrase parse:')
    dbg.print_tree(tree)
    parse_info.attempts = []
  return tree

def or_rule(name, or_list, mode='', list_of=None):
  dbg.dprint('public', 'or_rule(%s, %s, %s, %s)' %
             (name, `or_list`, `mode`, `list_of`))
  return _add_rule(OrRule(name, or_list, list_of), mode)

def seq_rule(name, seq, mode='', list_of=None):
  dbg.dprint('public', 'seq_rule(%s, %s, %s, %s)' %
             (name, `seq`, `mode`, `list_of`))
  return _add_rule(SeqRule(name, seq, list_of), mode)

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

def pop_mode(outgoing_mode=None):
  global rules, mode, modes
  if len(modes) == 1:
    dbg.dprint('error',
           "Grammar error: pop_mode() when only global mode on the stack")
    exit(1)
  old_mode = modes.pop()
  if outgoing_mode is not None and old_mode.id != outgoing_mode:
    dbg.dprint('error', 'pop_mode(%s) called from mode %s' %
               (outgoing_mode, `old_mode.id`))
  # Refresh rules if we're at the global context.
  if len(modes) == 1: _push_mode('', modes.pop().__dict__)
  mode = modes[-1]
  rules = mode.rules
  dbg.dprint('public', '    pop_mode(_); %s -> %s' % (`old_mode.id`, `mode.id`))

def push_prefix(prefix, overwrite=False):
  global prefixes
  dbg.dprint('public', 'push_prefix(%s, %s)' % (`prefix`, `overwrite`))
  prefix = [] if prefix is None else [prefix]
  if not overwrite: prefix = prefixes[-1] + prefix
  prefixes.append(prefix)

def pop_prefix():
  global prefixes
  dbg.dprint('public', 'pop_prefix()')
  prefixes.pop()

def src(obj, incl_prefix=True):
  if type(obj) is str: return obj
  p, s = _prefix_if_leaf(obj)
  p = src(p) if incl_prefix and p else ''
  if type(obj) == AttrStr: return p + obj + src(s)
  elif type(obj) == AttrTuple: return p + obj[0] + src(s)
  elif type(obj) == tuple: return src(obj[0])  # TODO needed?
  elif type(obj) == list:
    return ''.join([src(j, incl_prefix or i != 0) for i, j in enumerate(obj)])
  elif isinstance(obj, Rule): return obj.src(incl_prefix)
  else: dbg.dprint('error', "Error: unexpected obj type '%s' in src" % type(obj))

# TODO Get this working. This is hard to work well before prefixes are properties
#      of leaf-level strings (I think). I plan to revisit this after prefixes are
#      stored in the new way. Start by making sure 57.water works.
def val(obj):
  return src(obj, incl_prefix=False)

def is_empty(obj):
  if type(obj) == BoolRule: return True
  if type(obj) == OrRule: return is_empty(obj.result)
  if type(obj) == SeqRule:
    if len(obj.tokens) != 1: return False
    return is_empty(obj.tokens[0])
  return False

def error(msg):
  dbg.dprint('error', 'Error: ' + msg)
  exit(1)

#------------------------------------------------------------------------------
#  Internal functions.
#------------------------------------------------------------------------------

def _prefix_if_leaf(tree_node):
  if type(tree_node) != AttrStr and type(tree_node) != AttrTuple: return ('', '')
  if 'prefix' not in tree_node.__dict__: return ('', '')
  suffix = tree_node.suffix if 'suffix' in tree_node.__dict__ else ''
  return (tree_node.prefix, suffix)

def _add_subst(rule_or_text):
  global substs
  if isinstance(rule_or_text, str) or isinstance(rule_or_text, Rule):
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
  mode._pending_rules = {}
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

def _add_rule(rule, mode_name):
  # TODO Clean this up when refresh-rules-on-mode-pop is far enough along.
  global mode
  if mode_name not in all_rules: all_rules[mode_name] = {}
  all_rules[mode_name][rule.name] = rule
  mode._pending_rules.setdefault(mode_name, {})[rule.name] = rule
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
  should_pop_prefix = False
  is_negated = False
  def _end(val, labels):
    if is_negated: val = None if val else all_rules['']['Empty']
    if should_pop_prefix: pop_prefix()
    return val, labels
  dbg.dprint('temp', 'item=%s' % (item if isinstance(item, str) else `item`))
  if type(item) is tuple:  # It's an item with a prefix change.
    prefix_chng = None if item[0] == '.' else item[0][1:-1]  # Drop the parens.
    overwrite = (item[0] == '.')
    if prefix_chng and prefix_chng.startswith('prefix='):
      overwrite = True
      prefix_chng = prefix_chng[len('prefix='):]
    push_prefix(prefix_chng, overwrite)
    should_pop_prefix = True
    item = item[1]
  c = item[0]
  if c == ':': return _end(_CommandStr(item[1:]), None)
  if c == '!':
    is_negated = True
    item = item[1:]
    c = item[0]
  if c == '.':
    # TODO This can only happen with a '.-mode_name' item, which is planned to
    #      be replaced by prefix_changes at mode starts. Get rid of this case
    #      both here and in layer1.water on the mode_result rule definition -
    #      that is, after we can handle the new mode-start prefix_changes.
    #print('ERROR: This case was supposed to be gone')
    #import pdb; pdb.set_trace()
    item = item[1:]
    c = item[0]
    push_prefix(None, overwrite=True)
    should_pop_prefix = True
  item, label = _find_label(item)
  labels = [label] if label else []
  if c in ['-', '=']:
    mode_name = _ModeName(item[1:])
    mode_name.may_have_params = (c == '-')
    return _end(mode_name, labels)
  if c == "'": val = _parse_exact_str(item[1:-1], it)
  elif c == '"':
    re = item[1:-1] % mode
    dbg.dprint('temp', 're=%s' % `re`)
    val = _parse_exact_re(re, it)
  else:
    val = _rule(item).parse(it)
    if val: labels.append(item)
  return _end(val, labels)

def _parse_exact_str(s, it):
  to_escape = list("+()|*.[]?^")
  for e in to_escape: s = s.replace(e, "\\" + e)
  return _parse_exact_re(s, it)

# Returns val, new_pos; val is the match on success or None otherwise.
def _direct_parse(s, it):
  m = re.match(s, it.tail(), re.MULTILINE)
  if m is None: return None
  it.move(len(m.group(0)))
  return m

# TODO If a prefix parse fails, we need to back up the iterator.
def _parse_prefix(it, prefix_list=None):
  global prefixes
  if prefix_list is None: prefix_list = prefixes[-1]
  if not prefix_list: return ''
  prefixes.append(prefix_list[:-1])
  def done(v):
    prefixes.pop()
    dbg.dprint('temp', '_parse_prefix will return %s based on prefix stack %s' % (`v`, `prefix_list`))
    return v
  val, labels = _parse_item(prefix_list[-1], it)
  if val is None: return done(None)
  suffix = _parse_prefix(it)
  if suffix is None: val = None
  else: val.suffix = suffix
  return done(val)
 
def _parse_exact_re(s, it):
  prefix = _parse_prefix(it)
  if prefix is not None:
    s = s.decode('string_escape')
    m = _direct_parse(s, it)
    if m:
      num_grp = len(m.groups()) + 1
      val = m.group(0) if num_grp == 1 else m.group(*tuple(range(num_grp)))
      val = AttrTuple(val) if type(val) is tuple else AttrStr(val)
      val.prefix = prefix
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
  # TODO Clean up the mode handling here once refresh-rules-on-mode-pop is done.
  push_mode('')  # Initialize the global mode.
  r = seq_rule('phrase', ["'>:'", '"[^\\n]*\\n"'], mode='')
  r.add_fn('parsed', ' parse.command(tokens[1])\n')
  push_mode('')  # Force rules to be reloaded.
  pop_mode()
  runfile(os.path.join(os.path.dirname(__file__), 'base_grammar.water'))

# Returns a list of rules of type elt_type, or None if obj cannot be
# built of such a list. If elt_type is None, then obj.list_of is used
# as the elt_type.
def _list_of(obj, elt_type=None):
  if elt_type is None: elt_type = obj.list_of
  def _apply_to_items(items):
    mapped_items = [_list_of(i, elt_type) for i in items]
    # Propagate up any None values indicating failure.
    if any(map(lambda x: x is None, mapped_items)): return None
    return sum(mapped_items, [])
  if type(obj) is list: return _apply_to_items(obj)
  if obj.name == elt_type: return [obj]
  if obj.name == 'Empty': return []
  if isinstance(obj, OrRule): return _list_of(obj.result, elt_type)
  if isinstance(obj, SeqRule): return _apply_to_items(obj.tokens)
  return None

def _rule(rule_name):
  mode_index = len(modes) - 1
  while mode_index >= 0:
    rules = all_rules[modes[mode_index].id]
    if rule_name in rules: return rules[rule_name]
    mode_index -= 1
  return None

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
