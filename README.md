# text2sgy

# Use default sample interval (2 ms)
python txt2sgy.py data.txt

# Specify 1 ms sample interval (1000 microseconds)
python txt2sgy.py data.txt -s 1000

# Specify both sample interval and output file
python txt2sgy.py data.csv --sample-interval 4000 --output converted.sgy

# read_sgy
# Basic usage - read and display file info
python read_sgy.py your_file.sgy

# Read with verbose output
python read_sgy.py your_file.sgy -v

# Read, display info, and plot
python read_sgy.py your_file.sgy -p

# Read and save to CSV
python read_sgy.py your_file.sgy -c output.csv

# All options combined
python read_sgy.py your_file.sgy -v -p -c output.csv