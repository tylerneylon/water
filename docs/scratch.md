# Scratch notes

This is a place for temporary notes as I work.

## Thinking on how to implement `+` and `*`

    a -> (( hello | there ))* other_stuff

should become

    a -> _inner_34 other_stuff
    
    _inner_34 -> (( body )) _inner_34 | Empty

I might want to be able to handle labels already on the item.

The above is dangerous because we could loop by continuously paring
nothing (Empty) as rule a.

I think the right way to think about that is that any potentially-empty
rules, including *-rules, should not be looped.

----

How about handling naming a `rulename` to `rulename_list`?

    a -> my_rule* other_stuff

becomes

    a -> _inner_35:my_rule_list other_stuff

etc

---

Idea: support a `names` method that returns a list of
strings that are interpreted as names through which to
expose the rule associated with that name.

Or, for `+` and `*`, I could just use the last-provided
name as the official name. Eg, if there's a label, use that.
No label, but it's a rule name, use that. Otherwise you have
to access it through tokens.

---

Toward a good user experience with +, * suffixes -- it would
be nice to support lists as the returned type for these.

Currently mode rules return lists, but they also always call
mode_params, so they would interfere with any pre-existing
mode rules (or be interfered with by them).

So I suggest having an alternate mode rule syntax which does
not call any methods to enter it. Something like =mode_name
instead of -mode_name. Or perhaps --mode_name.

Now, for application with * and + suffixes, the challenge
becomes how to add rules in a new custom mode. For this, I
propose that we use parse-level commands instead of a
substitution. The rules would be relatively simple, so this
approach seems feasible to me.

---

Including files.

I think this can be a pipeline of a file loader and a nestable
parser. The trouble is the debugging info. For now, every rule
has just a start_pos and an end_pos. I think in the end that we'll
want more data with each rule, such as a list (stack) of points
within a nest of files, including both orig_pos and text_pos with
version number. We would also like a filename/source field that
could include either the file name (the obvious case) or something
indicating where it came from as a string in code (the less obvious
case).

Current plan: Get an exec-like function working that breaks
debugging info, and then fix debugging info on top of that.

---

## How rules are updated

Currently, rules are stored in two places: a universal rule set, and in a mode
stack. This allows for easy shadowing that changes with the mode, and fast
lookups.

Most of the time, it also allows for single-chunk language definition blocks to
not have to worry about setting up partial rules that break as they're being
parsed. However, if a new mode is pushed (under the current system) in the
middle of such a block, the new mode could contain broken rules.

I'd like to provide stronger guarantees that order doesn't matter within a
rule definition block. Here is a plan to do so:

* Rule lookups happen as if they are always pulled out of the universal rule
  set. Effectively, the universal rule set is always definitive, and never
  deferred (as it is now). In practice, a cache can be set up that is as fast as
  a single dictionary (with possible work between mode pushes/pops) but is
  invalidated whenever the universal rule set changes.
* Rules defined within a mode only exist in the current mode object until that
  mode is popped, at which point, they're added to the universal rule set.

That's it.

---

## How parse_string can work

Currently parse_string pushes a new global mode onto the mode stack and parses
phrases within that.

I suggest instead that the default be to parse within the current mode, and that
options may be made to parse in either the base global mode or in the highest-
existing mode of a certain name. Which one corresponds with the expected
behavior of a function like exec? This isn't clear to me. I'll be in a better
position to decide once I have more working experience.

---

## A principle to add to my list of principles

The parse tree should correspond to the source in the sense that:

* Each parsed phrase corresponds to a nonempty section of the source text, and
* all phrase objects together partition the source text on a full successful
  parse.

In addition, src(rule) for any full level of the parse tree should reproduce the
entire parsed source in order. A "full level" I haven't defined carefully, but
intuitively it's a set of nodes that could act as all the leaves of a tree with
the same root as the original tree.

Also: where did I write down my development principles?

---

## How +,* suffixes can work

Ok, this is the umpteenth time I've changed my mind about this, but this one is
the most recent, and afer more experience with things.

I propose a new syntax that supports turning a rule's output into a certain kind
of list. Something like this:

>
  a -->
    'A'
  a_star[a] --> a_plus | Empty
  a_plus[a] -->
    a a_star

The new part is the [a] notation, which means to reduce the output to a list of
rules of type a. If not possible, the rule is a parse failure.

This can be achieved by recursively calling it on all tokens or list elements,
unless (i) the item is already type a, in which case return [a] or (ii) the item
fits none of the previous criteria, in which case we consider the operation a
parse failure.

---

## Infix operators

>
  sum -> number+'+'
  product -> number+'*'

The values after + or * are separators.

>
  a -->
    'A'
  a_star[a] --> a_plus | Empty
  a_plus[a] -->
    a ('+')a_star

The tricky part is making a separator work well with prefixes.
They feel conceptually different to me.
Basically, a prefix is what counts as whitespace, and occasionally we want
to turn that off within a mode.

My hunch is that prefixes should be stack-based (they somewhat are already).

Every rule can have a `.prefix` field which complements its `tokens` to give
the full `src`. (Well, every `SeqRule`, that is.)

Two operations are possible when adding to the prefix stack:
1. Add a new item to be sandwiched by the last item; or
2. Add a blank slate.

We want to use 1 for separators like infix operators.
We want to use 2 for things like strings.

Maybe the notation can be like this:

>
  number_plus[number] -->
    number ('+')number_star
  str -->
    "['\"]" (='')-str

For the last part, I could also consider a notation that alters the prefix on
entry to a mode, such as this:

> str (prefix='')
  phrase --> # etc

Actually, I do prefer that.

So, for now, my decision is:

* An item can be (<prefix_change>)<item>
* Start of a lang def block can be > <mode_name> (<prefix_change>)

and a `prefix_change` can be:

* (<item>)

meaning we sandwich the item between the old prefix, or

* (prefix=<item>)

meaning the prefix is replaced as a new stack prefix.

As before, prefix changes are always temporary and popped for the user.
I may consider old explicitly stack setting (through the api) to be bad
practice after this, and think about how to discourage its use.

For starters, I'll implement the prefix_change on rule names. I hope this
can be a slight modification to the code that handles . prefixes (not sure).

---

## Some steps for prefixes

* Add a `prefix` field to `SeqRule` so `src` can get correct data, and
  test that.
* Notice and react to a parse failure on a prefix.
* Understand a push-prefix-change on items / get 52.water working.
* Understand a set-prefix-change on items, with a test.
* Understand prefix changes on lang def blocks, and test.

---

## General next steps, after the infix sutff

* Add a unit test system which is easy to run comprehensively.
* Split out samples into working, test-error-msgs, and pending.
* Code cleanup and list out in-code todo items.
* Try to clean up grammars: core (mainly) and layers (secondarily).
