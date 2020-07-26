for var in ta te ml bn gu mr pa or
do
python3 -m webapp.cli.export-parallel-corpus --src_lang $var --tgt_lang en --model mm-to-en-iter1
python3 -m webapp.cli.filter-alignments --src_lang $var --tgt_lang en --model mm-to-en-iter1
done