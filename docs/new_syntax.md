# New syntax

Notes on an update for the base grammar.

## Human-friendly syntax description

A general statement is of the form

    rule_name -> seq1 | seq2 | seq3

I'll give a bottom-up
explanation for the `seq` parts.

A primitive is either a rule_name, a single-quoted string,
a double-quoted string, or non-special punctuation.

The following are special punctuation:

    | (( ))

but are only recognized as special when they're surrounded
by spaces.
These are also special punctuation:

    . ! + * ?

but are only recognized as special when part of a
non-punctuation rule, explained further below.

Single-quoted strings are interpreted as literals.
Double-quoted strings are interpreted as regular expressions.

The `|` operator separates or-items, and separates top-level
items; in other words, it is a last-evaluated operator.

Anything inside a `(( ))` pair is a subrule, allowing nested
or-items, and more interesting constructions with the suffixes
described below.

### Example

This syntax is further explained below, but a few quick JavaScript
examples might help to show what's going on:

    if_stmnt -> 'if' ( expr ) block:then (( 'else' if_stmnt? block ))?
    obj_lit -> { (( (( name  |  str_lit )) : expr ))*, }

Here's a group of rules that work together:

    num_lit -> integer fraction? exponent?
    integer -> '0' | "[1-9]" digit*
    fraction -> . digit+
    exponent -> "[eE]" "[+-]?" digit+
    digit -> "[0-9]"

### Suffixes

If a non-punctuation rule is followed by `+` or `*`, then it
becomes a list of that rule, similar to a regular expression.
If a rule follows the `+` or `*`, then that rule is treated
as a separator between items of the list. For example, the
sequence

    word ( arg*, )

could match any of the following (ignoring inter-token spacing for now):

    factorial(n)
    max(x, y)
    exit()

this next item would fail, though, due to missing separators:

    print("hi %s" % 'there')

If a non-punctuation rule is followed by `?`, then a parse failure
on that rule is acceptable (it doesn't break the overall seq parse).
The result is a `None` value if the rule fails.

As a best practice, I recommend that punctuation rules not end
in `+`, `*`, or `?`, as this case can be confusing. The current system
would interpret the rule `=+` as a literal, although some users
might expect it to mean 1 or more `=` rules. I suggest the following
use patterns:

    Use '=+'    to mean the literal =+
    Use '='+    to mean 1 or more =
    similarly for * and ?
    (=+ would be interpreted as a literal)
    ---
    Use .'='    to mean = preceded by no prefix.
    Use '.='    to mean the literal .=
    similarly for !
    (.= would be interepreted as a literal)

### Modes

A rule of the form `-mode_name` is intended as a mode.
For now, only one mode is expected per rule.
I may also only allow a mode rule at the end of a sequence,
but I can't remember whether or not the current implementation
allows earlier mode rules.

### Prefixes

The punctuation `.` and `!` have special meanings when they
precede a non-punctuation rule.

A `.` means the prefix is effectively the empty string
before and within the rule name that follows it. For example,
if the prefix is set to whitespace, then the rule `.'hello'`
means the literal `hello` must immediately follow whatever
was last parsed - no whitespace. This is even more powerful
in the case of a named rule, such as `.-str`, which effectively
makes everything parsed in mode `str` to have no prefix.

A `!` means to give a parse failure if the rule afterwords
succeeds, and give an empty success (like the `True` rule)
if it fails. This is intended for use as part of a sequence where,
for example, keywords must be filtered out. For example,

    'var' !keyword name = expr ;

will succeed on

    var x = 3;

and fail on

    var function = 5;

assuming `function` is a keyword.

### Labels

Any rule followed by `:label` gets a temporary (within the rule
being defined) alternative name that may add readability and
allow for cleaner method bodies. It's expected that labels
be placed before any suffixes.

## Variable names and values

Variable assignment proceeds in two stages:

1. Every name in the rule starts as a list.
2. If a `?` item is missing, a `None` value is added.
2. Once parsing is complete, any names with a length-one list become a single item.

Values inside `(( ))` pairs aren't named unless the pair is given a label,
like this:

    expr (( + | - )):op expr

in which case `op` gets the value of the anonymous rule inside the `(( ))` pair.

Listed rules — meaning rules followed by a `+` or `*` — keep their same name.
For example, in the rule

    word ( arg*, )

the list of args is called `arg` even though it is a singular noun.

The `tokens` list works as before, although now it will only refer to the
or-item that succeeded (as will all variable names).

Rules preceded by `!` will be left out of both `tokens` and the named parameters.

## Implementation notes

TODO
