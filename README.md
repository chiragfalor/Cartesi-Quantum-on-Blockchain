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

Then, one uses frontend to send inputs. In a new terminal entire 

```shell
cd frontend-console
```

Inputs are of the form `{"gate":"H", "target":1}`

If one wants to create Bell pair in the first two bits
```shell
yarn start input send --payload '{"gate":"H", "target":1}'
yarn start input send --payload '{"gate":"CX", "target":0, "control":1}'
```

If one wants to teleport the entangled first qubit to fourth position
```shell
yarn start input send --payload '{"gate":"TEL",  "target":0, "control":3}'
```
We can perform arbitrary complicated quantum computations and finally Measure all. This would run the complete circuit on a quantum machine and return the output of our final computation.

```shell
yarn start input send --payload '{"gate":"MeasAll"}'
```

At each gate, the logger logs a TextImage of the circuit to keep track of the computations. 



