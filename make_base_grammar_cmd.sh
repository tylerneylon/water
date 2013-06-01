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

water -commands bootstrap.water --nonewlines > base_grammar.cmd.water
water -commands base_grammar.water >> base_grammar.cmd.water
