import argparse

import pandas as pd
import matplotlib.pyplot as plt


def main(filename, output_name, x_metrics, y_metrics):
    # Read the CSV file
    data = pd.read_csv(filename)
    print(data)

    # Extract the values from columns A and B
    x_values = data[x_metrics]
    y_values = data[y_metrics]
    print(y_values)



    # Create a line plot
    plt.figure(figsize=(10, 6))  # Set the figure size (width, height) in inches
    plt.plot(x_values, y_values)

    # Add labels and title
    plt.xlabel(x_metrics)
    plt.ylabel(y_metrics)
    plt.title(f"{x_metrics} vs {y_metrics}")

    # Save the plot as a PNG image
    plt.savefig(f"{output_name}.png", dpi=300, bbox_inches='tight')
    print(f"Outputted {output_name}.png")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot points of two columns in a CSV')
    parser.add_argument('--filename', '-f', required=True, help='File of averaged results to convert to CSV')
    parser.add_argument('--output-name', '-n', required=True, help='Output filename')
    parser.add_argument('-x', required=True, help='Column for x-axis')
    parser.add_argument('-y', required=True, help='Column for y-axis')
    args = parser.parse_args()

    main(args.filename, args.output_name, args.x, args.y)

