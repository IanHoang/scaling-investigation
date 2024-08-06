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


def aggregate_rounds_results(client_details: dict, test_execution_id_pattern: str, output_name: str):
    # Client Creation
    client = create_opensearch_client(client_details)

    # Since we're aggregating rounds of a specific test configuration, we should be using a pattern
    documents = get_documents(client, test_execution_id_pattern)

    # Filter the metrics and get a cumulative avg of all results
    unique_test_ids, throughput_documents, service_time_documents, latency_documents = filter_documents(documents)
    unique_test_ids = sorted(unique_test_ids)

    # Get average throughput from all rounds
    average_throughput_class = build_average_throughput_class(throughput_documents)
    # print(asdict(average_throughput_class))

    # Get average service time from all rounds
    average_service_time_class = build_average_service_time_class(service_time_documents)
    # print(asdict(average_service_time_class))

    # Get average latency form all rounds
    average_latency_class = build_average_latency_class(latency_documents)
    # print(asdict(average_latency_class))

    # Generate dataclass and save as a json
    test_result = TestResult(unique_test_ids, average_throughput_class, average_service_time_class, average_latency_class)
    test_result_dict = asdict(test_result)
    print(test_result_dict)

    with open(f"{output_name}.json", "w") as file:
        json.dump(test_result_dict, file, indent=4)

    print(f"Outputted to file called {output_name}.json")



def build_average_throughput_class(all_round_results):
    MIN = "min"
    MEAN = "mean"
    MEDIAN = "median"
    units = "ops/s"

    cumulative_min = []
    cumulative_mean = []
    cumulative_median = []

    for round_result in all_round_results:
        cumulative_min.append(round_result[MIN])
        cumulative_mean.append(round_result[MEAN])
        cumulative_median.append(round_result[MEDIAN])

    # print(cumulative_min, cumulative_mean, cumulative_median)
    # print(all_round_results)

    avg_min = statistics.mean(cumulative_min)
    avg_mean = statistics.mean(cumulative_mean)
    avg_median = statistics.mean(cumulative_median)

    rsd_min = (statistics.stdev(cumulative_min) / avg_min) * 100
    rsd_mean = (statistics.stdev(cumulative_mean) / avg_mean) * 100
    rsd_median = (statistics.stdev(cumulative_median) / avg_median) * 100

    return AveragedThroughput(avg_min, rsd_min, avg_mean, rsd_mean, avg_median, rsd_median, units)

def build_average_service_time_class(all_round_results):
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
        cumulative_p50_service_time.append(round_result[P50_SERVICE_TIME])
        cumulative_p90_service_time.append(round_result[P90_SERVICE_TIME])
        cumulative_p99_service_time.append(round_result[P99_SERVICE_TIME])
        cumulative_p99_9_service_time.append(round_result[P99_9_SERVICE_TIME])
        cumulative_p99_99_service_time.append(round_result[P99_99_SERVICE_TIME])
        cumulative_p100_service_time.append(round_result[P100_SERVICE_TIME])

    avg_p50_service_time = statistics.mean(cumulative_p50_service_time)
    avg_p90_service_time = statistics.mean(cumulative_p90_service_time)
    avg_p99_service_time = statistics.mean(cumulative_p99_service_time)
    avg_p99_9_service_time = statistics.mean(cumulative_p99_9_service_time)
    avg_p99_99_service_time = statistics.mean(cumulative_p99_99_service_time)
    avg_p100_service_time = statistics.mean(cumulative_p100_service_time)

    rsd_p50_service_time = statistics.stdev(cumulative_p50_service_time) / avg_p50_service_time
    rsd_p90_service_time = statistics.stdev(cumulative_p90_service_time)/ avg_p90_service_time
    rsd_p99_service_time = statistics.stdev(cumulative_p99_service_time)/ avg_p99_service_time
    rsd_p99_9_service_time = statistics.stdev(cumulative_p99_9_service_time)/ avg_p99_9_service_time
    rsd_p99_99_service_time = statistics.stdev(cumulative_p99_9_service_time)/ avg_p99_99_service_time
    rsd_p100_service_time = statistics.stdev(cumulative_p100_service_time)/ avg_p100_service_time

    return AveragedServiceTime(avg_p50_service_time, rsd_p50_service_time, avg_p90_service_time, rsd_p90_service_time, avg_p99_service_time, rsd_p99_service_time, avg_p99_9_service_time, rsd_p99_9_service_time, avg_p99_99_service_time, rsd_p99_99_service_time, avg_p100_service_time, rsd_p100_service_time, units)

def build_average_latency_class(all_round_results):
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
        cumulative_p50_latency.append(round_result[P50_LATENCY])
        cumulative_p90_latency.append(round_result[P90_LATENCY])
        cumulative_p99_latency.append(round_result[P99_LATENCY])
        cumulative_p99_9_latency.append(round_result[P99_9_LATENCY])
        cumulative_p99_99_latency.append(round_result[P99_99_LATENCY])
        cumulative_p100_latency.append(round_result[P100_LATENCY])

    avg_p50_latency = statistics.mean(cumulative_p50_latency)
    avg_p90_latency = statistics.mean(cumulative_p90_latency)
    avg_p99_latency = statistics.mean(cumulative_p99_latency)
    avg_p99_9_latency = statistics.mean(cumulative_p99_9_latency)
    avg_p99_99_latency = statistics.mean(cumulative_p99_99_latency)
    avg_p100_latency = statistics.mean(cumulative_p100_latency)

    rsd_p50_latency = statistics.stdev(cumulative_p50_latency) / avg_p50_latency
    rsd_p90_latency = statistics.stdev(cumulative_p90_latency)/ avg_p90_latency
    rsd_p99_latency = statistics.stdev(cumulative_p99_latency)/ avg_p99_latency
    rsd_p99_9_latency = statistics.stdev(cumulative_p99_9_latency)/ avg_p99_9_latency
    rsd_p99_99_latency = statistics.stdev(cumulative_p99_9_latency)/ avg_p99_99_latency
    rsd_p100_latency = statistics.stdev(cumulative_p100_latency)/ avg_p100_latency

    return AveragedLatency(avg_p50_latency, rsd_p50_latency, avg_p90_latency, rsd_p90_latency, avg_p99_9_latency, rsd_p99_latency, avg_p99_9_latency, rsd_p99_9_latency, avg_p99_99_latency, rsd_p99_99_latency, avg_p100_latency, rsd_p100_latency, units)

def filter_documents(documents):
    unique_test_ids = set()
    throughput_documents = []
    service_time_documents = []
    latency_documents = []

    THROUGHPUT = "throughput"
    SERVICE_TIME = "service_time"
    LATENCY = "latency"

    for document in documents:
        operation_name = document["_source"]["name"]
        operation_test_id = document["_source"]["test-execution-id"]
        metrics = document["_source"]["value"]
        if operation_name == THROUGHPUT:
            throughput_documents.append(metrics)
        elif operation_name == SERVICE_TIME:
            service_time_documents.append(metrics)
        elif operation_name == LATENCY:
            latency_documents.append(metrics)

        unique_test_ids.add(operation_test_id)

    return unique_test_ids, throughput_documents, service_time_documents, latency_documents


def get_documents(client, test_execution_id_pattern):
    INDEX_PATTERN = 'benchmark-results-*'
    SIZE = 10000
    print(test_execution_id_pattern)
    # For regex patterns
    if "*" in test_execution_id_pattern:
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "terms": {
                                "name": ["throughput", "service_time", "latency"]
                            }
                        },
                        {
                            "wildcard": {
                                "test-execution-id": test_execution_id_pattern
                            }
                        }
                    ]
                }
            }
        }

        query_response = client.search(body=query, index=INDEX_PATTERN, size=SIZE)
        # print(query_response)
        print("Number of documents returned: ", query_response['hits']['total']['value'])
        documents = query_response['hits']['hits']

        return documents

    elif type(test_execution_id_pattern) == list:

        test_execution_id_patterns = test_execution_id_pattern
        documents = []
        for pattern in test_execution_id_patterns:
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "terms": {
                                    "name": ["throughput", "service_time", "latency"]
                                }
                            },
                            {
                                "wildcard": {
                                    "test-execution-id": pattern
                                }
                            }
                        ]
                    }
                }
            }

            query_response = client.search(body=query, index=INDEX_PATTERN, size=SIZE)
            # print(query_response)
            print(f"Number of docs received with {pattern}: {query_response['hits']['total']['value']}")
            documents += query_response['hits']['hits']

        print("Number of documents total: ", len(documents))
        return documents


    else:
        raise Exception("Need pattern to test execution id to aggregate lg host results from all rounds. Example: use test-execution-id*")


def create_opensearch_client(client_details):
    client = OpenSearch(
        hosts = [f'{host}:{port}'],
        http_auth = (username, password),
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    return client

def comma_separated_list(input: str):
    return input.split(',')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Aggregate Results from Nodes from MDS')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--test-id-pattern', '-p', help='Test Execution ID Pattern (with wildcard) to use to aggregate all rounds for a specific test configuration.')
    group.add_argument('--test-ids', '-ids', help='Test Execution IDs to include in the results. Example: id-1,id-2,id-3')
    parser.add_argument('--output-name', '-n', required=True, help='Output filename to use')
    parser.add_argument('--latency', '-l', action='store_true', help='Show latency. Default: False')
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

    if args.test_id_pattern:
        aggregate_rounds_results(client_details, args.test_id_pattern, args.output_name)
    elif args.test_ids:
        test_ids = args.test_ids.split(",")
        aggregate_rounds_results(client_details, test_ids, args.output_name)

