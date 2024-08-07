import os
import argparse
import re
import json
import statistics
import numpy as np
from dataclasses import asdict

import pandas as pd
import tabulate
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth, exceptions
import boto3
from dotenv import load_dotenv

from config import TestResult, AveragedThroughput, AveragedServiceTime, AveragedLatency


def aggregate_rounds_results(client_details: dict, folder_path: str, output_name: str):
    # Client Creation
    client = create_opensearch_client(client_details)

    file_paths = get_test_execution_file_paths(folder_path)
    all_results = []

    # Read the files in the folder and load them into memory
    for file_name in file_paths:
        result_dict = get_data(file_name)
        all_results.append(result_dict)

    total_rounds = len(all_results)
    unique_test_ids = [result["test-pattern"] for result in all_results]
    # Get average throughput from all rounds
    average_throughput_class = build_average_throughput_class(all_results)
    # print(asdict(average_throughput_class))
    # Get average service time from all rounds
    average_service_time_class = build_average_service_time_class(all_results)
    # print(asdict(average_service_time_class))
    # Get average latency form all rounds
    average_latency_class = build_average_latency_class(all_results)
    # print(asdict(average_latency_class))

    # Generate dataclass and save as a json
    test_result = TestResult(unique_test_ids, average_throughput_class, average_service_time_class, average_latency_class)
    test_result_dict = asdict(test_result)
    print(test_result_dict)

    with open(f"{output_name}.json", "w") as file:
        json.dump(test_result_dict, file, indent=4)

    print(f"Outputted to file called {output_name}.json")


def build_average_throughput_class(all_round_results):
    AVERAGED_THROUGHPUT = "averaged-throughput"
    MIN = "min"
    MEAN = "mean"
    MEDIAN = "median"
    units = "ops/s"

    cumulative_min = []
    cumulative_mean = []
    cumulative_median = []

    for round_result in all_round_results:
        cumulative_min.append(round_result[AVERAGED_THROUGHPUT][MIN])
        cumulative_mean.append(round_result[AVERAGED_THROUGHPUT][MEAN])
        cumulative_median.append(round_result[AVERAGED_THROUGHPUT][MEDIAN])

    avg_min = statistics.mean(cumulative_min)
    avg_mean = statistics.mean(cumulative_mean)
    avg_median = statistics.mean(cumulative_median)

    rsd_min = (statistics.stdev(cumulative_min) / avg_min) * 100
    rsd_mean = (statistics.stdev(cumulative_mean) / avg_mean) * 100
    rsd_median = (statistics.stdev(cumulative_median) / avg_median) * 100

    # print(cumulative_min, cumulative_mean, cumulative_median)
    return AveragedThroughput(avg_min, rsd_min, avg_mean, rsd_mean, avg_median, rsd_median, units)

def build_average_service_time_class(all_round_results):
    AVERAGED_SERVICE_TIME = "averaged-service-time"
    P50_SERVICE_TIME = "50_0"
    P90_SERVICE_TIME = "90_0"
    P99_SERVICE_TIME = "99_0"
    P99_9_SERVICE_TIME = "99_9"
    P99_99_SERVICE_TIME = "99_99"
    P100_SERVICE_TIME = "100_0"
    units = "ms"

    cumulative_p50_service_time = []
    cumulative_p90_service_time = []
    cumulative_p99_service_time = []
    cumulative_p99_9_service_time = []
    cumulative_p99_99_service_time = []
    cumulative_p100_service_time = []

    for round_result in all_round_results:
        cumulative_p50_service_time.append(round_result[AVERAGED_SERVICE_TIME][P50_SERVICE_TIME])
        cumulative_p90_service_time.append(round_result[AVERAGED_SERVICE_TIME][P90_SERVICE_TIME])
        cumulative_p99_service_time.append(round_result[AVERAGED_SERVICE_TIME][P99_SERVICE_TIME])
        cumulative_p99_9_service_time.append(round_result[AVERAGED_SERVICE_TIME][P99_9_SERVICE_TIME])
        cumulative_p99_99_service_time.append(round_result[AVERAGED_SERVICE_TIME][P99_99_SERVICE_TIME])
        cumulative_p100_service_time.append(round_result[AVERAGED_SERVICE_TIME][P100_SERVICE_TIME])

    avg_p50_service_time = statistics.mean(cumulative_p50_service_time)
    avg_p90_service_time = statistics.mean(cumulative_p90_service_time)
    avg_p99_service_time = statistics.mean(cumulative_p99_service_time)
    avg_p99_9_service_time = statistics.mean(cumulative_p99_9_service_time)
    avg_p99_99_service_time = statistics.mean(cumulative_p99_99_service_time)
    avg_p100_service_time = statistics.mean(cumulative_p100_service_time)

    rsd_p50_service_time = (statistics.stdev(cumulative_p50_service_time) / avg_p50_service_time) * 100
    rsd_p90_service_time = (statistics.stdev(cumulative_p90_service_time) / avg_p90_service_time) * 100
    rsd_p99_service_time = (statistics.stdev(cumulative_p99_service_time) / avg_p99_service_time) * 100
    rsd_p99_9_service_time = (statistics.stdev(cumulative_p99_9_service_time) / avg_p99_9_service_time) * 100
    rsd_p99_99_service_time = (statistics.stdev(cumulative_p99_99_service_time) / avg_p99_99_service_time) * 100
    rsd_p100_service_time = (statistics.stdev(cumulative_p100_service_time) / avg_p100_service_time) * 100

    # print(cumulative_p50_service_time, cumulative_p90_service_time)
    return AveragedServiceTime(avg_p50_service_time, rsd_p50_service_time, avg_p90_service_time, rsd_p90_service_time, avg_p99_service_time, rsd_p99_service_time, avg_p99_9_service_time, rsd_p99_9_service_time, avg_p99_99_service_time, rsd_p99_99_service_time, avg_p100_service_time, rsd_p100_service_time, units)

def build_average_latency_class(all_round_results):
    AVERAGED_LATENCY = "averaged-latency"
    P50_LATENCY = "50_0"
    P90_LATENCY = "90_0"
    P99_LATENCY = "99_0"
    P99_9_LATENCY = "99_9"
    P99_99_LATENCY = "99_99"
    P100_LATENCY = "100_0"
    units = "ms"

    cumulative_p50_latency = []
    cumulative_p90_latency = []
    cumulative_p99_latency = []
    cumulative_p99_9_latency = []
    cumulative_p99_99_latency = []
    cumulative_p100_latency = []

    for round_result in all_round_results:
        cumulative_p50_latency.append(round_result[AVERAGED_LATENCY][P50_LATENCY])
        cumulative_p90_latency.append(round_result[AVERAGED_LATENCY][P90_LATENCY])
        cumulative_p99_latency.append(round_result[AVERAGED_LATENCY][P99_LATENCY])
        cumulative_p99_9_latency.append(round_result[AVERAGED_LATENCY][P99_9_LATENCY])
        cumulative_p99_99_latency.append(round_result[AVERAGED_LATENCY][P99_99_LATENCY])
        cumulative_p100_latency.append(round_result[AVERAGED_LATENCY][P100_LATENCY])

    avg_p50_latency = statistics.mean(cumulative_p50_latency)
    avg_p90_latency = statistics.mean(cumulative_p90_latency)
    avg_p99_latency = statistics.mean(cumulative_p99_latency)
    avg_p99_9_latency = statistics.mean(cumulative_p99_9_latency)
    avg_p99_99_latency = statistics.mean(cumulative_p99_99_latency)
    avg_p100_latency = statistics.mean(cumulative_p100_latency)

    rsd_p50_latency = (statistics.stdev(cumulative_p50_latency) / avg_p50_latency) * 100
    rsd_p90_latency = (statistics.stdev(cumulative_p90_latency) / avg_p90_latency) * 100
    rsd_p99_latency = (statistics.stdev(cumulative_p99_latency) / avg_p99_latency) * 100
    rsd_p99_9_latency = (statistics.stdev(cumulative_p99_9_latency) / avg_p99_9_latency) * 100
    rsd_p99_99_latency = (statistics.stdev(cumulative_p99_99_latency) / avg_p99_99_latency) * 100
    rsd_p100_latency = (statistics.stdev(cumulative_p100_latency) / avg_p100_latency) * 100

    # print(cumulative_p50_latency, cumulative_p90_latency)
    return AveragedLatency(avg_p50_latency, rsd_p50_latency, avg_p90_latency, rsd_p90_latency, avg_p99_latency, rsd_p99_latency, avg_p99_9_latency, rsd_p99_9_latency, avg_p99_99_latency, rsd_p99_99_latency, avg_p100_latency, rsd_p100_latency, units)


def get_data(result_file_path: str) -> dict:
    with open(result_file_path) as file:
        data = json.load(file)

    return data

def get_test_execution_file_paths(folder_path: str):
    test_execution_files = []
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path) and "avg" not in filename and ".json" in filename:
                test_execution_files.append(file_path)
    else:
        print("Folder path does not exist: ", folder_path)

    try:
        test_execution_files = sorted(test_execution_files, key=(lambda x: int(''.join(filter(str.isdigit, x)))))
    except:
        raise Exception("Files need to have the run number associated with it. Check folder directory to see if there are any file names without their associated run number or iteration. For example, to represent run 2 of a specific run, use test-execution-2.json instead of test-execution.json")

    return test_execution_files

def create_opensearch_client(client_details):
    client = OpenSearch(
        hosts = [f'{host}:{port}'],
        http_auth = (username, password),
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    return client

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Aggregate Results from Nodes from MDS')
    parser.add_argument('--folder', '-f', required=True, help='Folder of all rounds from autoscaling group tests')
    parser.add_argument('--output-name', '-n', required=True, help="Output filename to use")
    args = parser.parse_args()

    load_dotenv()
    host = os.getenv('MDS')
    port = 443
    region = os.getenv('AWS_REGION')
    username = os.getenv('MDS_USERNAME')
    password = os.getenv('MDS_PASSWORD')

    client_details = {
        "host": os.getenv('MDS'),
        "port": 443,
        "region": os.getenv('AWS_REGION'),
        "username": os.getenv('MDS_USERNAME'),
        "password": os.getenv('MDS_PASSWORD')
    }

    aggregate_rounds_results(client_details, args.folder, args.output_name)
