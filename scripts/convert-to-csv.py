import pandas as pd
import argparse
import numpy as np
import json

def main(filename, output_name):
    # Read the JSON file
    with open(filename, 'r') as f:
        data = json.load(f)

    # Extract the metric names and values from the nested dictionaries
    metric_names = []
    metric_values = []

    ids = [id for id in data['test_pattern']]
    ids = ",".join(ids)
    metric_names.append("test-pattern")
    metric_values.append(ids)

    metrics = ['averaged_throughput', 'averaged_service_time', 'averaged_latency']
    for metric in metrics:
        for key, value in data[metric].items():
            if isinstance(value, (int, float)):
                metric_names.append(key)
                metric_values.append(np.round(value, decimals=2))
                # metric_values.append(value)

    # Create a DataFrame from the metric names and values
    df = pd.DataFrame({'metric_name': metric_names, 'metric_value': metric_values})

    # Save the DataFrame as a CSV file
    df.to_csv(f"{output_name}.csv", index=False)
    print(f"Outputted to {output_name}.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert Averaged Results to CSV')
    parser.add_argument('--file', '-f', help='File of averaged results to convert to CSV')
    parser.add_argument('--output-name', '-n', required=True, help='Output filename to use')
    args = parser.parse_args()

    main(args.file, args.output_name)
