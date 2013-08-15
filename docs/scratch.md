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
