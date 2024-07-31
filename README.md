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
3. After running 1-5 rounds of a specific configuration (e.g. 8 clients), run the `python3 aggregate-results.py -i <test-execution-id pattern>` to aggregate results for a round
4. Update the ASG (scale out or in) and then rerun steps 2 and 3