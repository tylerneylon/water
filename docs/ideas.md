# Ideas

Random small thoughts.

## Rename `False` to something like `NoMatch`

The analogy between what I call a `BoolRule` and the built-in rules
currently called `Empty` and `False` may not be clear to users.
For me, it's clear that `False` will never actually match anything, but
for the user, they're not used to thinking of rules as boolean values.

The analogy is also weakened by a sense that `Empty` is like `True`, but
in practice it will be useful as the *lack* of a match, so that it feels
more like false. For example, `Empty` will be the result when a question-marked
rule fails to match. In this case, the `Empty` result feels more like a negative
than a postiive.

The name `NoMatch` is acceptable, although it would be better if it were a
single word that was both short and clear in meaning.
