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

### Examples

This syntax is further explained below, but a few quick JavaScript
examples might help to show what's going on:

    if_stmnt -> 'if' ( expr ) block:then (( 'else' (( if_stmnt | block )) ))?
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

I'll write this section as a stream of thought, and maybe clean it up later.

How little is needed in a core grammar?

I hope the rules can remain simply `OrRule` and `SeqRule`, as well as
the occasional `BoolRule` for the canonical `True` and `False` rules.

I am probably overusing the word `rule`, and should distinguish between
`items`, which are non-special strings in a grammar spec; vs `rule`s as
in objects of type `Rule`. So an `item` could be `args*,` or `'function'`
or `."[0-9]"?`, but not `((` or `))`, and considered as a string.

### Or/Seq split

How will we handle the fact that rules can combine or-parts and seq-parts?

If a rule is just a seq, it becomes a `SeqRule`.
Otherwise, it has or-parts, and those parts become internally-named
`SeqRule`s, while the overall rule is an `OrRule`. Internal names
start with an underscore.

It seems cleaner to keep `OrRule` methods
on the actual `OrRule` instead of duplicating them across the
internal `SeqRule`s. The current setup assumes methods are run
directly on the owning rule with the parsed pieces. A way to
deal with this is to set up method calls on `OrRule`s to get
their locals from their `self.result` value.

#### `or_index`

It may be useful for methods to know which of their or-list was
successfully parsed. So I suggest that all `OrRule`s have an
`or_index` property with the 0-based index of the successfully
parsed piece.

I also suggest that all unrecognized property lookups on an
`OrRule` be delegated to their `result`. Are there any negative
consequences of that approach? Since every `result` is a `SeqRule`,
it seems that delegation will always be at most one level deep.
At first glance, this approach seems good to me.

### Grouping

I feel like grouping can be left out of the core. How?

For every group, replace it with an internally-named rule.
This can even be done by substitution, I think.

I think that actually covers everything for subgroups, because
prefixes, labels, and suffixes will all continue to work fine
with a rule name instead of a subgroup, and we do not need to
provide explicit access to pieces of a subgroup by name.

But then, how will people access the various pieces of a subgroup?
No methods can be defined on it. It would be convenient if I could
access variables by name like this:

    a (( b | c )):grp        # Access grp.or_index
    a (( b c )):grp          # Access grp.b
    a (( b c | d e)):grp     # Access grp.d if grp.or_index == 1

I think these will all work under the current design, with the
caveat that I can't remember if per-name `SeqRule` pieces are
actually properties of the object or just appear that way to
methods. I'd like to make sure they're genuine object properties,
with some sanity check that a name collision doesn't do anything
too harmful (goal: prevent accidental mistakes ; not worrying
about malicious users for now).

### Prefixes

I already handle `.` prefixes.

The `!` prefix is straightforward to implement internally.
Can I handle it with a substitution or non-core rule?
I think no because it's hard to undo a successful parse
non-internally.

### Suffixes

Suffixes also seem tricky to handle outside the core because of
property naming. We could rename properties in a `parsed` method,
but that feels a little invasive.

Let's explore the option anyway.

How would `x+` work? It could be

    x x*

with some follow-up work to make it a single list. Ok, let's explore
`x*`. This could be

    _x_star -> x _x_star | True

but then how would the property lookups occur? For example, this rule:

    a -> x x* x

would expect to have ... what? I just realized this is an ambiguous
case for value naming.

Ok, let's try using `x_list` for all list versions of `x` and just `x` for
non-list items. (By "list items" I mean anything using a `+` or `*` suffix.)

I think we can implement `+` and `*` using non-core rules that set up
methods on internally-made rules.
For example, `_x_star` above could have a `_list` method which returns
`[x] +  _x_star.list()`.

A better implementation for `x+` might be as

    _x_plus -> x _x_star | x

and this can have a `_list` method that works similarly.

One tricky part will be inserting the names as properties (eg having the value
of `x_list` appear correctly to method calls on a rule using `x*`),
but I think we can do that
correctly in one of the non-core layers.
I think we can accomplish this with labels; for example the line

    fn_decl -> name ( arg*, )

could be replaced with

    fn_decl -> name ( _arg_star__2c:arg_list )

where I used `_2c` to represent a comma with the goal of avoiding
internal name clashes (not guaranteed to be avoided but I think good enough).

#### The `?` suffix

We might also be able to do this outside of the core, in a manner similar
to the other suffixes. The only tricky part I anticipate is setting the
value to `None` on a non-match. Actually, we can handle that by having
a `True` rule always return a `None` value. But then how will we tell
when a parse has been successful or not?

I propose we change `True` to `Empty` and see if we can get it to
evaluate to `False` in Python. Thus the two canonical `BoolRule`
values become `False` and `Empty`, and the no-match value of a
`?` rule becomes `Empty` (as a `result` value).

We can use an internal rule like the following for `x?`.

    x_ques_ -> x | Empty

### Labels

I think labels will be easiest to implement in the core parser.
Basically, the properties known to a rule need to be established
by the time the main `parsed` body is called, and I don't know of
a way to hook that method before the main body is called.

### Left-recursion

Some users might want to write a rule like this:

    expr -> expr + expr | expr * expr | number

which may be useful for operator precedence.

The current implementation would loop on this, but Dan suggested
short-circuiting such recursion, which seems like a good idea.
Harder to use incorrectly.

My suggested implementation for this is to augment the `parse_stack`
with not only rule names, but also parse locations, which would be
`(version, text_pos)` pairs.

Since an `OrRule` may be hit multiple times in a meaningful way, but
`SeqRule`s cannot, I think it makes sense to only notice recursion
for `SeqRule`s.

The above example would be broken down like this:

    expr -> _sub_expr_1 | _sub_expr_2 | number
    _sub_expr1 -> expr + expr
    _sub_expr2 -> expr * expr

Consider this on the input

    1 * 2 + 3 * 4

First we hit `_sub_expr_1` which recurses into `expr`. Then we hit
`_sub_expr_1` again, but it notices the recursion and fails. So the
second `expr` parse moves on to `_sub_expr_2`, which goes down into
`expr` again, and this time (due to noticing recursion), only a
number will be accepted.

Ultimately, I believe this behavior is as desired, and the resulting
parse tree will be:

          +
        /   \
       /     \
      *       *
     / \     / \
    1   2   3   4

Hm, but what about this next expression?

    1 + 2 + 3

This is interesting. If the short-circuit system ignored `text_pos`,
then we'd get `1 + 2` as an `expr` but that would be seen as the entire
`expr`, and we'd probably get a parse error at the next `+`.

Since we're taking `text_pos` into account, I think it ends up looking
for `expr` at the location of `2`, so it gets `2 + 3` as a subexpression.
This is *almost* right, except that for actual numerical expressions, we
usually want the operations to be evaluated left-to-right.

In other words, with the above setup, we'll get this parse tree for `1 - 2 - 3`:

        -
       / \
      /   -
     /   / \
    1   2   3

which (incorrectly) evaluates to 2. The tree we want (mathematically) is:

        -
       / \
      -   \
     / \   \
    1   2   3

which correctly evaluates to -4.

I have a vague idea for parsing infix operators in the correct order,
which is a more complex parsing system. I'm not ready to formalize this yet,
but I can hand-wavily describe the algorithm with an example.

I'll consider an example for the rule:

    expr -> expr - expr | number

For the expression `1 - 2 - 3`, it would work like this:

     1. expr on 1 - 2 - 3
     2. expr -> "expr - expr" on 1 - 2 - 3
     3. expr -> "expr - expr" -> expr on 1 - 2 - 3
     4. expr -> "expr - expr" -> expr -> "expr - expr" on 1 - 2 - 3
     5. *loop noticed, autofail and flag "expr - expr" as SC'd*
     6. expr -> "expr - expr" -> expr -> number on 1 - 2 - 3; SUCCESS
     7. expr -> .."- expr" on - 2 - 3; SUCCESS
     8. expr -> .."expr" on 2 - 3
     9. expr -> .."expr" -> "expr - expr" on 2 - 3
    10. *loop noticed*
    11. expr -> .."expr" -> number on 2 - 3; SUCCESS
    12. expr almost done as 1 - 2, but we had looping under expr -> "expr - expr",
        so try to consider the current expr as the left part of "expr - expr", continue as:
    13. expr -> .."- expr" on - 3 (with .. set to 1 - 2)

I need to think more about the general behavior of this system.
It may be better in the end to simply consider left-recursion as an error,
or to stick with the simpler fail-on-second-parse idea.

For now, I consider the new syntax to be complete without the need to
completely resolve how we handle infix operators and left recursion.
I'll leave those to a future work iteration, and probably another
design doc.

### Summary

Much of this work can be done outside the core grammar.

#### Core work

The core in `parse.py` must be able to handle a `BoolRule`, and must
be able to delegate more effectively from an `OrRule` to its `result`.
I'd like to add an `or_index` to `OrRule`s. I'd like refactor
the way `SeqRule` parses so that individual item parses happen in their
own function (this is more of a refactor than a part of the new syntax).
We will also need to build in support for the `!` prefix, as well
as labels.

#### Non-core work

The suffixes `+`, `*`, and `?` can be handled with a combination of special
parsing rules and labels.

Groups can be handled by special parsing rules, as can rules that combine
or-lists and seq-lists on a single line.

## Naming convention

A small set of common names can live in user space, and we expect all
users to know about them. They are (so far):

* `phrase`
* `comment`
* `statement`
* `expr`
* `parsed`
* `mode_params`

Other core names will be double-underscored (they aren't yet) like this:

* `__word`
* `__item`
* `__str`

They still live in the user namespace (everything does), but we want to
make it harder to accidentally screw things up.

There's an intermediate realm for rules created programmatically, and
these can have single-underscore prefixes, like this:

* `_subst_0`
* `_subst_1`
* `_x_star`





