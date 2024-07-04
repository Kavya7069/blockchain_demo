#block5003

import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

class Blockchain:
    def __init__(self):
        self.chain = []
        self.trans = []
        self.create_block(proof = 1, prev_hash = '0')
        self.nodes = set() 
        
    def create_block(self, proof, prev_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof':proof,
                 'prev_hash': prev_hash,
                 'trasaction' : self.trans}
        self.trans = []
        self.chain.append(block)
        return block
    
    def get_prev_block(self):
        return self.chain[-1]

    def pow(self, prev_proof):
        new_proof = 1 #each iteration incremented by one
        checkproof = False #to check if 'new_proof' is correct
        while checkproof == False:
            hash_operation = hashlib.sha256(str(new_proof**2 - prev_proof**2).encode()).hexdigest()
                 #an simple example computation problem, has to be non-symmetrical
            if hash_operation[:4] == '0000':#the hash has to start with 4 leading zeros(target)
                checkproof = True
            else:
                new_proof += 1
        return new_proof

    def hash(self,block):#encode the blocks dict and get hash
        encoded_block = json.dumps(block, sort_keys = True).encode()
            #we encode using json instead of just str because we will have to put this in json file 
        return hashlib.sha256(encoded_block).hexdigest()  

    #to prove validity: 1. 'prev_hash' shld be the previous hash; 2. verify pow

    def is_valid(self, chain):
        prev_block = chain[0]
        block_index = 1 
        while block_index < len(chain): #iterate all the blocks
           block = chain[block_index]
           if block['prev_hash'] != self.hash(prev_block):
               return False
           prev_proof = prev_block['proof']
           proof = block['proof']
           hash_operation = hashlib.sha256(str(proof**2 - prev_proof**2).encode()).hexdigest()
           if hash_operation[:4] != '0000':
               return False
           prev_block = block
           block_index += 1
        return True

    def add_trans(self, sender, receiver, amount):
        self.trans.append({'sender' : sender,
                           'receiver' : receiver,
                           'amount' : amount})
        prev_block = self.get_prev_block()
        return prev_block['index'] + 1

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for nodes in network:
            response = requests.get(f'http://{nodes}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False 

#Mining the blockchain

#creating a Web App
app= Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

#Creating an address for the node on port 5000
node_address = str(uuid4()).replace('-' , '')


#Creating a blockchain obj
blockchain = Blockchain()

#Mining a new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    prev_block = blockchain.get_prev_block()
    prev_proof = prev_block['proof']
    proof = blockchain.pow(prev_proof)
    prev_hash = blockchain.hash(prev_block)
    blockchain.add_trans(sender = node_address, receiver = 'you', amount = 1)
    block = blockchain.create_block(proof, prev_hash)
    response = {'message' : 'Congratulations, you just mined a block!',
                'index' : block['index'],
                'timestamp' : block['timestamp'],
                'proof' : block['proof'],
                'prev_hash' : block['prev_hash'],
                'transaction' : block['trans']}
    return jsonify(response), 200

#Getting the full blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain' : blockchain.chain,
                'length' : len(blockchain.chain)}
    return jsonify(response), 200

@app.route('/is_valid', methods = ['GET'])
def is_valid():
        valid = blockchain.is_valid(blockchain.chain)
        response = {'message' : 'The blockchain is valid' if valid else 'The blockchain is not valid'}
        return jsonify(response), 200
    
#Adding a new transaction to the blockchain
@app.route('/add_trans', methods = ['POST'])
def add_trans():
    json = request.get_json()
    transaction_keys = ['sender' , 'receiver', 'amount']
    if not all (key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    index = blockchain.add_trans(json['sender'],json['receiver'], json['amount'])
    response = {'message' : f'This transaction will be added to Block {index}'}
    return jsonify(response), 201
    
#Decentralizing our block
#Connecting new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message' : "All the nodes are now connected. The Bitcoin Blockchain now contains the following nodes",
                'total_node' : list(blockchain.nodes)}
    return jsonify(response), 201

#replacing the chain by the largest chain if needed
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
        is_chain_replaced = blockchain.replace_chain()
        response = {'message' : 'The blockchain is replaced' if is_chain_replaced else 'The blockchain is not replaced'}
        return jsonify(response), 200

#Running the app
app.run(host = '0.0.0.0', port = 5003)

