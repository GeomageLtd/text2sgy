import numpy as np
import os
import struct
from datetime import datetime
import csv  # Importing the csv module
import argparse  # For command line arguments

def read_text_data(file_path):
    """
    Read a text file with one sample per line or a CSV file with Time and Value columns
    """
    if file_path.endswith('.csv'):
        # Read CSV file
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            samples = [float(row[1]) for row in reader if row and len(row) > 1]
    else:
        # Read text file
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Convert lines to float values
        samples = [float(line.strip()) for line in lines if line.strip()]
    
    return np.array(samples)

def create_segy_file(input_file, output_file, sample_interval=2000):
    """
    Convert text file with amplitude values to SEG-Y format
    
    Parameters:
    input_file (str): Path to the input text or CSV file
    output_file (str): Path to the output SEG-Y file
    sample_interval (int): Sample interval in microseconds (default: 2000 = 2ms)
    """
    # Read the sample data
    data = read_text_data(input_file)
    
    # Get number of samples
    num_samples = len(data)
    
    # Create output file
    with open(output_file, 'wb') as f:
        # Write EBCDIC header (3200 bytes)
        ebcdic_header = create_ebcdic_header()
        f.write(ebcdic_header)
        
        # Write Binary header (400 bytes)
        binary_header = create_binary_header(num_samples, sample_interval)
        f.write(binary_header)
        
        # Write trace data
        write_trace(f, data, sample_interval)
    
    print(f"Successfully converted {input_file} to SEG-Y format: {output_file}")
    print(f"Number of samples: {num_samples}")

def create_ebcdic_header():
    """
    Create EBCDIC header (3200 bytes)
    """
    # Create a header with spaces (ASCII 32)
    header = bytearray([64] * 3200)  # 64 is EBCDIC for space
    
    # Add some basic information (in EBCDIC)
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # Convert ASCII to EBCDIC (simplified)
    header_text = f"C01 CONVERTED FROM TEXT FILE {date_str}"
    
    # Simple ASCII to EBCDIC conversion for basic text
    for i, char in enumerate(header_text[:80]):
        # Very simplified ASCII to EBCDIC mapping for common characters
        if ord(char) == 32:  # space
            header[i] = 64
        elif 48 <= ord(char) <= 57:  # numbers 0-9
            header[i] = ord(char) + 192
        elif 65 <= ord(char) <= 90:  # uppercase A-Z
            header[i] = ord(char) + 128
        elif 97 <= ord(char) <= 122:  # lowercase a-z (convert to uppercase in EBCDIC)
            header[i] = ord(char) - 32 + 128
        elif char == '-':
            header[i] = 96
        elif char == ':':
            header[i] = 122
            
    return bytes(header)

def create_binary_header(num_samples, sample_interval=2000):
    """
    Create Binary header (400 bytes)
    
    Parameters:
    num_samples (int): Number of samples in the trace
    sample_interval (int): Sample interval in microseconds (default: 2000 = 2ms)
    """
    # Initialize with zeros
    header = bytearray(400)
    struct.pack_into('>H', header, 16, sample_interval)
    
    # Bytes 3227-3228 (3-4): Number of samples per trace
    struct.pack_into('>H', header, 20, num_samples)
    
    # Bytes 3229-3230 (5-6): Data sample format code
    # 1 = 4-byte IBM floating-point
    # 5 = 4-byte IEEE floating-point
    format_code = 5  # IEEE floating-point
    struct.pack_into('>H', header, 24, format_code)
    
    # Bytes 3501-3502 (277-278): SEG-Y Revision number
    # 0x0100 = Revision 1.0
    struct.pack_into('>H', header, 300, 0x0100)
    
    # Bytes 3503-3504 (279-280): Fixed length trace flag
    # 1 = all traces have the same number of samples
    struct.pack_into('>H', header, 302, 1)
    
    # Bytes 3505-3506 (281-282): Number of extended textual headers
    # 0 = no extended headers
    struct.pack_into('>H', header, 304, 0)
    
    return header

def write_trace(f, data, sample_interval=2000):
    """
    Write a single SEG-Y trace
    
    Parameters:
    f (file): Output file object
    data (numpy.ndarray): Array of trace samples
    sample_interval (int): Sample interval in microseconds (default: 2000 = 2ms)
    """
    # Create trace header (240 bytes)
    trace_header = bytearray(240)
    
    # Set important values in trace header
    # Bytes 115-116: Number of samples in this trace
    num_samples = len(data)
    struct.pack_into('>H', trace_header, 114, num_samples)
    
    # Bytes 117-118: Sample interval in microseconds
    struct.pack_into('>H', trace_header, 116, sample_interval)
    
    # Write trace header
    f.write(trace_header)
    
    # Write trace data samples as IEEE floating-point (4 bytes each)
    for sample in data:
        f.write(struct.pack('>f', sample))

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Convert text/CSV data to SEG-Y format')
    parser.add_argument('input_file', type=str, help='Path to the input text or CSV file')
    parser.add_argument('-o', '--output', type=str, help='Path to the output SEG-Y file (default: input filename with .sgy extension)')
    parser.add_argument('-s', '--sample-interval', type=int, default=2000, 
                        help='Sample interval in microseconds (default: 2000 = 2ms)')
    
    # Parse arguments
    args = parser.parse_args()
    
    input_file = args.input_file
    output_file = args.output
    
    # If no output file is specified, use the input filename with .sgy extension
    if not output_file:
        output_file = os.path.splitext(input_file)[0] + '.sgy'
    
    # Get the sample interval
    sample_interval = args.sample_interval
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        return
    
    # Convert the file
    try:
        create_segy_file(input_file, output_file, sample_interval)
    except ValueError as e:
        print(f"Error: {e}")
        return

if __name__ == "__main__":
    main()