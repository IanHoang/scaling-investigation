import re
import argparse

'''
Prerequisites: Cat a benchmark.log file and grep for "reached join point for index". Copy the output for the workers that relate to a specific time or test and paste it into a file. Then run the script.
'''
def sort_log_file(input_file, output_file):
    with open(input_file, 'r') as file:
        log_lines = file.readlines()

    pattern = r'Worker\[(\d+)\]'

    log_entries = []
    for line in log_lines:
        match = re.search(pattern, line)
        if match:
            worker_number = int(match.group(1))
            log_entries.append((worker_number, line))

    log_entries.sort(key=lambda x: x[0])

    with open(output_file, 'w') as file:
        for worker_number, line in log_entries:
            file.write(line)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sort log file based on Worker number')
    parser.add_argument('-f', '--file', type=str, required=True, help='Input log file')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output sorted log file')
    args = parser.parse_args()

    sort_log_file(args.file, args.output)
