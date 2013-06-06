#!/usr/bin/python
#
# dbg.py
#
# Functions to handle debug output for project water.
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
# run        green     Strings sent to run fn
#

from __future__ import print_function
import sys

# This is either 'all' or a list of whitelisted dbg_topic names.
topics = 'all'

# This is a list of writable file-like objects which receive debug output.
# Only sys.stdout is in color.
dst = []

# If true, prints a number before every dprint statement.
# This can be useful for setting a breakpoint for a deterministic error.
showNums =   False  # Default: False
breakOnNum = None   # Default: None
_num = 0


# Set up cprint

try:
  from termcolor import colored
except:
  def _cprint(s, color=None): print(s)
  def colored(s, color=None): return s

# TODO Avoid setting a breakpoint if no output went to a tty?
def cprint(text, color=None, end='\n'):
  global _num, showNums, breakOnNum
  s = text + end
  _num += 1
  if showNums and end == '\n': s = str(_num) + ' ' + s
  for d in dst:
    if d.isatty(): s = colored(s, color)
    if d is sys.stdout and color == 'red':
      # red output is redirected to stderr from stdout.
      sys.stderr.write(s)
    else:
      d.write(s)
  if _num == breakOnNum:
    import pdb; pdb.set_trace()

#------------------------------------------------------------------------------
#  Public functions.
#------------------------------------------------------------------------------

def dprint(dbg_topic, text, end='\n'):
  color_map = {'tree': 'yellow', 'parse': 'magenta', 'public': 'cyan',
               'temp': 'blue', 'error': 'red', 'phrase': 'white',
               'run': 'green'}
  if not dbg_topic in color_map:
    cprint('Error: dprint called with unknown dbg_topic (%s)' % dbg_topic,
           'red')
    exit(1)
  t = dbg_topic
  if t != 'error' and topics != 'all' and t not in topics: return
  # TODO If I want this back in, I need to get the parse_stack length from
  #      input since the module dependencies will get sticky if I import parse.
  #if dbg_topic == 'parse': text = '  ' * len(parse.parse_stack) + text
  cprint(text, color=color_map[dbg_topic], end=end)

def print_parse_failure(parse_info, verbosity=1, dst=sys.stderr):
  p, m, write = parse_info, parse_info.main_attempt, dst.write
  write('\n')
  write('Farthest parse stack:\n')
  write('  ' + str(m.stack) + '\n')
  write('Farthest token mismatch:\n')
  src = p.code[m.fail_pos:m.fail_pos + 20]
  if src.find('\n') >= 0: src = src[:src.find('\n')]
  write('  Token ' + `m.stack[-1]` + ' vs Code ' + `src` + '\n')
  lines = [_line_with_pos(p.code, m.start_pos),
           _line_with_pos(p.code, m.fail_pos)]
  pos = [m.start_pos - lines[0][0], m.fail_pos - lines[1][0]]
  messages = ['parse began here', 'parse failed here']
  write('Error point:\n')
  if lines[0][0] == lines[1][0]:
    line = p.code[lines[0][0]:lines[0][1]]
    line += '' if line.endswith('\n') else '\n'
    write('* %s' % line)
    for ch in ['^', '|']:
      _write_char_at_positions(write, ch, pos[0] + 2, pos[1] + 2)
    msg = messages[1]
    msg_delta = max(pos[1] - len(msg) // 2, pos[0] + 1) - pos[0] - 1
    write('  ' + ' ' * pos[0] + '|' + ' ' * msg_delta + msg + '\n')
    write('  ' + ' ' * pos[0] + '|\n')
    msg = messages[0]
    msg_pos = max(pos[0] - len(msg) // 2, 0)
    write('  ' + ' ' * msg_pos + msg + '\n')
  else:
    for i in range(2):
      line = p.code[lines[i][0]:lines[i][1]]
      line += '' if line.endswith('\n') else '\n'
      write('* %s' % line)
      for ch in ['^', '|']: write('  ' + ' ' * pos[i] + ch + '\n')
      msg_pos = max(pos[i] - len(messages[i]) // 2, 0)
      write('  ' + ' ' * msg_pos + messages[i] + '\n')
  write('\n')

def print_tree(obj, indent='  ', seq_item=None):
  # We do type-checking in a hacky way to avoid needing to 'import parse'.
  if type(obj).__name__ == 'SeqRule':
    dprint('tree', '%s' % obj.name)
    for i in range(len(obj.seq)):
      dprint('tree', indent, end='')
      item = '-| %s' % obj.mode_id if obj.seq[i] == '-|' else obj.seq[i]
      print_tree(obj.tokens[i], indent + '  ', item)
  elif type(obj).__name__ == 'OrRule':
    dprint('tree', '%s -> ' % obj.name, end='')
    print_tree(obj.result, indent)
  elif seq_item and seq_item.startswith('-|'):
    dprint('tree', '%s ' % seq_item, end='')
    print_tree(obj, indent)
  elif seq_item:
    # TODO Improve how this works for mode results.
    val = '[...]' if type(obj) is list else `obj`
    dprint('tree', '%s -> %s' % (seq_item, val))
  elif type(obj) == list:
    dprint('tree', '')
    for i in obj:
      dprint('tree', indent, end='')
      print_tree(i, indent + '  ')
  else:
    dprint('tree', '%s' % `obj`)


#------------------------------------------------------------------------------
#  Internal functions.
#------------------------------------------------------------------------------

# Returns start, stop so that code[start:stop] is the line including pos.
def _line_with_pos(code, pos):
  start = code[:pos].rfind('\n') + 1  # Still works if find fails.
  stop = code[pos:].find('\n')
  stop = stop + pos + 1 if stop >= 0 else len(code)
  return start, stop

def _write_char_at_positions(write, ch, pos1, pos2):
  write(' ' * min(pos1, pos2) + ch)
  delta = max(pos1, pos2) - min(pos1, pos2) - 1
  write(' ' * delta + ch + '\n')

