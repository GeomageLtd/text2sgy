import numpy as np
import struct
import matplotlib.pyplot as plt
import os
import argparse
from datetime import datetime

def read_segy_file(file_path, verbose=False):
    """
    Read a SEG-Y file and return its contents
    
    Parameters:
    file_path (str): Path to the SEG-Y file
    verbose (bool): Whether to print detailed information
    
    Returns:
    tuple: (ebcdic_header, binary_header, traces)
    """
    with open(file_path, 'rb') as f:
        # Read EBCDIC header (3200 bytes)
        ebcdic_header = f.read(3200)
        if verbose:
            print("EBCDIC Header:")
            try:
                # Attempt to decode EBCDIC to ASCII (simplified approach)
                header_text = ebcdic_to_ascii(ebcdic_header)
                print(header_text)
            except:
                print("Could not decode EBCDIC header")
        
        # Read Binary header (400 bytes)
        binary_header = f.read(400)
        
        # Extract key information from binary header
        sample_interval = struct.unpack('>H', binary_header[16:18])[0]
        num_samples = struct.unpack('>H', binary_header[20:22])[0]
        format_code = struct.unpack('>H', binary_header[24:26])[0]
        
        if verbose:
            print("\nBinary Header Info:")
            print(f"Sample interval: {sample_interval} microseconds")
            print(f"Number of samples per trace: {num_samples}")
            print(f"Data format code: {format_code}")
            
            # Determine data format
            format_desc = {
                1: "4-byte IBM floating-point",
                2: "4-byte two's complement integer",
                3: "2-byte two's complement integer",
                4: "4-byte fixed-point with gain",
                5: "4-byte IEEE floating-point",
                8: "1-byte two's complement integer"
            }
            print(f"Data format: {format_desc.get(format_code, 'Unknown')}")
        
        # Read trace data
        traces = []
        trace_count = 0
        
        # Continue reading until end of file
        while True:
            # Read trace header (240 bytes)
            trace_header = f.read(240)
            if len(trace_header) < 240:  # End of file
                break
                
            trace_count += 1
            
            # Extract trace header info
            trace_samples = struct.unpack('>H', trace_header[114:116])[0] or num_samples
            trace_interval = struct.unpack('>H', trace_header[116:118])[0] or sample_interval
            
            # Read trace data
            if format_code == 5:  # IEEE floating-point
                trace_data = np.array([struct.unpack('>f', f.read(4))[0] for _ in range(trace_samples)])
            elif format_code == 1:  # IBM floating-point
                trace_data = np.array([ibm_to_float(f.read(4)) for _ in range(trace_samples)])
            else:
                # Skip unsupported formats for now
                f.seek(4 * trace_samples, os.SEEK_CUR)
                trace_data = np.zeros(trace_samples)
                if verbose:
                    print(f"Warning: Unsupported data format {format_code}")
            
            traces.append(trace_data)
            
            if verbose and trace_count == 1:
                print(f"\nFirst Trace Header Info:")
                print(f"Number of samples: {trace_samples}")
                print(f"Sample interval: {trace_interval} microseconds")
        
        if verbose:
            print(f"\nTotal number of traces read: {trace_count}")
        
        return ebcdic_header, binary_header, traces

def ebcdic_to_ascii(ebcdic_bytes):
    """
    Simple EBCDIC to ASCII conversion for display purposes
    """
    # Very simplified EBCDIC to ASCII mapping for common characters
    result = ""
    for byte in ebcdic_bytes:
        if byte == 64:  # EBCDIC space
            result += " "
        elif 192 <= byte <= 201:  # EBCDIC numbers
            result += chr(byte - 192 + 48)
        elif 193 <= byte <= 218:  # EBCDIC uppercase
            result += chr(byte - 128)
        elif 129 <= byte <= 154:  # EBCDIC lowercase
            result += chr(byte - 32)
        elif byte == 96:  # EBCDIC hyphen
            result += "-"
        elif byte == 122:  # EBCDIC colon
            result += ":"
        else:
            result += "."
    
    # Split into 80-character lines (EBCDIC card image format)
    lines = [result[i:i+80] for i in range(0, len(result), 80)]
    return "\n".join(lines)

def ibm_to_float(bytes_data):
    """
    Convert IBM floating point format to IEEE floating point
    """
    # Simple implementation - for complete implementation, consider using a library
    # or implementing the full IBM to IEEE conversion
    try:
        return struct.unpack('>f', bytes_data)[0]
    except:
        return 0.0

def plot_segy(traces, sample_interval=1000, filename=None):
    """
    Plot SEG-Y trace data
    
    Parameters:
    traces (list): List of trace data arrays
    sample_interval (int): Sample interval in microseconds
    filename (str): Original filename for the plot title
    """
    if not traces:
        print("No traces to plot")
        return
    
    # Create time axis in milliseconds
    time_axis = np.arange(0, len(traces[0]) * sample_interval / 1000, sample_interval / 1000)
    
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Decide what to plot based on number of traces
    if len(traces) == 1:
        # Single trace - plot amplitude vs time
        plt.plot(time_axis, traces[0])
        plt.xlabel('Time (ms)')
        plt.ylabel('Amplitude')
        plt.title(f'SEG-Y Trace Data - {filename or ""}')
        plt.grid(True)
    else:
        # Multiple traces - create wiggle plot or image
        if len(traces) <= 50:
            # Wiggle plot for a reasonable number of traces
            for i, trace in enumerate(traces):
                # Normalize and offset each trace
                normalized = trace / (np.max(np.abs(trace)) or 1) * 0.5
                plt.plot(normalized + i, time_axis, 'k-', linewidth=0.5)
            plt.gca().invert_yaxis()  # Invert Y axis (time increases downward)
            plt.xlabel('Trace Number')
            plt.ylabel('Time (ms)')
            plt.title(f'SEG-Y Wiggle Plot - {filename or ""}')
            plt.grid(True)
        else:
            # Image plot for many traces
            data_matrix = np.array(traces).T  # Transpose for proper orientation
            plt.imshow(data_matrix, aspect='auto', cmap='seismic', 
                       extent=[0, len(traces), time_axis[-1], time_axis[0]])
            plt.colorbar(label='Amplitude')
            plt.xlabel('Trace Number')
            plt.ylabel('Time (ms)')
            plt.title(f'SEG-Y Image Plot - {filename or ""}')
    
    plt.tight_layout()
    plt.show()

def save_to_csv(traces, output_file, sample_interval=1000):
    """
    Save trace data to CSV file
    
    Parameters:
    traces (list): List of trace data arrays
    output_file (str): Output CSV file path
    sample_interval (int): Sample interval in microseconds
    """
    # Create time axis in milliseconds
    time_axis = np.arange(0, len(traces[0]) * sample_interval / 1000, sample_interval / 1000)
    
    # Open output file
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header
        header = ['Time (ms)'] + [f'Trace {i+1}' for i in range(len(traces))]
        writer.writerow(header)
        
        # Write data
        for i, time in enumerate(time_axis):
            row = [time] + [trace[i] for trace in traces]
            writer.writerow(row)
    
    print(f"Data saved to {output_file}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Read and display SEG-Y files')
    parser.add_argument('file', help='Path to the SEG-Y file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print detailed information')
    parser.add_argument('-c', '--csv', help='Save to CSV file')
    parser.add_argument('-p', '--plot', action='store_true', default=True, help='Plot the trace data')
    
    args = parser.parse_args()
    
    # Read the SEG-Y file
    try:
        _, binary_header, traces = read_segy_file(args.file, args.verbose)
        
        # Extract sample interval from binary header
        sample_interval = struct.unpack('>H', binary_header[16:18])[0]
        
        # Always output basic information
        print(f"File: {args.file}")
        print(f"Number of traces: {len(traces)}")
        if traces:
            print(f"Samples per trace: {len(traces[0])}")
            print(f"Sample interval: {sample_interval} microseconds")
        
        # Save to CSV if requested
        if args.csv:
            import csv
            save_to_csv(traces, args.csv, sample_interval)
        
        # Plot if requested
        if args.plot:
            plot_segy(traces, sample_interval, os.path.basename(args.file))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
