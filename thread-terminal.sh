$1

for i in $(seq 0 $1)
do
	minicom -c on -b 115200 -D /dev/ttyACM$1
done
