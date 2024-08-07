### README

#### Prerequisites
1. Git clone repository to local computer
2. Set up venv (`python3 -m venv .venv`) and run (`source .venv/bin/activate`) to activate it. Afterwards, run `pip3 install -r requirements.txt` to install dependencies
3. Create an EC2 instance with `run-osb-with-term.sh` copied onto it. Install opensearch-benchmark onto the EC2 instance and run it with Big5 ingestion only. This might take some time so run it in a screen. Optional: if adding metrics to an MDS store, update `benchmark.ini` in `~/.benchmark/benchmark.ini` to include MDS store endpoint and credentials (reference `example_benchmark.ini`).
4. Set up an OpenSearch cluster
5. Copy `.env.example` to `.env` and insert AWS credentials there

#### Set up an Auto Scaling Group
Run `python3 asg-manager.py create` with appropriate parameters to create an auto scaling group.

#### Run Tests
Run `python3 run-osb-on-asg.py -i <test-exeuction-id>` to run tests on auto scaling group. Ensure that host and tags are provided.

#### Kill Tests
Run `python3 kill-osb-on-asg.py` to kill tests on auto scaling group. Ensure that host and tags are provided.


#### Preliminary Tests for Auto Scaling Group
1. Create an asg with `python3 asg-manager.py create`
2. Run a round of tests with a specific configuration. Run the test with `python3 run-osb-on-asg.py -i <test-execution-id>`
3. After running 1-5 rounds of a specific configuration (e.g. 8 clients), run the `python3 aggregate-nodes-results.py -i <test-execution-id pattern>` to aggregate results for a round. This will aggregate results from all nodes from the experiment through the MDS. The results will be a round of results. Run another round of experiments as needed.
4. Insert the rounds from step 3 that you want to average into a folder. Run `python3 aggregate-rounds-result.py -f <folder-name> -n <output-name>` to aggregate all rounds and produce a final averaged result file, which can be compared with the results in the LG Hosts tests.
5. Update the ASG (scale out or in) and then rerun stepss 2 - 4.

#### Preliminary Tests for LG Hosts
1. Set up LG Host with AMI from auto scaling group experiments
2. Insert `run-osb-with-term-lg-host.sh` script into instance and build an AMI
3. Run `bash run-osb-with-term-lg-host.sh <test-execution-id> <endpoint> <clients>` to generate a command to run the test. NOTE: We cannot run it directly in the script because there are issues with parsing \"\" in OSB client.
4. Run `python3 aggregate-lg-host-results.py -p <test-execution-id-pattern | comma-separated list of test-execution-id-patterns> -n <output_name>`. The comma-separated list option is useful if you want to limit the number of test ids that are aggregated together. For example, if you ran several tests but you only want 3 specific tests, you can specify 3 test-execution-id patterns with wildcards. Also, helpful if running with several lg hosts in scenarios where single lg host isn't enough (still only need to specify 3 test-execution-id patterns with wildcards to aggregate 3 tests from all lg hosts)