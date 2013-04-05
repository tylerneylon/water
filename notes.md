# Project Water

My primary notes are in a notebook dedicated to this project,
and this file is for use outside of that notebook - such as
when I'm traveling.

## Main goal

The main goal is to produce a system where we can easily
build a binary for a programming language with the following
features:

* The language is easy to build.
* The language is easy to modify at compile time
  (technically, the language is always specified
  at compile time.)
* Every language automatically comes with an
  interactive shell / interpreter.
* The final output of compilation could be native
  machine language that executes with extremely
  high efficiency.
* It is easy to provide precise error information.
* It is possible to provide sophisticated
  debugging capabilities.
* The code for all of this is compact and easy
  to understand.

## Instrumental goals

These are goals that do not fit directly into Water,
but which I would like to eventually build on top of
water.

* Enable useful runtime use analytics, and no-recompile
  use of those analytics for optimization. For example,
  have a sort function which could be quicksort,
  mergesort, heapsort, or others; collect analytics
  on the arrays typically sorted (or just the running
  times of the various sort algorithms), and later
  solidify the choice to a single algorithm that
  statistically gives the best performance.

## Optional goals

Include a full stack at binary runtime, so that
the language can be both modified and executed
at runtime. Lisp somewhat does this. In general,
it fits with the pholosophy of Water to always
consider language modification as a peer of
compilation. In other words, always think of
the dynamic language specification as *part*
of the language.

Support the possibility of powerful compile-time
execution, as in generic programming. I had to
check that vs metaprogramming. I do mean generic
programming, as in executing Turing-complete
stuff at compile-time. Of course I also want to
enable metaprogramming, but I think that is
easier to achieve.

## Design strategy

Here's a top-down analysis:

First, write it in python -> python.
Then, add -> llvm ir output.
Then, dogfood it (write it in itself).

Later, develop either machine language output,
or my own ir in order to implement pizza
efficiently.


## Next steps

What is my current goal?
I want something I might be able to accomplish
in about a week of small work amounts.

First, I'd like to internally specify the
lang spec syntax (better name?) in water.py.
(I guess I'll work with water2.py until I'm happy
with it, and then use it to replace water.py).
Second, I'd like to be able to internally output
and execute python code based on the language spec.


## Random thoughts

### Idea: Drop tokens (variables and characters only)

Mathematically, it feels more elegant to drop the token as an intermediate rule type,
and simply have variables and characters as axiomatic rules.

However, I'm not sure that is practical. In particular, imagine some keywords with
shared prefixes, such as const and continue. We really only need to tokenize once,
but if my parser inputs and spits back out low-level tokens while trying to match a
top-level statement rule, then the default behavior would be (with the current parsing
strategy) to reattempt to parse a continue as a const many times.

Maybe we could use a completely bottom-up parsing approach.

### A web/js-based interpreter as output and/or arbitrary browser-runnable js as output







