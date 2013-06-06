#
# rules.py
#
# Defines Rule, OrRule, SeqRule, and FalseRule.
#
# Rule is meant to only be a base class - not instantiated directly.
#
# Instances of {Or,Seq,False}Rule can represent general grammar rules
# to be parsed.
#
# Instances of {Or,Seq}Rule can also represent a successful parse of
# a subset of a src string.
#

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

