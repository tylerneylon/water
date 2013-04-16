#!/usr/bin/python
#
# This exhibits some behavior of the exec command which was surprising to me.
# Basically, running h() results in an error since the variable b cannot be
# found when inner function i() is executed. I expected the local scope to be
# examined for b first, but it wasn't.
#

def f():
  a = 3
  def g(): print(a)
  g()
  print('locals=%s' % `locals()`)
f()

def h():
  b = 4
  s = 'def i(): print(b)'
  lo = {'b': b}
  exec s in globals(), lo
  lo['i']()
h()

