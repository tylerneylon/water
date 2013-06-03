# Project Water

The goal of water is to build an open compiler -- an adaptable compiler that can
compile or modify any programming language; this enables non-compiler-experts
to evolve languages, as well as powerful cross-language developer tools.
The project is at a very early stage, and the current code is a rough
prototype of a language parser and compiler.

## Primary Goal

Let language designers and programmers focus on language, and ignore the
details of building parsers, compilers, optimizers, interpreters, and
debuggers. This modularity also allows tool developers to build for
multiple languages at once.

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

