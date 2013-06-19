# iter.py
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
    pass # TODO Don't forget to increment version.

  def tail(self):
    pass # TODO

  def text(self):
    return ''.join(self._text)

  def move(self, delta):
    self.text_pos += delta

  def orig_pos_from_text_pos(self, text_pos):
    index, offset = self._index_offset_in_text(self, text_pos)
    attrStr = self._text[index]
    return attr.origin[0] + (0 if attrStr.is_subst else offset)

  # Returns index, offset so _text[index][offset] is the character at text_pos.
  def _index_offset_in_text(self, text_pos):
    index = 0
    pos = 0
    t = self._text
    while index < len(t) and pos <= text_pos:
      pos += len(t[index])
      index += 1
    if pos <= text_pos:
      # We must have index == len(t) to get here.
      errStr = 'Request for text_pos=%d in iter of len %d' % (text_pos, pos)
      throw IndexError(errStr)
    # We must have pos > text_pos; while pos <= text_pos one index earlier.
    index -= 1
    pos -= len(t[index])
    return index, text_pos - pos
