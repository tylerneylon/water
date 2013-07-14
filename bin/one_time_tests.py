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
    raise AttributeError(name)
    
a = A()
print(a.abc)
