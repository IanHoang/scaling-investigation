import os
import argparse

import pandas as pd
import tabulate
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth, exceptions
import boto3
from dotenv import load_dotenv

THROUGHPUT = 'throughput'
LATENCY = 'latency'
SERVICE_TIME = 'service_time'

def gather_results(client_details, output_name, test_execution_id):
    client = create_opensearch_client(client_details)
    documents = get_documents(client, test_execution_id)

    throughput_metrics, latency_metrics, service_time_metrics = filter_results(documents)
    # Create dataframes
    throughput_df = pd.DataFrame.from_dict(throughput_metrics, orient='index')
    latency_df = pd.DataFrame.from_dict(latency_metrics, orient='index')
    service_time_df = pd.DataFrame.from_dict(service_time_metrics, orient='index')

    # Print to console
    print(tabulate.tabulate(throughput_df, headers='keys', tablefmt='grid', showindex=True))
    print(tabulate.tabulate(service_time_df, headers='keys', tablefmt='grid', showindex=True))
    print(tabulate.tabulate(latency_df, headers='keys', tablefmt='grid', showindex=True))

    # Export to CSV
    # throughput_df.to_csv(f"throughput-{output_name}.csv", index_label='Row ID')
    # service_time_df.to_csv(f"service-time-{output_name}.csv", index_label='Row ID')
    # latency_df.to_csv(f"latency-{output_name}.csv", index_label='Row ID')

def filter_results(documents):
    throughput = {}
    latency = {}
    service_time = {}

    for document in documents:
        document_name = document['_source']['name']
        document_id = document['_source']['test-execution-id']
        value = document['_source']['value']
        print(document)

        if document_name == THROUGHPUT:
            throughput[document_id] = value
        elif document_name == LATENCY:
            latency[document_id] = value
        elif document_name == SERVICE_TIME:
            service_time[document_id] = value

    return throughput, latency, service_time

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Aggregate Results from MDS')
    parser.add_argument('--output-name', '-n', required=True, help="Output filename to use")
    parser.add_argument('--id', '-i', default=None, help='Test-execution-id or test-execution-id pattern for specific documents')
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

    gather_results(client_details, args.output_name, args.id)
