import numpy as np
import os
import struct
from datetime import datetime

def read_text_data(file_path):
    """
    Read a text file with one sample per line
    """
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Convert lines to float values
    samples = [float(line.strip()) for line in lines if line.strip()]
    return np.array(samples)

def create_segy_file(input_file, output_file):
    """
    Convert text file with amplitude values to SEG-Y format
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
        binary_header = create_binary_header(num_samples)
        f.write(binary_header)
        
        # Write trace data
        write_trace(f, data)
    
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

def create_binary_header(num_samples):
    """
    Create Binary header (400 bytes)
    """
    # Initialize with zeros
    header = bytearray(400)
    
    # Set important values
    # Bytes 3225-3226 (1-2): Sample interval in microseconds (default to 1000 = 1ms)
    sample_interval = 2000
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

def write_trace(f, data):
    """
    Write a single SEG-Y trace
    """
    # Create trace header (240 bytes)
    trace_header = bytearray(240)
    
    # Set important values in trace header
    # Bytes 115-116: Number of samples in this trace
    num_samples = len(data)
    struct.pack_into('>H', trace_header, 114, num_samples)
    
    # Bytes 117-118: Sample interval in microseconds
    sample_interval = 1000  # 1ms
    struct.pack_into('>H', trace_header, 116, sample_interval)
    
    # Write trace header
    f.write(trace_header)
    
    # Write trace data samples as IEEE floating-point (4 bytes each)
    for sample in data:
        f.write(struct.pack('>f', sample))

def main():
    # Get input and output filenames
    input_file = input("Enter the input text file path: ")
    output_file = input("Enter the output SEG-Y file path (or press Enter to use the same name with .sgy extension): ")
    
    if not output_file:
        # Use the same name but with .sgy extension
        output_file = os.path.splitext(input_file)[0] + '.sgy'
    
    # Convert the file
    create_segy_file(input_file, output_file)

if __name__ == "__main__":
    main()
