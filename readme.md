# Project Water

The goal of water is to build an open compiler -- an adaptable compiler that can
compile or modify any programming language; this enables non-compiler-experts
to evolve languages, as well as powerful cross-language developer tools.
The project is at a very early stage, and the current code is a rough
prototype of a language parser and compiler.

## Open Compilers

An *open compiler* is a compiler which:

* can change the language as the source files are read,
* has decoupled output modules that can produce custom bytecode or a standard
  executable,
* essentially provides a free interpreted mode for any language,
* essentially provides a free debugger for any language,
* can generate extremely efficient compiled code.

A future goal, though lower priority, is to support fast compilation of
large code bases.

## Example use

From the base directory, run:

    $ bin/water.py samples/good/12.water

This will simply say `hi` to you. It's interesting because the end of
`12.water` is the following javascript:

    function f(n) {
      var p = console.log;
      while (n > 0) {
        p('hi');
        n--;
      }
    }
    f(3);

... and water knows nothing about javascript. So how did it work?

The answer is the top of the file `12.water`, which specifies a subset
of the javascript language. Here's a selection from the grammar spec in that file:

    stmnt_no_smcln -> func_def | assign | while | expr
    assign -> direct_assign | inc_assign
    direct_assign ->
      "(var)?" s ident s '=' s expr
      add_code:
        run.add("symbols['%s'] = " % ident.src())
        run.add(expr, "\n")
    inc_assign ->
      ident s inc_op
      add_code:
        run.add(ident, "['value'] ", inc_op, "\n")
    while ->
      'while' s '(' s cond s ')' s '{' -block
      add_code:
        run.add("while ", cond, ":\n")
        run.push_indent('  ')
        for r in mode_result: run.add(r)
        run.pop_indent()

This might remind you of Lex and Yacc, except that it goes a couple steps
further than parsing into a syntax tree. It also compiles and executes
the code.

Like many modern code execution flows, it follows the steps of parsing,
compiling into a runtime-ready language, and then execution in a runtime
environment. Currently, the runtime-ready language is Python. This is
because the system is at an early stage and still being developed. In
the future, for example, water may output llvm-ir code that can be converted
into executable files by llvm.

We can gain visibility into what water is doing by using some options.
For example, running

    bin/water.py samples/good/12.water --showcode

will not run the code, but instead print out the code actually executed,
which is Python:

    symbols = {}
    def log_fn(str_obj): print(str_obj['value'])
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
      while symbols['n']['value'] > {'type': 'num', 'value': 0}['value']:
        symbols['p']['value']({'type': 'str', 'value': 'hi'})
        symbols['n']['value'] -= 1
    symbols['f'] = {'type': 'fn', 'value': fn}
    symbols['f']['value']({'type': 'num', 'value': 3})

This code looks a bit complex.
It's not intended for human consumption.
Rather, it's meant to be general and
support the introspective features of javascript.

We can use another approach to see a line-by-line association between
input source (javascript) and output code (python):

    bin/water.py -showwork samples/good/12.water

Here is a truncated selection from the output of that command:

    -------------------------------------------------------------------------------------------------
    function f(n) {            |def fn(param0):
                               |  symbols = make_locals()
                               |  symbols['n'] = param0                                              
    -------------------------------------------------------------------------------------------------
      var p = console.log;     |  symbols['p'] = symbols['console']['value']['log']                  
    -------------------------------------------------------------------------------------------------
      while (n > 0) {          |  while symbols['n']['value'] > {'type': 'num', 'value': 0}['value']:
    -------------------------------------------------------------------------------------------------
        p('hi');               |    symbols['p']['value']({'type': 'str', 'value': 'hi'})            
    -------------------------------------------------------------------------------------------------
        n--;                   |    symbols['n']['value'] -= 1                                       
    -------------------------------------------------------------------------------------------------
      }                        |symbols['f'] = {'type': 'fn', 'value': fn}
    }                          |                                                                     
    -------------------------------------------------------------------------------------------------
    f(3);                      |symbols['f']['value']({'type': 'num', 'value': 3})                   
    -------------------------------------------------------------------------------------------------

