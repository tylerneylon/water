# Current Goal: New Syntax

These are the steps I plan to take
to implement the new grammar-specification syntax:

1. Support property delegation in `Object` *DONE*

2. Add property delegation to `OrRule` *DONE*

3. Add `or_index` to `OrRule` *DONE*

4. Add label support *DONE*

5. Switch `FalseRule` to `BoolRule` with instances `False` and `Empty` *DONE*

6. Factor out item parsing *DONE*

7. Add `!` prefix *DONE*

8. Switch `->` to `-->` in current grammar *DONE*

9. Add support for methods on `OrRule`s *DONE*

10. Add grammar for mixed or/seq rules *DONE*

11. Add grammar for grouping *DONE*

12. Add `?` grammar

13. Add `*`, `+` grammar

## Notes

* Later, I may want to come back and make sure dot notation works for
  referencing nested labels and pieces.
