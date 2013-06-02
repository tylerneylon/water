symbols = {}
def log_fn(str_obj):
  print(str_obj['value'])
log_obj = {'type': 'fn', 'value': log_fn}
symbols['console'] = {'type': 'obj', 'value': {'log': log_obj}}
def make_locals():
  lo = {}
  lo.update(symbols)
  return lo

def fn(param0):
  symbols = make_locals()
  symbols['n'] = param0
  symbols['p'] = symbols['console']['value']['log']
  while symbols['n']['value'] > 0:
    symbols['p']['value']({'type': 'str', 'value': 'hi'})
    symbols['n']['value'] -= 1
symbols['f'] = {'type': 'fn', 'value': fn}
symbols['f']['value']({'type': 'num', 'value': 3})
