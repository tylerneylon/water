#
# object.py
#
# Object is a class that supports syntax closer
# to a js object, such as treating dot notation
# as a synonym for []-based looups:
#
# obj = Object()
# obj['key'] = 3
# x = obj.key        # x == 3 now.
#

class Object(object):
  def __getitem__(self, name):
    return self.__getattribute__(name)
  def __setitem__(self, name, value):
    self.__dict__[name] = value
  def __contains__(self, name):
    try: self.__getitem__(name)
    except AttributeError: return False
    return True
  def __repr__(self): return repr(self.__dict__)

