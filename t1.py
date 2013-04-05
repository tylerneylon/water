class Rule(object):
  def __init__(self, x):
    self.x = x
    self.methods = {}
  # Enable parentheses-free method calls, as in myObj.method.
  def __getattribute__(self, name):
    val = object.__getattribute__(self, name)
    try: return val()
    except: return val
  def __getitem__(self, name): return self.__getattribute__(name)
  def __setitem__(self, name, value): self.__dict__[name] = value
  def addCall(self, method, imp):
    self.methods[method] = imp
  def fn(self):
    print('fn')
    print(self.x * self.x)
  def g(self, y):
    print('g')
    print(y * y)

r = Rule(3)
def h(x):
  print('h')
  print(x)
r.h = h
r.fn
r.g(5)
r.h(8)

def i():
  print('i')
r.i = i
r.i

r['i']
x = 'g'
r[x](9)

def j(): print('j')
x = 'j'
r[x] = j
r.j

