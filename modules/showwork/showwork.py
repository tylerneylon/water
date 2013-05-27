#!/usr/bin/python
#
# showwork.py
#
# A water module to nicely display a line-to-line correspondence between the
# input source (src) and the output code.
#

from __future__ import print_function

import dbg
import os
import parse
import run
import sys

# NOTE: I decided that functions in modules don't need to be named as if
#       they're private like _this since they aren't necessarily treated as
#       libraries by other user. Of course, individual module writers can do
#       what they like, and there may be modules that do act like libraries,
#       in which case private names could make sense.


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

# Returns a list of word-wrapped lines from one newline-free line.
def word_wrap(one_line, w):
  if one_line == '': return ['']
  short_lines = []
  while len(one_line) > w:
    short_lines.append(one_line[:w])
    one_line = one_line[w:]
  if one_line: short_lines.append(one_line)
  return short_lines

# Separates one newline-including string into lines word-wrapped at w chars.
def make_lines(long_string, w):
  if long_string is None: long_string = ''
  lines = long_string.split('\n')
  i = 0
  while i < len(lines):
    short_lines = word_wrap(lines[i], w)
    lines[i:i + 1] = short_lines
    i += len(short_lines)
  return lines

def get_src_ranges_and_lines(filename):
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
  return src_ranges, src_lines

# Splits/rejoins code so lines are together and consecutive ranges are distinct.
def get_code_ranges_and_lines():
  code_ranges = map(range_of_state, run.state_list)
  code_ranges, code_list = drop_middle_newlines(code_ranges, run.code_list)
  code_ranges, code_list = merge_into_lines(code_ranges, code_list)
  return merge_same_ranges(code_ranges, code_list)

# Builds a list of concurrent (src, code) string pairs, called chunks.
def chunks_from_src_code_info(s_ranges, s_lines, c_ranges, c_list):
  # None acts as a stopping mark for both range lists.
  s_ranges.append(None)
  c_ranges.append(None)

  chunks = []
  last_chunk = (0, 0)  # This will be < whatever is next.
  next_code = c_ranges[0] if len(c_ranges) else None
  next_src = s_ranges[0] if len(s_ranges) else None
  s, c = 0, 0  # s & c are the src & code indices.
  sline = s_lines[s] if next_src else ''
  cline = c_list[c] if next_code else ''
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
    #print('code@%s is %s\nsrc@%s is %s\n' %
    #      (next_code, `cline`, next_src, `sline`))
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
    next_src = s_ranges[s]
    next_code = c_ranges[c]
    sline = s_lines[s] if next_src else ''
    cline = c_list[c] if next_code else ''
  if next_code or next_src: chunks.append(['', ''])  # Chunk to hold the rest.
  while s < len(s_lines): add_to_last(s_lines[s], None); s += 1
  while c < len(c_list): add_to_last(None, c_list[c]); c += 1
  return chunks

# Combines consecutive chunks with the same side empty.
def combine_consec_empty_sides(chunks):
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
  return new_chunks

# Returns good widths, cols for printing chunks to the current console, where
# widths = [left_w, right_w] and cols = sum(widths) + 1 for the middle | column.
def find_good_col_widths(chunks):
  cols = int(os.popen('stty size').read().split()[1])
  max_cols = 200
  if cols > max_cols: cols = max_cols
  w = (cols - 1) // 2  # Width per screen half; 1 column for a vert split.
  widths = [w, w]

  # Check if we can improve the widths; smaller is better if the text fits.
  max_w = [0, 0]
  for c in chunks:
    for i in [0, 1]:
      if c[i]: max_w[i] = max(max_w[i], max(map(len, c[i].split('\n'))))
  min_max_w = min(max_w)
  if min_max_w < w:
    i = max_w.index(min_max_w)
    widths[i] = max_w[i]
    # Make other width as small as the text it contains, if possible.
    widths[1 - i] = min(max_w[1 - i], cols - 1 - widths[i])
  return widths

def print_chunks_in_columns(chunks, widths):
  cols = widths[0] + 1 + widths[1]
  for chunk in chunks:
    print('-' * cols)
    left_lines = make_lines(chunk[0], widths[0])
    right_lines = make_lines(chunk[1], widths[1])
    def print_a_line(left, right):
      if left is None: left = ''
      if right is None: right = ''
      print('%%-%ds|%%-%ds' % (widths[0], widths[1]) % (left, right))
    map(print_a_line, left_lines, right_lines)
  print('-' * cols)

# This function is here since it doesn't belong directly in the core. The core
# is only responsible for making this function possible.
def showwork(filename):
  run.run_code = False
  parse.runfile(filename)

  # 1. Get convenient sequences of ranges and line-based strings.
  src_ranges, src_lines = get_src_ranges_and_lines(filename)
  # We call code_list a "list" and not "lines" as some strings may be multiple
  # lines, which is what we want so code ranges are always changing.
  code_ranges, code_list = get_code_ranges_and_lines()

  # 2. Build concurrent, maybe uneven, line-based src/code string pairs.
  # This is the most nontrivial part of this entire function.
  chunks = chunks_from_src_code_info(src_ranges, src_lines,
                                     code_ranges, code_list)

  # 3. Preserve src/code mapping but collate & format for clear printing.
  chunks = combine_consec_empty_sides(chunks)
  widths = find_good_col_widths(chunks)
  print_chunks_in_columns(chunks, widths)


# We expect args[0] to be the part of the shell command up to and including our
# command name - which may contain spaces, and have been considered different
# arguments by the shell itself.
def main(args, self_dir):
  if len(args) < 2:
    print("Usage: %s <water_filename>" % args[0])
    exit(2)
  showwork(args[1])
