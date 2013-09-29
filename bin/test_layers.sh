#!/bin/bash
#
# test_layers.sh
#
# A way to quickly see how a change in water or the layer files
# will affect base_grammar.water.
#
water -commands all_layers.water --nonewlines | diff base_grammar.water -
