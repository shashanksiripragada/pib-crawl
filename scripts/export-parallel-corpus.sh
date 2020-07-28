for lang in hi ta te ml bn gu mr pa or ur
do
python3 -m pib.export.export-parallel-corpus --src_lang $lang 
python3 -m pib.export.filter-alignments --src_lang $lang
done