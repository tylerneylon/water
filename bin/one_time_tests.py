#!/usr/bin/python
#
# one_time_tests.py
#
# Tests to answer one-off code questions.
#

#############################################################################
# Question 1:
# Must __getattribute__ explicitly call __getattr__ on a lookup failuer?
#
# Answer:
# It appears not.
#############################################################################

class A(object):
  def __getattribute__(self, name):
    print("__getattribute__ called")
    raise AttributeError(name)
  def __getattr__(self, name):
    print("__getattr__ called")
    return '<from __getattr__>'
    
def q1():
  a = A()
  print(a.abc)

#############################################################################
# Question 2:
# Can I make a small-scale reproduction of the bug I have in parse.py?
#
# Answer:
# I think yes.
#############################################################################

class B(object):
  def __init__(self, myname):
    self.myname = myname
  def __getattribute__(self, name):
    print("__getattribute__(%s, %s)" % (object.__getattribute__(self, 'myname'), name))
    try:
      return object.__getattribute__(self, name)
    except AttributeError:
      d = object.__getattribute__(self, '__dict__')
      if name in d: return d[name]
      raise
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
