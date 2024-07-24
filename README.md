### README

#### Prerequisites
1. Git clone repository to local computer
2. Set up venv (`python3 -m venv .venv`) and run (`source .venv/bin/activate`) to activate it. Afterwards, run `pip3 install -r requirements.txt` to install dependencies
3. Create an AMI with `run-osb-with-term.sh` copied onto it
4. Set up an OpenSearch cluster
5. Copy `.env.example` to `.env` and insert AWS credentials there

#### Set up an Auto Scaling Group
Run `python3 asg-manager.py create` with appropriate parameters to create an auto scaling group.

#### Run Tests
Run `python3 run-osb-on-asg.py` to run tests on auto scaling group. Ensure that host and tags are provided.

#### Kill Tests
Run `python3 kill-osb-on-asg.py` to kill tests on auto scaling group. Ensure that host and tags are provided.
