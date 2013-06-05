#!/bin/bash
#
# make_base_grammar_cmd.sh
#
# Run this command to generate the file base_grammar.cmd.water,
# which is used by parse.py to know the common base grammar used
# to parse all other water files.
#
# This script uses the commands module along with the files
# bootstrap.water and base_grammar.water.
#

# Use a temporary file since a redirected output destination cannot
# be read from; e.g. "cat file > file" will result in file being empty,
# no matter what it started with.
water -commands base_grammar.water --nonewlines > tmpfile
mv tmpfile base_grammar.cmd.water
