#!/usr/bin/python
#

class B(object):
  def __init__(self, myname):
    self.myname = myname
  #def __getattribute__(self, name):
  #  mycall = "__getattribute__(%s, %s)" % (object.__getattribute__(self, 'myname'), name)
  #  print(mycall)
  #  try:
  #    return object.__getattribute__(self, name)
  #  except AttributeError:
  #    print(mycall + " : had an AttributeError; trying backups")
  #    d = object.__getattribute__(self, '__dict__')
  #    if name in d: return d[name]
  #    raise
  def __getattr__(self, name):
    print("__getattr__(%s, %s)" % (object.__getattribute__(self, 'myname'), name))
    d = object.__getattribute__(self, '__dict__')
    if 'delegate' in d: return self.delegate.__getattribute__(name)
    raise AttributeError(name)

def q2():
  b1 = B('b1')
  b2 = B('b2')
  b3 = B('b3')

  b1.delegate = b2
  b2.delegate = b3
  b3.key = 'value'

  print(b1.key)

q2()
