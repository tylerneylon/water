# Project Water

The goal of water is to build a dynamic compiler, which is explained below.
The project is at a very early stage, and the current code is a rough
prototype of a language parser.

## Primary Goal

Let language designers and programmers focus on language, and ignore the
details of building parsers, compilers, optimizers, interpreters, and
debuggers.

## Dynamic Compilers

A *dynamic compiler* is a compiler which:

* can change the language as the source files are read,
* has decoupled output modules that can produce custom bytecode or a standard
  executable,
* essentially provides a free interpreted mode for any language,
* essentially provides a free debugger for any language,
* can generate extremely efficient compiled code.

A future goal, though lower priority, is to support fast compilation of
large code bases.

