#!/usr/bin/python
#
# I'm learning how to add methods to
# class instances at runtime here.
#

import types

class Object(object):
  # Enable parentheses-free method calls, as in: retVal = myObj.method
  def __getattribute__(self, name):
    val = object.__getattribute__(self, name)
    try: return val()
    except: return val
  # Enable bracket-syntax on attributes, as in: retVal = myObj[methodName]
  def __getitem__(self, name): return self.__getattribute__(name)
  def __setitem__(self, name, value): self.__dict__[name] = value

class Rule(Object):
  pass

a = Object()
a.x = 5

def f(self, x):
  print("self.x=%s" % `self.x`)
  print("x=%s" % `x`)

a.__dict__['f'] = types.MethodType(f, a)

#f.im_class = a.__class__
#f.im_func = f
#f.im_self = a
#a.f = f

a.f(6)
