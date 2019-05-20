##################################################################
#
# REQUIREMENTS
# 
# 1. Individual users should be able to broadcast
# transactions to the miners i.e., parties re-
# sponsible for verifying the blocks.
# 
# 2. All transactions within a block must be 
# digitally signed by the user initiating a transaction.
# 
# 3. Miners verify the transaction within a 
# block by solving a computationally hard problem.
# Can simplify the difficulty to test and demo.
# 
# 4. The miner who solves the problem first,
# gets a reward according to the rules of blockchain.
# 
# 5. When the block is verified, the miner broadcasts 
# the verified block to the users.
# 
# 6. In order to deal with the issues associated with 
# spoofed blocks the users must use the longest chain rule.
# 
# Support at least 3 users and 3 miners
# 
# Must provide both confidentiality and digital signature
# 
# Must provide the choice of RSA or DSA for digital signatures
# 
##################################################################

import hashlib
import json
import requests
import binascii
from time import time
from urllib.parse import urlparse
from Crypto.PublicKey import RSA
from uuid import uuid4
from Crypto.Hash import SHA
from Crypto.Signature import PKCS1_v1_5


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.new_block(previous_hash=1, proof=100)
        self.nodes = set()
        self.node_id = str(uuid4()).replace('-', '')


    def new_block(self, proof, previous_hash=None):
        # creates a new Block and adds it to the chain

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # reset current list of transactions
        self.current_transactions = []
        
        self.chain.append(block)
        return block    


    def new_transaction(self, sender, recipient, amount, method, signature, public_key):
        # adds a new transaction to the list of transactions

        if signature == None or self.verify_signature(sender, recipient, amount, method, signature, public_key):
            self.current_transactions.append({
                'sender': sender,
                'recipient': recipient,
                'amount': amount,
            })
        else:
            return 'Transaction signature is not valid'

        return self.last_block['index'] + 1
    

    def verify_signature(self, sender, recipient, amount, method, signature, public_key):

        msg = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        }

        if method == 'RSA':
            public_key = RSA.importKey(binascii.unhexlify(sender))
            verifier = PKCS1_v1_5.new(public_key)
            h = SHA.new(str(msg).encode('utf8'))
            return verifier.verify(h, binascii.unhexlify(signature))
        elif method == 'DSA':
            h = SHA.new(str(msg).encode('utf8')).digest()
            return public_key.verify(h, signature)
    
    
    @staticmethod
    def hash(block):
        # creates SHA-256 hash of a block

        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    
    @property
    def last_block(self):
        # returns the last block in the chain

        return self.chain[-1]

    
    def proof_of_work(self, last_proof):
        # finds a number such that hash(pp') contains "04",
        # where p is the previous proof and p' is the new proof
        
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        
        return proof

    
    @staticmethod
    def valid_proof(last_proof, proof):
        # validates the proof

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:2] == "10"
    

    def register_node(self, address):
        # adds a new node to the list of nodes

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        # determines if a given blockchain is valid

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print('\n---------------\n')

            if block['previous_hash'] != self.hash(last_block):
                return False
            
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            
            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        # consensus algorithm that resolves conflicts by replacing
        # the chain with the longest one in the network

        neighbors = self.nodes
        new_chain = None

        max_length = len(self.chain)

        # verifies the chains from the nodes in the network
        for node in neighbors:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        
        if new_chain:
            self.chain = new_chain
            return True
        
        return False
