##################################################################
# 
# References    blockchain - https://hackernoon.com/learn-blockchains-by-building-one-117428612f46
#               DSA - https://www.di-mgt.com.au/public-key-crypto-discrete-logs-4-dsa.html
#               RSA - http://adilmoujahid.com/posts/2018/03/intro-blockchain-bitcoin-python/
# 
##################################################################


import hashlib
import json
import Crypto.Random
import binascii
from textwrap import dedent
from time import time
from blockchain import Blockchain
from flask import Flask, jsonify, request
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


app = Flask(__name__)
blockchain = Blockchain()


def calculate_signature(method, key, sender, recipient, amount):
    # calculates signature based on chosen method

    msg = {
        'sender': sender,
        'recipient': recipient,
        'amount': amount
    }

    if method == 'RSA':
        private_key = RSA.importKey(binascii.unhexlify(key))
        signer = PKCS1_v1_5.new(private_key)
        h = SHA.new(str(msg).encode('utf8'))
        signature = binascii.hexlify(signer.sign(h)).decode('ascii')
    elif method == 'DSA':
        # TODO: implement DSA
        signature = 'DSA'
    else:
        return ''

    return signature


@app.route('/keys/RSA/new', methods=['GET'])
def make_RSA_keys():
    # generate a pair of private and public RSA keys

    random_num = Crypto.Random.new().read
    private_key = RSA.generate(1024, random_num)
    public_key = private_key.publickey()
    response = {    
		'private key': binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
		'public key': binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
    }
    return jsonify(response), 200


@app.route('/keys/DSA/new', methods=['GET'])
def make_DSA_keys():
    # generate a pair of private and public DSA keys
    pass


@app.route('/mine', methods=['GET'])
def mine():
    # mines a new block

    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    blockchain.new_transaction(
        sender='0',
        recipient=blockchain.node_id,
        amount=1,
        method=None,
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
    if signature == '':
        return 'Invalid signature method', 400
    
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'], method, signature)

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
