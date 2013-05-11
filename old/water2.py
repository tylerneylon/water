#!/usr/bin/python

import re
import sys

base_tokens = [
               ['', r'^>tokens', 'push:token_def_mode'],
               ['', r'^>rules', 'push:rule_def_mode']
              ]
base_rules = {}

token_def_tokens = [
                    ['', r'^(\S| \S)', 'pop'],
                    ['\'list', r'^  list'],
                    ['%token_name', r'  \S+']
                   ]
token_def_rules = {
                   'statement' : ['or', 'token_list', 'named_token'],
                   'token_list' : ['rules', '\'list', 'token+'],
                   'token+' : ['rules', '%token_name', 'token*'],
                   'token*' : ['or', 'token+', '%nothing'],
                   # TODO The parameter for a regex here should be able to accept spaces inside quotes.
                   'named_token' : ['rules', '%token_name', '%token_name']
                  }

rule_def_rules = [
                  ['', r'->'],
                  ['', r'|']
                 ]
rule_def_tokens = {
                   '' : []  # TODO HERE
                  }

mode_dict = {'base_mode'      : [base_tokens, base_rules],
             'token_def_mode' : [token_def_tokens, token_def_rules],
             'rule_def_mode'  : [rule_def_tokens, rule_def_rules]
            }

              ['', r'->'],
              ['', r'|'],
              ['%token', r'\S+']
             ]

rule_dict = {'line' : ['or', 'tokens_start', 'rules_start', 'statement'],
             'tokens_start' : ['rules', 
             'rules_start' : []
            }


token_list = [['', r'for'],
              ['', r'print'],
              ['\'(', r'\('],
              ['\')', r'\)'],
              ['', r';'],
              ['', r'<'],
              ['', r'='],
              ['\'+=', r'\+='],
              ['%identifier', r'\w']]

rule_dict = {'statement' : ['or', 'assignment', 'for_loop', 'print_statement'],
             'assignment' : ['or', 'direct_assignment', 'incremental_assignment'],
             'direct_assignment' : ['rules', '%identifier', '\'=', 'expression'],
             'incremental_assignment' : ['rules', '%identifier', '\'+=', 'expression'],
             'expression' : ['or', '%identifier', '%number'],
             'for_loop' : ['rules', '\'for', '\'(', 'statement', '\';', 'conditional', '\';', 'statement', '\')', 'statement'],
             'conditional' : ['rules', 'expression', '\'<', 'expression'],
             'print_statement' : ['rules', '\'print', '%identifier']
            }

# TODO For now I'll explicitly build functions to turn a parse tree into a python string.
#      In the future, I will pull these out so they are easy to specify in a .water file.
def tree_to_str(t):
  #import pdb; pdb.set_trace()
  #print "tree_to_str( <type %s> <len %d> )" % (type(t), len(t))
  if type(t) is tuple: return t[1]
  if t[0] == 'direct_assignment':
    return ' '.join(map(tree_to_str, t[1:]))
  elif t[0] == 'incremental_assignment':
    return ' '.join(map(tree_to_str, t[1:]))
  elif t[0] == 'for_loop':
    init = tree_to_str(t[3])
    cond = tree_to_str(t[5])
    inc  = tree_to_str(t[7])
    body = tree_to_str(t[9])
    return "%s\nwhile %s:\n  %s\n  %s" % (init, cond, body, inc)
  elif t[0] == 'conditional':
    return ' '.join(map(tree_to_str, t[1:]))
  elif t[0] == 'print_statement':
    return ' '.join(map(tree_to_str, t[1:]))
  else: # This fall-through case is meant for 'or' rules.
    return tree_to_str(t[1])

def exec_statement_tree(t, ctx):
  exec tree_to_str(t) in ctx
  return ctx

# Attempt to parse the current context as rule specified in the context.
# The return value is (subtree, context) when the rule can be parsed, or None on failure. 
#
# grammar is
#   0 -> token list
#   1 -> rule list
# context is
#   0 -> black box for use by token peek and pop
#   1 ->
#   2 -> list (stack) of rules
# TODO Turn these objects into dictionaries with descriptive keys.
def parse_rule(grammar, context):
  rule_name = context[2][-1]
  token = token_peek(context[0])
  #print "parse_rule(next_tok=%s, rule stack=%s)" % (token, context[2])
  if (rule_is_token(rule_name)):
    is_match = (token[0] == rule_name)
    if is_match: token_pop(context[0])
    return debug_return((token, context) if is_match else None)
  else:
    rule = grammar[1][rule_name]
    if rule[0] == 'or':
      for subrule in rule[1:]:
        context[2].append(subrule)
        result = parse_rule(grammar, context)
        context[2].pop()
        if result:
          tree, context = result
          return debug_return(([rule_name, tree], context))
      return debug_return(None)
    elif rule[0] == 'rules':
      subtree = [rule_name]
      for subrule in rule[1:]:
        context[2].append(subrule)
        result = parse_rule(grammar, context)
        context[2].pop()
        if not result:
          pb = tokens_from_tree(subtree)
          #print "About to push back %s" % `pb`
          token_push_list(context[0], tokens_from_tree(subtree))
          #print "context[0] is now %s" % `context[0]`
          return debug_return(None)
        subtree.append(result[0])
      return debug_return((subtree, context))

def tokens_from_tree(tree):
  if type(tree) == tuple: return [tree]
  if type(tree) == str: return []
  # Otherwise it's a list.
  return sum(map(tokens_from_tree, tree), [])

def print_tree(tree, indent=0):
  if type(tree) is list:
    head = tree[0] if type(tree[0]) is str else `tree[0]`
    print "  " * indent + head + ":"
    for subtree in tree[1:]:
      print_tree(subtree, indent=(indent + 1))
  else:
    head = tree if type(tree) is str else `tree`
    print "  " * indent + head

# TODO TEMP DEBUG
def debug_return(x):
  #print "returning %s" % `x`
  return x

def rule_is_token(rule_name):
  return rule_name.startswith('%') or rule_name.startswith('\'')

# Token parsing functions.

def token_init(filename, token_list):
  f = open(filename, 'r')
  next_tokens = []
  return [f, next_tokens, token_list]

# t is a tokenizer
# TODO Make this a class.
def token_peek(t):
  if not t[1]: _token_parse_line(t)
  return t[1][0] if t[1] else None

def token_pop(t):
  if not t[1]: _token_parse_line(t)
  return t[1].pop(0) if t[1] else None

def token_push_list(t, l):
  t[1][0:0] = l

def _token_parse_line(t):
  if t[0].closed: return
  line = t[0].readline()
  if len(line) == 0:
    t[0].close()
    return
  t[1] = _tokenize_line(t[2], line)

def _tokenize_line(token_list, line):
  for token_def in token_list:
    m = re.match(token_def[1], line)
    if m:
      rest_of_line = line[m.end(0):]
      rest_of_tokens = _tokenize_line(token_list, rest_of_line)
      this_token = [(token_def[0], m.group(0))] if not token_def[0].startswith('_') else []
      return this_token + rest_of_tokens
  if len(line.strip()) > 0:
    sys.stderr.write("Unable to tokenize the line suffix \"%s\"\n" % line)
  return []


# main

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print "Usage: %s <water-file>" % sys.argv[0]
    exit(2)

  # Prepare the token list.
  for i in xrange(len(token_list)):
    token_def = token_list[i]
    if not token_def[0]: token_def[0] = "'" + token_def[1]
  token_list.append(['_whitespace', r'\s+'])

  t = token_init('sample1.water', token_list)

  grammar = [token_list, rule_dict]
  context = [t, None, ['statement']]

  ctx = {}
  for i in xrange(3):
    tree, context = parse_rule(grammar, context)
    #print "%s" % `tree`
    #print("=== Parse tree is ===")
    #print_tree(tree)
    #print("=== Code is ===")
    #print tree_to_str(tree)
    #print "tree_to_str gives:\n%s" % tree_to_str(tree)
    ctx = exec_statement_tree(tree, ctx)
