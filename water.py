#!/usr/bin/python
#
# water.py
#
# A fluid compiler.
#
# TODO Add public documentation.
#

from __future__ import print_function

import dbg
import os
import parse
import run
import sys

# TODO All of the code from here until the main clause at the bottom is for
#      showwork. It belongs in a separate module, not here.

# Expects two pairs; returns -1, 0, or 1 when r1 < r2,
# r1 ~ r2, or r1 > r2.
def rng_cmp(r1, r2):
  if r1[1] <= r2[0]: return -1
  if r2[1] <= r1[0]: return 1
  return 0

def rng_merge(r1, r2):
  return (min(r1[0], r2[0]), max(r1[1], r2[1]))

def range_of_state(st): return (st['start'], st['end'])

# Output code strings will have at most 1 newline at their ends.
def drop_middle_newlines(ranges, code_strs):
  out_ranges = []
  out_strs = []
  for i in range(len(code_strs)):
    code = code_strs[i]
    pieces = [s + '\n' for s in code.split('\n')]
    pieces[-1] = pieces[-1][:-1]
    if code.endswith('\n'): pieces.pop()
    out_strs += pieces
    out_ranges += [ranges[i] for p in pieces]
  return out_ranges, out_strs

# Drop all newlines; each output code string is a line.
def merge_into_lines(ranges, code_strs):
  out_ranges = []
  out_strs = []
  for i in range(len(code_strs)):
    code = code_strs[i]
    if i == 0 or out_strs[-1].endswith('\n'):
      out_ranges.append(ranges[i])
      out_strs.append(code)
    else:
      out_ranges[-1] = rng_merge(out_ranges[-1], ranges[i])
      out_strs[-1] += code
  out_strs = map(lambda s: s[:-1], out_strs)
  return out_ranges, out_strs

# Output strings are \n-joined input lines, grouped by identical ranges.
def merge_same_ranges(ranges, code_strs):
  out_ranges = []
  out_strs = []
  for i in range(len(code_strs)):
    if out_ranges and out_ranges[-1] == ranges[i]:
      out_strs[-1] += ('\n' + code_strs[i])
    else:
      out_ranges.append(ranges[i])
      out_strs.append(code_strs[i])
  return out_ranges, out_strs

# This function is here since it doesn't belong directly in the core. The core
# is only responsible for making this function possible.
def showwork(filename):
  run.run_code = False
  parse.runfile(filename)

  # 1. Load in the src and find a list of char ranges for each line.

  f = open(filename)
  src = f.read()
  # TODO I just realized I'm not using the terms src & code consistently.
  #      Go back and change many uses of code -> src.
  #      To be clear to myself: 'src' means the input, 'code' is the output
  #      sent to the runtime during normal operation.
  f.close()
  src_lines = src.split('\n')

  # A 'range' is a pair (start, end) represending s[start:end].
  src_ranges = []
  idx = 0
  for line in src_lines:
    size = len(line) + 1
    src_ranges.append((idx, idx + size))
    idx += size


  # 2. Consolidate code info so consecutive ranges are distinct.

  code_ranges = map(range_of_state, run.state_list)
  code_ranges, code_list = drop_middle_newlines(code_ranges, run.code_list)
  code_ranges, code_list = merge_into_lines(code_ranges, code_list)
  code_ranges, code_list = merge_same_ranges(code_ranges, code_list)


  # 3. Build a list of concurrent (src, code) string pairs.

  # None acts as a stopping mark for both range lists.
  src_ranges.append(None)
  code_ranges.append(None)

  chunks = []
  last_chunk = (0, 0)  # This will be < whatever is next.
  next_code = code_ranges[0] if len(code_ranges) else None
  next_src = src_ranges[0] if len(src_ranges) else None
  s, c = 0, 0  # s & c are the src & code indices.
  sline = src_lines[s] if next_src else ''
  cline = code_list[c] if next_code else ''
  # I'm leaving in some commented-out print statements because I'm not 100% that
  # the current chunking heuristics are optimal. If I want to experiment, I can
  # uncomment the prints to help see the decisions being made.
  def new_chunk(src, code):
    #print('new_chunk(%s, %s)' % (`src`, `code`))
    chunks.append([src, code])
  def add_to_last(src, code):
    #print('add_to_last(%s, %s)' % (`src`, `code`))
    if src: chunks[-1][0] += src
    if code: chunks[-1][1] += code
  while next_code and next_src:
    #print('\nlast_chunk is %s' % (last_chunk,))
    #print('code@%s is %s\nsrc@%s is %s\n' % (next_code, `cline`, next_src, `sline`))
    # We have both new src and new code to add.
    if rng_cmp(next_src, next_code) == 0:
      # Next src & code overlap, so make them a new chunk. The lists were
      # consolidated above, so we don't want to append to the last chunk.
      new_chunk(sline, cline)
      s += 1
      c += 1
      last_chunk = rng_merge(next_code, next_src)
    else:
      # Next src & code don't overlap, so we will only add one or the other.
      if rng_cmp(next_src, last_chunk) == 0:
        # Looks like the current src is still part of the last chunk.
        add_to_last('\n' + sline, None)
        s += 1
      elif rng_cmp(next_code, last_chunk) == 0:
        add_to_last(None, '\n' + cline)
        c += 1
      else:
        # Next src is not part of last chunk; new chunk w whichever is first.
        if rng_cmp(next_src, next_code) == -1:
          # src before code
          new_chunk(sline, None)
          s += 1
          last_chunk = next_src
        else:
          # code before src
          new_chunk(None, cline)
          c += 1
          last_chunk = next_code
    next_src = src_ranges[s]
    next_code = code_ranges[c]
    sline = src_lines[s] if next_src else ''
    cline = code_list[c] if next_code else ''
  if next_code or next_src: chunks.append(['', ''])  # Chunk to hold the rest.
  while s < len(src_lines): add_to_last(src_lines[s], None); s += 1
  while c < len(code_list): add_to_last(None, code_list[c]); c += 1

  # 3.5. Combine consecutive chunks with the same side empty.

  def do_combine(prev_chunks, next_chunk):
    if len(prev_chunks) == 0: return False
    for i in [0, 1]:
      if prev_chunks[-1][i] == next_chunk[i] == None: return True
    return False

  new_chunks = []
  for chunk in chunks:
    if do_combine(new_chunks, chunk):
      for i in [0, 1]:
        if chunk[i] is not None:
          new_chunks[-1][i] += ('\n' + chunk[i])
    else:
      new_chunks.append(chunk)
  chunks = new_chunks

  # 4. Collate, word-wrap, and print the lines side-by-side.

  cols = int(os.popen('stty size').read().split()[1])
  max_cols = 200
  if cols > max_cols: cols = max_cols
  w = (cols - 1) // 2  # Width per screen half; 1 column for a vert split.

  # Returns a list of word-wrapped lines from one newline-free line.
  def word_wrap(one_line):
    if one_line == '': return ['']
    short_lines = []
    while len(one_line) > w:
      short_lines.append(one_line[:w])
      one_line = one_line[w:]
    if one_line: short_lines.append(one_line)
    return short_lines

  # Separates one newline-including string into word-wrapped lines.
  def make_lines(long_string):
    if long_string is None: long_string = ''
    lines = long_string.split('\n')
    i = 0
    while i < len(lines):
      short_lines = word_wrap(lines[i])
      lines[i:i + 1] = short_lines
      i += len(short_lines)
    return lines

  for chunk in chunks:
    print('-' * cols)
    left_lines = make_lines(chunk[0])
    right_lines = make_lines(chunk[1])
    def print_a_line(left, right):
      if left is None: left = ''
      if right is None: right = ''
      print('%%-%ds|%%-%ds' % (w, w) % (left, right))
    map(print_a_line, left_lines, right_lines)
  print('-' * cols)

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print("Usage: %s <water_filename> [options]" % sys.argv[0])
    exit(2)
  if True:
    dbg.dst = [sys.stdout]
    dbg.topics = ['tree', 'parse', 'public']
    dbg.topics = ['run']
  else:
    #dbg.topics = 'all'
    dbg.dst = []
  if '--showwork' in sys.argv:
    showwork(sys.argv[1])
  else:
    parse.runfile(sys.argv[1])

