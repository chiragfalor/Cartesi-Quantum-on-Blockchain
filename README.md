# Cartesi submission for HackBoston

Build the docker image for Cartesi Virtual Machine (in host mode).
Install the requirements by running the following commands
```shell
cd quantumblockchain
python3 -m venv .env
. .env/bin/activate
pip install -r requirements.txt
ROLLUP_HTTP_SERVER_URL="http://127.0.0.1:5004" python3 qbc.py
```
