declare -a arr=("or" "pa")


for i in "${arr[@]}"
do
   echo "$i"
   python align_new.py $i en
done