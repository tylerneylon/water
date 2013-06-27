# iterator.py
# Project Water
#
# Define an iterator for use by parse.py.
#
# Terminology:
#  We use the word "text" to mean the current state of the source, including
#  all substitutions made. The word "original" (short version: "orig") means the
#  source before *any* substitutions were made. Substitutions and replacements
#  are synonymous.
#

# An _AttrStr is a string with attributes. For example, the following is valid:
# s = _AttrStr('hello there')
# s.attr = 42
# print(s + str(len(s) + s.attr))
class _AttrStr (str):
  pass

# _text is a list of _AttrStr objects. The current text version is the
# concatenation of all these, as strings. Each _AttrStr has these attributes:
#  * is_subst  - True iff the string is a replacement of original text.
#  * origin    - The range, as a [start, end) pair, of the string in orig src.
class Iterator (object):
  
  def __init__(self, src):
    self.orig_src = src
    attrStr = _AttrStr(src)
    attrStr.is_subst = False
    attrStr.origin = (0, len(src))
    self._text = [attrStr]
    self.text_pos = 0
    self.version = 0

  def replace(self, rng, new_str):
    index1, offset1 = self._index_offset_in_text(rng[0])
    index2, offset2 = self._index_offset_in_text(rng[1])
    new_list = []
    if offset1 > 0:
      new_list.append(self._str_slice(index1, 0, offset1))
    new_str = _AttrStr(new_str)
    new_str.is_subst = True
    origin_start = self.orig_pos_of_text_pos(rng[0])
    origin_end = self.orig_pos_of_text_pos(rng[1], use_end_pos=True)
    new_str.origin = (origin_start, origin_end)
    new_list.append(new_str)
    if offset2 < len(self._text[index2]):
      new_list.append(self._str_slice(index2, offset2, None))
    self._text[index1:index2 + 1] = new_list
    self.version += 1

  def tail(self):
    index, offset = self._index_offset_in_text(self.text_pos)
    tail_list = [self._text[index][offset:]] + self._text[index + 1:]
    return ''.join(tail_list)

  def text(self):
    return ''.join(self._text)

  def move(self, delta):
    self.text_pos += delta

  def orig_pos_of_text_pos(self, text_pos, use_end_pos=False):
    index, offset = self._index_offset_in_text(text_pos)
    attrStr = self._text[index]
    if attrStr.is_subst:
      return attrStr.origin[1] if use_end_pos else attrStr.origin[0]
    return attrStr.origin[0] + offset  # Exact value since attStr is orig src.

  def orig_pos(self):
    return self.orig_pos_of_text_pos(self.text_pos)

  # Returns index, offset so _text[index][offset] is the character at text_pos.
  def _index_offset_in_text(self, text_pos):
    index = 0
    pos = 0
    t = self._text
    while index < len(t) and pos <= text_pos:
      pos += len(t[index])
      index += 1
    if pos < text_pos:  # We must have index == len(t) for this to be true.
      errStr = 'Request for text_pos=%d in iterator of len %d'
      raise IndexError(errStrFmt % (text_pos, pos))
    # We must have pos > text_pos; while pos <= text_pos one index earlier.
    index -= 1
    pos -= len(t[index])
    return index, text_pos - pos

  def _str_slice(self, index, start, end):
    s = self._text[index]
    t = _AttrStr(s[start:end])
    t.is_subst = s.is_subst
    if t.is_subst:
      t.origin = s.origin
    else:
      t_start = s.origin[0] + start
      t.origin = (t_start, t_start + len(t))
    return t
