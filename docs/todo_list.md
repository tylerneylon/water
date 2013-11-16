# Todo items from the code

* Avoid setting a breakpoint if no output went to a tty?
`bin/dbg.py`:49

---

* If I want this back in, I need to get the parse_stack length from
input since the module dependencies will get sticky if I import parse.

`bin/dbg.py`:103

    def dprint(dbg_topic, text, end='\n'):
      ...
      #if dbg_topic == 'parse': text = '  ' * len(parse.parse_stack) + text

---

* Handle tuples from prefixes.
`bin/dbg.py`:156
in `def print_tree(obj, indent='  ', seq_item=None):`

---

* Improve how this works for mode results.
`bin/dbg.py`:157

    val = '[...]' if type(obj) is list else `obj`
    dprint('tree', '%s -> %s' % (seq_item, val))

---

* Change the comments below to reflect the latest mode syntax.
`bin/layer1.water`:6

---

* Check the accuracy of the above comment.
`bin/layer1.water`:50

Which refers to:

```
Note on strings:
"-delimited strings are regex's, '-ones are literals.
For "-strings, the parser converts \" to an internal " and otherwise
leaves escaped characters the same, which are converted within python
to whatever they represent. For '-strings, \' is still converted, also by
the parser, but otherwise everything else stays exactly the same.
```

---

* In many cases, I have \s where I mean \s but not \n.
`bin/layer1.water`:52

---

* Be able to clean up the syntax that looks like this: `mode_result.tokens[1].tokens[1].src()`
`bin/layer2.water`:6

---

* See if I can use `parse_string` more in this layer, such as from `combined_rule`.
`bin/layer2.water`:85

---

* Allow blank lines in code blocks
`bin/layer2.water`:142

---

* The infix rules have a lot of overlap; factor for cleanup.
`bin/layer2.water`:183

---

* Update these comments
`bin/layer2.water`:186, 205

```
def get_infix_star_rule(body, infix):
  # TODO update these comments
  # body_rule -> body
  # iplus_rule -->
  #   body_rule (infix)body_star
  # istar_rule[body_rule] --> iplus_rule | Empty
```

---

* In the star and plus rules, it would be nice if we could refer to item? by the name item.
`bin/layer2.water`:221

---

* Add 'public' output for `>:` commands.
`bin/parse.py`:30

---

* Pull this out into a modules & class that does not depend on parse.
`bin/parse.py`:74

    parse_info = None

---

* Make these available via command-line args.
`bin/parse.py`:78

    show_extra_dbg = False

---

* Think of a way to do this more cleanly.
`bin/parse.py`:157

```
  # Right now run._state is
  # awkwardly set from both parse and run.
  # For examle, maybe a command could set up its code_block as the body of an
  # add_code fn, and then call run.add on itself.
  run._state = {'start': self.start_pos, 'end': self.end_pos}
```

---

* (future): When I set up caching, I can update the cache about rules in the substs list (and add that info to the list).
`bin/parse.py`:167

---

* Rename opts to params everywhere in this file.
`bin/parse.py`:428

    def push_mode(name, params={}):

---

* Drop these lines. They may be useful for debugging in the meantime.
`bin/parse.py`:442

```
if False:
for rule_name in new_rules[mode_name]:
print('Officially adding the rule %s (mode %s)' % (rule_name, mode_name))
```

---

* Move all src functionality here. I think it's cleaner because the prefix handling is the same and would be more complex split up.
`bin/parse.py`:465

    def src(obj, incl_prefix=True):

---

* Reconsider when `incl_prefix` should be passed down. Unit tests would be good. I suspect the current code doesn't do this correctly.
`bin/parse.py`:467

    def src(obj, incl_prefix=True):

---

* needed?
`bin/parse.py`:474

    def src(obj, incl_prefix=True):

---

* Get this working. This is hard to work well before prefixes are properties of leaf-level strings (I think).
I plan to revisit this after prefixes are stored in the new way. Start by making sure 57.water works.
`bin/parse.py`:480

    bin/parse.py-483-def val(obj):

---

* Clean this up when refresh-rules-on-mode-pop is far enough along.
`bin/parse.py`:546

```
def _add_rule(rule, mode_name):
  global mode
  mode._pending_rules.setdefault(mode_name, {})[rule.name] = rule
  return rule
```

---

* Is this function needed? Delete if not.
`bin/parse.py`:560

```
  # Returns a, b for 'a@b', or None, b for @-free items.
  def _parse_at_syntax(item):
    pass
```

---

* This can only happen with a `'.-mode_name'` item, which is planned to be replaced by `prefix_changes` at mode starts. Get rid of this case both here and in layer1.water on the `mode_result` rule definition - that is, after we can handle the new mode-start prefix_changes.
`bin/parse.py`:610

```
if c == '.':
  #print('ERROR: This case was supposed to be gone')
```

---

* If a prefix parse fails, we need to back up the iterator.
`bin/parse.py`:650

    def _parse_prefix(it, prefix_list=None):

---

* Add public documentation.
`bin/tests.py`:7

    tests.py (top-of-file comments)

---

* Add public documentation.
`bin/water.py`:7

    water.py (top-of-file comments)

---

* I just realized I'm not using the terms src & code consistently.
Go back and change many uses of code -> src.
To be clear to myself: 'src' means the input, 'code' is the output sent to the runtime during normal operation.
`modules/showwork/showwork.py`:100

---

* Figure out how to allow this fn to be callable from `add_code` blocks.
`samples/good/12.water`:10

```
>:
  def push_value(rule):
    run.add(rule)
    run.add("['value']")
```

---

* If I replace `statement` with `statement --> Empty`, we get stuck in a loop. Could we notice this and warn the user about it?
`samples/good/23.water`:6

---

* Consider being able to optionally define methods on or rules. Not sure yet that it's the right thing to do.
`samples/good/24.water`:5

---

* If the first line is s += 0, we should see an error.
`samples/good/7.water`:6

---

* Make sure dot notation works for referencing nested labels and pieces.

---

* Looking at substitution steps, I see lots of inefficiencies, such
  as many one-rule rules. I could try to reduce those in automated
  expansion. Optimizing them away later seems tricky as users may
  change the grammar later and have reasonable behavior expectations
  that are destroyed by an optimizer.

