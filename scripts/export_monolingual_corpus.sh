
for LANG in hi en bn ta ml te or gu pa ur mr
do
    set -x;
    python3 -m pib.export.export-mono-corpus --lang $LANG --prefix non-src-archive/monolingual-exports/raw ;
    set +x;
done

