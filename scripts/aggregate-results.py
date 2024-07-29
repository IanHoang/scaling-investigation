import os

from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth, exceptions
import boto3
from dotenv import load_dotenv

load_dotenv()
host = os.getenv('HOST')
port = 443
region = os.getenv('AWS_REGION')
username = os.getenv('MDS_USERNAME')
password = os.getenv('MDS_PASSWORD')

# TODO: Need to address this
# session = boto3.Session(
#     aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
#     aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
#     region_name=os.getenv('AWS_REGION')
# )

# credentials = boto3.Session().get_credentials()
# auth = AWSV4SignerAuth(credentials, region)

INDEX_PATTERN = 'benchmark-results-*'
ITERATIONS = 200

client = OpenSearch(
    hosts = [f'{host}:{port}'],
    http_auth = (username, password),
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)

query = {
  "query": {
    "match_all" : {}
  }
}

query_response = client.search(body=query, index=INDEX_PATTERN)
print(host)
print(query_response)