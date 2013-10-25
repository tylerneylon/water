#!/bin/bash
#
# convertjs.sh
#
# This script makes it easy to get the correct output from
# different js sources as I work on implementing js:tgp.
#

for f in {14..17}.water; do
  cat $f | egrep -v '^#' > ${f%.water}.js
done
