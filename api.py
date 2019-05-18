##################################################################
# 
# Usage         python3 api.py
# 
# References    https://hackernoon.com/learn-blockchains-by-building-one-117428612f46
# 
##################################################################


import hashlib
import json
from textwrap import dedent
from time import time
from uuid import uuid4
from blockchain import Blockchain
from flask import Flask, jsonify, request


app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()


def calculate_signature(method, key, sender, recipient, amount):
    # calculates signature based on chosen method  

    if method == 'RSA':
        # TODO: implement RSA
        signature = 'RSA'
    elif method == 'DSA':
        # TODO: implement DSA
        signature = 'DSA'
    else:
        return 'Invalid signature method', 400

    return signature


@app.route('/mine', methods=['GET'])
def mine():
    # mines a new block

    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    blockchain.new_transaction(
        sender='0',
        recipient=node_identifier,
        amount=1,
        signature=None,
    )

    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': 'New block created',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }

    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    # adds a transaction to the next block

    values = request.get_json()

    # check for all required fields in POST data
    required = ['sender', 'recipient', 'amount', 'method', 'key']
    if not all(k in values for k in required):
        return 'Missing values', 400

    signature = calculate_signature(values['method'], values['key'],values['sender'], values['recipient'], values['amount'])

    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'], signature)

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    # returns the full blockchain

    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    # registers neighboring nodes

    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    
    for node in nodes:
        blockchain.register_node(node)
    
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    # resolves conflicts

    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'The chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'The chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


if __name__ == '__main__':
    app.run()
