#!/bin/bash
run_id=$1
host=$2

hostname=$(hostname -I)
new_hostname=${hostname// }
uuid="$(uuidgen)"
new_uuid=${uuid// }
new_run_id="${run_id}-${new_hostname}-${new_uuid}"

# Fill out basic_auth_user and basic_auth_password first
opensearch-benchmark execute-test --workload=big5 --pipeline=benchmark-only --target-hosts=$host --client-options="basic_auth_user:'',basic_auth_password:''" --workload-params=test_iterations:10000,search_clients:1,target_throughput:"" --include-tasks=term --kill-running-processes --results-file=/home/ec2-user/$new_run_id --test-execution-id=$new_run_id