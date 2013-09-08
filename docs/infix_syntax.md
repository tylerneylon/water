# infix notation

504.2013

Here are some thoughts on how infix notation might work in a language grammar.
These are speculative and likely to change over time.

Let's work with the following operators and precedence levels:

    ||
    &&
    + -
    * /
    ^

We'll treat `||` and `&&` similar to C, where they're short-circuited
operators that return 1 for true and 0 for false, and treat nonzero inputs
as truthy.

Here's an idea for how to support expressions with these operators:

```
number -> "[1-9][0-9]*"
  value: return val(self)
variable -> "[a-zA-Z]+"
  value: return env.symbols[val(self)]
atom -> number | variable
power -> atom '^' power | atom    # right-associative
  value:
    if or_index == 0:
      return atom.value() ** power.value()
    else:
      return atom.value()
mult_op -> '*' | '/'
product -> power+mult_op
  value:
    v = power_list[0].value()
    for p in power_list[1:]:
      if p.prefix == '*': v *= p.value()
      else: v /= p.value()
    return v
sum_op -> '+' | '-'
sum -> product+sum_op
  value:
    v = product_list[0].value()
    for p in product_list[1:]:
      if p.prefix == '+': v += p.value()
      else: v -= p.value()
    return v
ands -> sum+'&&'
  value:
    v = sum_list[0].value()
    for s in sum_list[1:]:
      if v == 0: return 0
      v = s
    return v
expr -> ands+'||'
  value:
    v = ands_list[0].value()
    for s in sum_list[1:]:
      if v != 0: return v
      v = s
    return v
```

This seems decent to me since it has something like 7 lines per operator level,
which is not too bad. Of course, this is pretending like we are building a
compile-time evaluation, which isn't the full goal of expression eval at
runtime. However, it does represent the full parsing, and support appropriate
hooks for building the runtime evaluation code.

## Steps to code

1. Set up a new goal and progress bar.
2. Set up a `val()` public function.
3. Make sure the `power` eval works, specifically the attr references.
4. Switch all returned atoms to be attribute-friendly.
5. Switch how prefix sandwiching works to treat `prefixes[-1]` as a stack.
6. Switch all prefixes to be based on an atom's `.prefix` and `.suffix`.
7. Make sure the notation `p.prefix` in the `product` rule will work.
8. Support the a+b and a*b syntaxes.
9. Make sure the end-to-end system works.

