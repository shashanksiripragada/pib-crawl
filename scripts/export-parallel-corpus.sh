#!/bin/bash

set -x;

OUTPUT_DIR='non-src-archive/pib-export'
mkdir -p $OUTPUT_DIR;


for lang in hi ta te ml bn gu mr pa or ur
do
    python3 -m pib.export.export-parallel-corpus \
        --model mm-to-en-iter3 \
        --output-dir $OUTPUT_DIR \
        --src-lang $lang;
    

    python3 -m pib.export.filter-alignments \
        --model mm-to-en-iter3 \
        --output-dir $OUTPUT_DIR \
        --src-lang $lang;
done
