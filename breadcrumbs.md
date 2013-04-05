What I'm in the middle of:

Reimplementing the parsing engine in water3.py
to be based on classes.

The goal is to first still be able to parse sample1.water by running:

./water3.py sample1.water

without having a ton of token-specific code.

Take a look at language definition2.water to see the direction I'm headed in.

Here are my upcoming items:

[ ] Drop tokens internally (in progress)

[ ] Turn code output function into a data-based system

[ ] Clean up the current code, such as considering named tuples, refactoring, and in general aiming for elegance

[  ] (to be split up) Be able to read in and act on the language definition file.

