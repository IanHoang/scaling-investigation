#!/bin/bash
run_id=$1
host=$2
clients=$3

hostname=$(hostname -I)
new_hostname=${hostname// }
new_run_id="${run_id}-${new_hostname}"
params="time_period:600,search_clients:${clients},target_throughput:\"\""

# Fill out basic_auth_user and basic_auth_password first
echo opensearch-benchmark execute-test --workload=big5 --pipeline=benchmark-only --target-hosts=$host --client-options="basic_auth_user:'hoangia',basic_auth_password:'Hoangia@123'" --workload-params=$params --include-tasks=term --kill-running-processes --results-file=/home/ec2-user/$new_run_id --test-execution-id=$new_run_id