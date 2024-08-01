import os
import argparse
import re
import json
import statistics
import numpy as np

import pandas as pd
import tabulate
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth, exceptions
import boto3
from dotenv import load_dotenv

THROUGHPUT = 'throughput'
SERVICE_TIME = 'service_time'
LATENCY = 'latency'

# Aggregate results in a round: with a specific test_execution_id pattern (e.g. 8-clients-2) because we need to aggregate results from all nodes in a round
# Aggregate all rounds at the end
def aggregate_results(client_details, output_name, test_execution_id):
    client = create_opensearch_client(client_details)
    documents = get_documents(client, test_execution_id)

    throughput_metrics, service_time_metrics, latency_metrics = filter_results(documents)

    # Create dataframes
    throughput_df = pd.DataFrame.from_dict(throughput_metrics, orient='index')
    service_time_df = pd.DataFrame.from_dict(service_time_metrics, orient='index')
    latency_df = pd.DataFrame.from_dict(latency_metrics, orient='index')

    # Print to console
    print(tabulate.tabulate(throughput_df, headers='keys', tablefmt='grid', showindex=True))
    print(tabulate.tabulate(service_time_df, headers='keys', tablefmt='grid', showindex=True))
    print(tabulate.tabulate(latency_df, headers='keys', tablefmt='grid', showindex=True))

    # Average results
    throughput_agg = {"min": None, "mean": None, "median": None, "units": "ops/s"}
    service_time_agg = {"50_0": None, "90_0": None, "99_0": None, "99_9": None, "99_99": None, "100_0": None, "units": "ms"}
    latency_agg = {"50_0": None, "90_0": None, "99_0": None, "99_9": None, "99_99": None, "100_0": None, "units": "ms"}

    populated_throughput_agg = calculate_arithmetic_mean(throughput_metrics, throughput_agg)
    populated_service_time_agg = calculate_arithmetic_mean(service_time_metrics, service_time_agg)
    populated_latency_agg = calculate_arithmetic_mean(latency_metrics, latency_agg)
    print(f"Throughput Metrics: {len(throughput_metrics)}, Service Time Metrics: {len(service_time_metrics)}, Latency Metrics: {len(latency_metrics)}")
    print(populated_throughput_agg)
    print(populated_service_time_agg)
    print(populated_latency_agg)

    # Export to CSV
    # throughput_df.to_csv(f"throughput-{output_name}.csv", index_label='Row ID')
    # service_time_df.to_csv(f"service-time-{output_name}.csv", index_label='Row ID')
    # latency_df.to_csv(f"latency-{output_name}.csv", index_label='Row ID')
    averaged_results_from_nodes = {
        "test-pattern": test_execution_id,
        "averaged-throughput": populated_throughput_agg,
        "averaged-service-time": populated_service_time_agg,
        "averaged-latency": populated_latency_agg
    }

    new_output_name = ""
    if output_name[-1] == "*":
        new_output_name = output_name[0:-2] + "-averaged.json"
    else:
        new_output_name = output_name + "-averaged.json"

    write_to_file(averaged_results_from_nodes, new_output_name)
    print("Wrote to file: ", new_output_name)

def filter_results(documents):
    throughput = {}
    service_time = {}
    latency = {}

    for document in documents:
        document_name = document['_source']['name']
        document_id = document['_source']['test-execution-id']
        operation = document['_source']['operation']
        value = document['_source']['value']

        node_ip_address = get_node_ip_address(document_id)
        value["node_ip_address"] = node_ip_address
        value["operation"] = operation

        if document_name == THROUGHPUT:
            throughput[document_id] = value
        elif document_name == SERVICE_TIME:
            service_time[document_id] = value
        elif document_name == LATENCY:
            latency[document_id] = value

    return throughput, service_time, latency

# TODO: Need to address this and add to README
# session = boto3.Session(
#     aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
#     aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
#     region_name=os.getenv('AWS_REGION')
# )

# credentials = boto3.Session().get_credentials()
# auth = AWSV4SignerAuth(credentials, region)
def create_opensearch_client(client_details):
    client = OpenSearch(
        hosts = [f'{host}:{port}'],
        http_auth = (username, password),
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    return client

def get_documents(client, test_execution_id):
    INDEX_PATTERN = 'benchmark-results-*'
    SIZE = 10000

    query = {
        "query": {
            "terms": {
                "name": ["throughput", "service_time", "latency"]
            }
        }
    }

    if test_execution_id != None and len(test_execution_id) > 0:
        # For regex patterns
        if "*" in test_execution_id:
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
                                    "test-execution-id": test_execution_id
                                }
                            }
                        ]
                    }
                }
            }
        else:
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
                                "term": {
                                    "test-execution-id": test_execution_id
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

def calculate_arithmetic_mean(nodes, metrics_to_average):

    for metric in metrics_to_average:
        if metric == "test-pattern" or metric == "units":
            continue

        metrics_from_nodes = [nodes[node][metric] for node in nodes]
        metric_mean = statistics.mean(metrics_from_nodes)
        # calculate_relative_stdev(metrics_from_nodes, metric_mean)
        metrics_to_average[metric] = metric_mean


    return metrics_to_average

def calculate_relative_stdev(metrics_from_nodes, metric_average):
    stdev = statistics.stdev(metrics_from_nodes)
    return np.round(stdev / metric_average, decimals=2)

def get_node_ip_address(document_id):
    # Define the regular expression pattern
    pattern = r'-(\d+\.\d+\.\d+\.\d+)-'

    # Search for the pattern in the string
    match = re.search(pattern, document_id)

    if match:
        ip_address = match.group(1)
        return ip_address
    else:
        raise Exception("No IP Address found")

def write_to_file(averaged_results_from_nodes, file_name):
    formatted_averaged_results_from_nodes = json.dumps(averaged_results_from_nodes, indent=4)

    with open(file_name, "w") as output_json:
        print(formatted_averaged_results_from_nodes, file=output_json)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Aggregate Results from Nodes from MDS')
    parser.add_argument('--output-name', '-n', required=True, help="Output filename to use")
    parser.add_argument('--id', '-i', required=True, help='Test-execution-id or test-execution-id pattern for specific documents.')
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

    aggregate_results(client_details, args.output_name, args.id)
