#!/bin/bash
#
# test.sh
#
# This script checks the current output of water run on each
# sample file against its output in the correct_output directory.
#
# If the correct output is missing, a warning is printed, but the
# sample is still considered to pass.
#

trap "echo Quitting early.; exit" SIGINT

output_dir="correct_output"
for sample_file in *.water; do
  output_file="${output_dir}/${sample_file%%.*}.output"
  if ! [[ -f ${output_file} ]]; then
    echo "WARNING: ${sample_file} is missing its output file ${output_file}."
    continue
  fi
  echo -n "About to run water ${sample_file}: "
  if water ${sample_file} | diff ${output_file} - > /dev/null; then
    # They match.
    echo Passed.
  else
    # They don't match.
    tput setaf 1  # Set terminal color to red.
    echo Failed.
    tput sgr0     # Reset terminal color to default.
  fi
done
