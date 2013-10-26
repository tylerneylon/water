#!/bin/bash
#
# update_correct_output.sh
#
# This script adds any missing <sample_name>.output files to the
# correct_output directory. It assumes that the current sample and
# the current version of water are both working correcty.
#

files_run=0
output_dir="correct_output"
for sample_file in *.water; do
  output_file="${output_dir}/${sample_file%%.*}.output"
  if [[ -f ${output_file} ]]; then continue; fi
  echo About to run water ${sample_file}
  water ${sample_file} > ${output_file}
  files_run=$[${files_run} + 1]
done
if [[ ${files_run} -eq 0 ]]; then
  echo "All files are already up to date."
else
  echo "Done; ${files_run} file(s) updated."
fi
