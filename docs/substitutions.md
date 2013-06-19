# Substitutions

This is a design document toward adding
substitutions to water.
I'll use the words substitution and replacement interchangeably.

Substitutions are a bit like C macros, except that I'd like
the core mechanism to be more general, so that using them
will *not* feel like a workaround or a hack.

We need a few pieces to enable substitutions:

* Since source is no longer a static string, we need a way to track how it
  evolves, and where we are. This must include support for printing
  out user-friendly error messages, and allow for some caching during parsing.
* We need a way for the core grammar to support substitutions. I decided to
  use a new public method called parse.replace() with a behavior similar to
  run.add(); in other words, we can replace either strings or trees, or
  variadic parameter lists thereof. Actually, replace may not be the best name
  since we may call it multiple times within the implementation of a single
  substutition.
* We need a way to augment existing or-rules.
* It's nice to think ahead about easier ways for the main grammar to support
  substitutions.
* Thinking even further ahead, it may be nice to allow some code to isolate,
  at compile-time, changes due to substitutions.
  In other words, we'd like to be able to do something like `require <module>`
  where the `module` has its own crazy substitution rules, but they are no
  longer in effect after the `require` call.
  We may also want to turn off grammar editing
  *except* for substitutions.

## Iterators

An iterator will be an object defined in its own `py` file.
It will have the following data:

* A list of attribute-having strings. Their concatenation is the current state
  of the source. Each string has an origin range, given as a `(start, end)` pair
  in the Python manner - so `end` is an excluded position.
  Strings will also be marked as either original source or a replacement.
* A version number that is incremented every time a replacement is made.
* A position within the current text.

We can make an attribute-having string like this:

    class AttrStr (str):
      pass

The following operations are supported:

* **Split** from a range of positions in the current text to a string to
  replace that range.
* Get the **current tail** as a string.
* **Update position** to move us forward.
* Get a **line from a current-version position**.
* Get a **source position from a current-version position**.

### Origin ranges

I can consider that each string may have, instead of a single `origin` range, a
pair of ranges called `full_origin` and `split_origin`. The meaning is analogous
to the way we map source input and code output lines, where `full_origin` is
always the complete pre-substitution range that became the tree that became the
replaced strings; and `split_origin` is a consecutive partitioning of the
source. In some cases, the `split_origin` may have zero-length, but it will
still have a valid position in the source.

There is a challenge in assigning origin ranges when a substitution is made from
the output of a previous substitution. In that case, I suggest that the new
replacement just use the entire origin range of whatever it replaces.

### Use with existing parse methods

The main entry point into parsing is a call to `parse_phrase(src, pos)`
(where I currently have `code` instead of `src`, though in the long run
I think it should be `src`). This can be replaced by an initial call like this:

    iter = Iterator(src)
    while !iter.done(): tree = parse_phrase(iter)

There are also many calls of the form:

    tree, pos = a_parse_fn(src, pos)  # With variations on "a_parse_fn".

These can be replaced with calls like this:

    tree = a_parse_fn(iter)

If there are any cases where the output `pos` value does not overwrite the
input value, then we can implement a `copy` method on `Iterator`, and use it
as such:

    saved_iter = iter.copy()
    tree = a_parse_fn(iter)
    # May still use saved_iter for access to the old iter state.

### Substitution history

I think it would be nice to allow users to explore what substitutions have been
made. This could help with debugging when the error was introduced in a
non-obvious way by substitutions. We already have access to two versions of the
source: the original, and the latest version when the error occurred. These
may be enough for many cases. If a water module wants more history, we can
allow hooks into `parse.replace` or whichever method is appropriate. This way
an external module can do its own work of tracking replacements, and we can
keep the iterator object a bit simpler by offloading that work.

## Error reporting

Error reporting relies on being able to show as much information as possible
to the user about where something went wrong.

If an error occurred at a point
in original source, we can continue using the current output. (Well, we can
improve on that, but that's independent of substitutions.)

If an error occurred in the current source text that is a replacement, then
we need to provide different information. We can print out the line of
source from the current text, along with a pointer to the origin start
position in the original soruce that corresponds to the error position
in the current text. The purpose is to clarify where the error came from.
Some testing will be good to check that this feedback is what's most
useful.

## Methods, internally and for grammar-writers

The grammar can call the method

    parse.replace(...)

from the `parsed` method of a rule.
The method `parse.replace()` can act similarly to the `run.run()`
setup, where inputs can be either strings or rules. Rules are replaced by their
`src()` values, and this allows us to keep track of which substituted code
came from where - to a reasonable extent.

When `parse.replace` is called, it sets a global variable that tracks a list of
inputs to the iterator's split (or maybe "replace") method. If that global value
is set, we immediately make the changes to `iter` and recursively call parse again at the
original code point. This code is injected from the near-end point of an
otherwise normal and successful parse.

This way calling `parse` feels like it just works even when multiple
replacements may be happening before it completes.

In the future, I may want to put in a check against infinite substitution loops.


## Substitutions in the main grammar

There could be a new type of grammar statement of the form

    <rule_name> =| <new_rule_name>

which prepends `new_rule_name` to the beginning of `rule_name` as an or rule.
Maybe `|=` would append the new rule to the end of the list.

This can be used for substitutions since the new rule could be a substitution
that is checked for first.

All of the above fits into the core grammar. Now for the main grammar.

The main grammar might allow syntax like this:

    >! <existing_or_rule_name> <new_seq>
      <space-sep'd list of strings or tokens from seq>

this itself would be replaced by something like this:

    <existing_or_rule_name> =| <internal_seq_rule_name>
    <internal_seq_rule_name> -> <new_seq>
      : parse.replace(<comma-sep'd list of strings or tokens from seq>)

## Future: working with grammar states

We could learn from a common pattern in 2D drawing frameworks where the current
graphics state can be saved and loaded. This operation could wrap calls to
something like `require` so that poorly-written code that is `require`'d 
cannot change the grammar.

I can imagine some users wanting to turn off all grammar changes except
for substitutions. This is a little tricky because the replacement value
for the proposed subst grammar is a non-subst result. In other words, if we
just delete grammar-changning syntax from the grammar, we will in effect be
sabotaging substitutions as well. A possible workaround is to give replaced
source access to a larger grammar than original source. I haven't thought
about this carefully yet.

