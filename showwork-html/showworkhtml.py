#!/usr/bin/python
#
# showworkhtml.py
#
# A Water module to show side-by-side input and output lines.
# Eventually I plan to put all non-core showwork code in this module.
#

# Enable imports from the parent directory.
import sys; sys.path.append('..')

import os
import parse
import re
import run

def file_contents(filename):
  f = open(filename)
  s = f.read()
  f.close()
  return s

class Template(object):
  def __init__(self, filename):
    template = file_contents(filename)
    self.pieces = re.split(r'(\[\[.*?\]\])', template)

  # We expect key to be a string of the form '[[something]]'.
  def set(self, key, value):
    idx = self.pieces.index(key)
    self.pieces[idx] = value

  def write_to(self, dst):
    f = open(dst, 'w') if type(dst) == str else dst
    f.write(str(self))

  def __str__(self):
    return ''.join(self.pieces)
  

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print('Usage: %s <water_filename>' % sys.argv[0])
    exit(2)
  in_filename = sys.argv[1]
  run.run_code = False
  parse.runfile(in_filename)
  
  src = file_contents(in_filename)

  code_html = []
  js = ['var ranges = [']
  for i in range(len(run.code_list)):
    code = run.code_list[i]
    code_html.append('<span id="%d" class="code-span">%s</span>' % (i, code))
    if i > 0: js.append(', ')
    rng = run.state_list[i]
    js.append('[%d, %d]' % (rng['start'], rng['end']))
  js.append('];')

  template = Template('template.html')
  template.set('[[source file name]]', os.path.basename(in_filename))
  template.set('[[src content]]', src)
  template.set('[[code content]]', ''.join(code_html))
  template.set('[[javascript]]', ''.join(js))

  out_filename = 'tmpout.html'
  template.write_to(out_filename)
  os.system('open %s' % out_filename)

