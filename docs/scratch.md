# Scratch notes

This is a place for temporary notes as I work.

## Thinking on how to implement `+` and `*`

    a -> (( hello | there ))* other_stuff

should become

    a -> _inner_34 other_stuff
    
    _inner_34 -> (( body )) _inner_34 | Empty

I might want to be able to handle labels already on the item.

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
