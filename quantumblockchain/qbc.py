# Make Predictions with k-nearest neighbors on the Iris Flowers Dataset

# from http.client import UNSUPPORTED_MEDIA_TYPE
import json
import logging
import traceback
from os import environ
import numpy as np
from qiskit import QuantumCircuit, Aer, execute

import requests

# Your API definition
logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

rollup_server = environ["ROLLUP_HTTP_SERVER_URL"]
logger.info(f"HTTP rollup_server url is {rollup_server}")




def hex2str(hex):
    """
    Decodes a hex string into a regular string
    """
    return bytes.fromhex(hex[2:]).decode("utf-8")

def str2hex(str):
    """
    Encodes a string as a hex string
    """
    return "0x" + str.encode("utf-8").hex()


def apply_one_qubit_gate(gate, qubit_number):
    if gate == 'H':
        circ.h(qubit_number)
    elif gate == 'X':
        circ.x(qubit_number)
    elif gate == 'Y':
        circ.y(qubit_number)
    elif gate == 'Z':
        circ.z(qubit_number)
    elif gate == 'S':
        circ.s(qubit_number)
    elif gate == 'T':
        circ.t(qubit_number)
    elif gate == 'Sdg':
        circ.sdg(qubit_number)
    elif gate == 'Tdg':
        circ.tdg(qubit_number)
    elif gate == 'I':
        circ.iden(qubit_number)
    else:
        raise(Exception('Invalid one qubit gate'))


def teleport_qubit(from_number, to_number):
    '''
    Discards qubit at to_number, creates a new bell pair with the last qubit and teleports the qubit at from_number to to_number
    '''
    circ.reset(to_number)
    circ.reset(num_qubits-1)
    circ.h(num_qubits-1)  # apply Hadamard gate to create superposition
    circ.cx(num_qubits-1, to_number)   # creates entangled bell pair
    # measure in bell basis and teleport the from number 
    # Sender's protocol
    circ.cx(from_number, num_qubits-1)
    circ.h(from_number)
    circ.measure(from_number, from_number)
    circ.measure(num_qubits-1, num_qubits-1)
    # Receiver's protocol
    circ.x(to_number).c_if(circ.clbits[from_number], 1)
    circ.z(to_number).c_if(circ.clbits[num_qubits-1], 1)


def apply_two_qubit_gate(gate, qubit_number1, qubit_number2):
    if gate == 'CX':
        circ.cx(qubit_number1, qubit_number2)
    elif gate == 'CY':
        circ.cy(qubit_number1, qubit_number2)
    elif gate == 'CZ':
        circ.cz(qubit_number1, qubit_number2)
    elif gate == 'SWAP':
        circ.swap(qubit_number1, qubit_number2)
    elif gate == 'TEL':
        teleport_qubit(qubit_number1, qubit_number2)
    else:
        raise(Exception('Invalid two qubit gate'))



def measure_qubit(qubit_number):
    circ.measure(qubit_number, qubit_number)


def measure_all():
    circ.measure_all()
    # wipe out the gates
    all_gates_so_far = []
    # initiate new circuit
    circ = QuantumCircuit(num_qubits)


def update_state(input):
    if input["gate"] == "MeasAll":
        measure_all()
    elif input["gate"] == "Meas":
        measure_qubit(input["target"])
    elif 'control' in input:
        apply_two_qubit_gate(input['gate'], input['target'], input['control'])
    else:
        apply_one_qubit_gate(input['gate'], input['target'])
    





def handle_advance(data):
    logger.info(f"Received advance request data {data}")

    status = "accept"
    try:
        # retrieves input as string
        input = hex2str(data["payload"])
        logger.info(f"Received input: '{input}'")

        # json input should be like this {"gate": "CX", "target": 0, "control": 1}

        # possible one qubit gates: H, X, Y, Z, S, T, Sdg, Tdg, I
        # possible two qubit gates: CX, CY, CZ, SWAP
        # possible measurements: Meas, MeasAll
        input_json = json.loads(input)
        logger.info(input_json)
        
        update_state(input_json)

        # draw the current circuit
        logger.info('Current state of circuit\n'+str(circ.draw(output='text')))

        if input['gate'] == 'MeasAll':
            # output is the result of the measurement
            backend = Aer.get_backend('qasm_simulator')   # use quantum simulator but can replace with actual quantum computer here
            job = execute(circ, backend, shots=1024)
            counts = job.result.get_counts()
            # flip the bits to get the correct order (qiskit counts from right to left) and divide by 1024 to get the probability
            counts = {k[::-1]: v/1024 for k, v in counts.items()}
            output = str2hex(json.dumps(counts))
        else:
            output = all_gates_so_far
        logger.info(f"Output: {output}")
        logger.info(f"Adding notice with payload: {output}")
        response = requests.post(rollup_server + "/notice", json={"payload": output})
        logger.info(f"Received notice status {response.status_code} body {response.content}")

    except Exception as e:
        status = "reject"
        msg = f"Error processing data {data}\n{traceback.format_exc()}"
        logger.error(msg)
        response = requests.post(rollup_server + "/report", json={"payload": str2hex(msg)})
        logger.info(f"Received report status {response.status_code} body {response.content}")

    return status


def handle_inspect(data):
    logger.info(f"Received inspect request data {data}")
    logger.info("Adding report")
    response = requests.post(rollup_server + "/report", json={"payload": data["payload"]})
    logger.info(f"Received report status {response.status_code}")
    return "accept"



num_qubits = 5
circ = QuantumCircuit(num_qubits)

all_gates_so_far = []


handlers = {
    "advance_state": handle_advance,
    "inspect_state": handle_inspect,
}

finish = {"status": "accept"}
rollup_address = None

while True:
    logger.info("Sending finish")
    response = requests.post(rollup_server + "/finish", json=finish)
    logger.info(f"Received finish status {response.status_code}")
    if response.status_code == 202:
        logger.info("No pending rollup request, trying again")
    else:
        rollup_request = response.json()
        data = rollup_request["data"]
        if "metadata" in data:
            metadata = data["metadata"]
            if metadata["epoch_index"] == 0 and metadata["input_index"] == 0:
                rollup_address = metadata["msg_sender"]
                logger.info(f"Captured rollup address: {rollup_address}")
                continue
        handler = handlers[rollup_request["request_type"]]
        finish["status"] = handler(rollup_request["data"])
