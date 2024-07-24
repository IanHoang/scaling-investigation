#!/bin/bash
run_id=$1
host=$2

opensearch-benchmark execute-test --workload=big5 --pipeline=benchmark-only --target-hosts=$host --client-options="basic_auth_user:'',basic_auth_password:''" --workload-params=test_iterations:10000,search_clients:1,target_throughput:"" --include-tasks=term --kill-running-processes --results-file=/home/ec2-user/$run_id --test-execution-id=$run_id