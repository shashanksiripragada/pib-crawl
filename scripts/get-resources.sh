DB=./pib
ILMULTI=$HOME/.ilmulti

mkdir -p $ILMULTI


url="http://preon.iiit.ac.in/~jerin/resources/datasets/pib-crawled.db.tar.gz" 

file=$DB/pib-crawled.db.tar.gz

if [ -f $file ]; then
    echo "$file already exists, skipping download"
else
    wget --user-agent="Mozilla/5.0" $url
    #curl $url
    if [ -f $file ]; then
        echo "$url successfully downloaded."
    else
        echo "$url not successfully downloaded."
        exit 1
    fi
    if [ ${file: -4} == ".tgz" ]; then
        tar zxvf $file
    elif [ ${file: -4} == ".tar" ]; then
        tar xvf $file
    elif [ ${file: -7} == ".tar.gz" ]; then
        tar xvf $file
    fi
fi

mv *.db $DB/ 