from web3 import Web3
import json

import grpc
import updateService_pb2_grpc as usgrpc
import updateService_pb2 as us

import backupService_pb2_grpc as bsgrpc
import backupService_pb2 as bs

from ethsnarks.field import FQ
from ethsnarks.jubjub import Point
from math import floor, log2
from typing import List
G = Point.from_y(FQ(20819045374670962167435360035096875258406992893633759881276124905556507972311))
import time

import random
from random import Random
import re
import math
import requests
import string

class MMR:
    @staticmethod
    def leaf_index(position):
        index = 0
        for i, bit in enumerate(reversed(format(position - 1, 'b'))):
            if bit == '1':
                index = index + (2 << i) - 1
        index += 1
        return index

    @staticmethod
    def peak_node_index(position):
        next_leaf_index = MMR.leaf_index(position + 1)
        return next_leaf_index - 1

    @staticmethod
    def peak_existence(width, peak_height) -> bool:
        return width & (1 << (peak_height - 1)) != 0

    @staticmethod
    def max_height(width):
        return floor(log2(width)) + 1

    @staticmethod
    def sibling_map(width, position) -> str:
        covered_width = 0
        sib_map = None
        my_peak_height = None

        # Find which peak the item belongs to & sibling map for it
        max_height = MMR.max_height(width)
        for i in range(max_height):
            # Starts from the left-most peak
            peak_height = max_height - i
            current_peak_width = (1 << (peak_height - 1))
            if MMR.peak_existence(width, peak_height):
                covered_width += current_peak_width

            if covered_width >= position:
                # The leaf belongs to this peak
                if peak_height == 1:
                    reversed_sib_map = ""
                else:
                    reversed_sib_map = format(covered_width - position, '0{}b'.format(peak_height - 1))
                sib_map = reversed_sib_map[::-1]
                my_peak_height = peak_height
                break

        assert sib_map is not None
        assert my_peak_height is not None
        assert len(sib_map) == my_peak_height - 1
        return sib_map

class PedersenMMR(MMR):
    def __init__(self, bits=16):
        self.bits = bits
        self.width = 0
        self.items = {}
        self.nodes = {}
        self.peaks = [Point.infinity()] * bits

    @classmethod
    def from_peaks(cls, bits, peaks: List[Point]):
        assert len(peaks) == bits
        mmr = cls(bits)
        mmr.width = PedersenMMR.width_from_peaks(peaks)
        mmr.peaks = [*peaks]
        # Update branch nodes
        index = 0
        for i in range(len(peaks)):
            peak_height = len(peaks) - i
            if peaks[i] != Point.infinity():
                # Peak exists
                index += (1 << peak_height) - 1
                mmr.nodes[index] = peaks[i]
        return mmr

    @staticmethod
    def width_from_peaks(peaks: List[Point]) -> int:
        width = 0
        for i in range(len(peaks)):
            peak_height = len(peaks) - i
            if peaks[i] != Point.infinity():
                width += 1 << (peak_height - 1)
        return width

    @staticmethod
    def peak_bagging(peaks: List[Point]) -> FQ:
        root_point = G
        width = PedersenMMR.width_from_peaks(peaks)
        for i in reversed(range(len(peaks))):
            # Starts from the right-most peak
            peak_height = len(peaks) - i
            peak = peaks[i]
            # With the mountain map, check the peak exists or not correctly
            assert (peak == Point.infinity()) is (False if MMR.peak_existence(width, peak_height) else True)
            # Update root point
            root_point = root_point * peak.y
        root_point = root_point * width
        return root_point.y

    @staticmethod
    def peak_update(prev_width, peaks: List[Point], item: Point) -> List[Point]:
        new_width = prev_width + 1
        leaf_node = item * new_width
        cursor = leaf_node
        new_peaks = peaks
        new_peak = None
        for i in reversed(range(len(peaks))):
            # Starts from the right-most peak
            peak_height = len(peaks) - i
            prev_peak = peaks[i]
            # With the mountain map, check the peak exists or not correctly
            assert (prev_peak == Point.infinity()) is \
                   (True if MMR.peak_existence(prev_width, peak_height) else False)
            # Move cursor to the next peak.
            cursor = cursor * prev_peak.y
            # Update new peak
            if not MMR.peak_existence(new_width, peak_height):
                # Peak should be zero
                new_peaks[i] = Point.infinity()
            elif not MMR.peak_existence(prev_width, peak_height):
                assert new_peak is None, "There should be only one new peak"
                new_peaks[i] = cursor
                new_peak = cursor
            else:
                new_peaks[i] = prev_peak

        assert new_peak is not None, "Failed to find new peak"
        return new_peak

    @staticmethod
    def inclusion_proof(root: FQ, position, item: Point, peaks: List[Point],
                        siblings: List[Point]) -> bool:
        # Check peak bagging first
        width = PedersenMMR.width_from_peaks(peaks)
        assert PedersenMMR.peak_bagging(peaks) == root

        sibling_map = MMR.sibling_map(width, position)
        my_peak_height = len(sibling_map) + 1
        my_peak = peaks[len(peaks) - my_peak_height]

        # Calculate the belonging peak with siblings
        leaf_node = item * position
        cursor = leaf_node
        for i in range(len(sibling_map)):
            is_right_sibling = sibling_map[i] == '1'
            right_node = siblings[i] if is_right_sibling else cursor
            left_node = cursor if is_right_sibling else siblings[i]
            cursor = right_node * left_node.y

        assert cursor == my_peak
        return True

    @property
    def root(self) -> FQ:
        return PedersenMMR.peak_bagging(self.peaks)

    def get_siblings(self, position) -> List[Point]:
        # variables to return
        width = self.width
        siblings = []

        sibling_map = MMR.sibling_map(width, position)
        my_peak_height = len(sibling_map) + 1

        # Calculate the belonging peak with siblings
        cursor_index = MMR.leaf_index(position)
        for i in range(my_peak_height - 1):
            has_right_sibling = sibling_map[i] == '1'
            if has_right_sibling:
                cursor_index = cursor_index + (2 << i)
                right_sibling_index = cursor_index - 1
                siblings.append(self.nodes[right_sibling_index])
            else:
                cursor_index += 1
                left_sibling_index = cursor_index - (2 << i)
                siblings.append(self.nodes[left_sibling_index])
        siblings = siblings + [Point.infinity()] * (self.bits - len(siblings))
        return siblings

    def get_inclusion_proof(self, position):
        siblings = self.get_siblings(position)
        return PedersenMMRProof(self.root, position, self.items[position], self.peaks, siblings)

    def append(self, item: Point):
        new_width = self.width + 1

        # Store leaf node
        # leaf_node = item * new_width
        leaf_node = item * new_width
        leaf_index = MMR.leaf_index(new_width)
        self.items[new_width] = item
        self.nodes[leaf_index] = leaf_node

        # When it is an odd leaf
        if new_width & 1:
            new_peaks = self.peaks
            new_peaks[len(new_peaks) - 1] = leaf_node
        # When it is an even leaf
        else:
            cursor = leaf_node
            cursor_index = leaf_index
            peak_node_index = MMR.peak_node_index(new_width)
            height = 1
            while cursor_index != peak_node_index:
                height = height + 1
                cursor_index = cursor_index + 1
                #
                left_node_index = cursor_index - (1 << (height - 1))
                left_node = self.nodes[left_node_index]
                cursor = cursor * left_node.y
                self.nodes[cursor_index] = cursor

            new_peaks = self.peaks[:-height] + [cursor] + [Point.infinity()] * (height - 1)

        self.peaks = new_peaks
        self.width = new_width

class PedersenMMRProof:
    def __init__(self, root: FQ, position, item: Point, peaks: List[Point], siblings: List[Point]):
        self.root = root
        self.position = position
        self.item = item
        self.peaks = peaks
        self.siblings = siblings
        self.zkp = None
        assert PedersenMMR.inclusion_proof(root, position, item, peaks, siblings)

    def __str__(self):
        return "root: {}\n".format(self.root) + \
               "position: {}\n".format(self.position) + \
               "item: {}\n".format(self.item) + \
               "peaks: {}\n".format(self.peaks) + \
               "siblings: {}".format(self.siblings)

# Check inclusion Proof 
def proof_check(proof, opindex,item):
    def inclusion_proof(root: FQ, position, item: Point, peaks: List[Point],
                        siblings: List[Point]) -> bool:
        # Check peak bagging first
        width = PedersenMMR.width_from_peaks(peaks)
        if PedersenMMR.peak_bagging(peaks) == root:

            sibling_map = MMR.sibling_map(width, position)
            my_peak_height = len(sibling_map) + 1
            my_peak = peaks[len(peaks) - my_peak_height]

            # Calculate the belonging peak with siblings
            leaf_node = item * position
            cursor = leaf_node
            for i in range(len(sibling_map)):
                is_right_sibling = sibling_map[i] == '1'
                right_node = siblings[i] if is_right_sibling else cursor
                left_node = cursor if is_right_sibling else siblings[i]
                cursor = right_node * left_node.y

            if cursor == my_peak:
                return True
        return False
    root = contract.function.look_op_root(opindex).call()
    peaks = proof.peaks
    result = []
    for i in range(len(item)):

        position = proof.position[i]
        siblings = proof.siblings[i]

        result.append(inclusion_proof(root,position,item,peaks,siblings))
    
    return result

myPRNG = Random()
data_size = 10000
contention_size = int(data_size * 0.1)
arg_list = dict()
command_list = list()
Tran_dict = dict()

comm_user_id = []
for i in range(contention_size):
    comm_user_id.append(myPRNG.randint(0, data_size))

no_of_queries = 8
no_of_reads = 6
no_of_writes = no_of_queries - no_of_reads
hotspot_queries = 0.6
no_of_comm_users = int(math.ceil(no_of_queries * hotspot_queries))


commit_read_only = 0
commit_medium_contention = 0
commit_high_contention = 0
trans_reqd = 20

def create_trans(trans_no, flag):
    alpha = list(string.ascii_uppercase)
    key = alpha[:no_of_comm_users]
    not_comm = alpha[no_of_comm_users:20]
    not_comm.remove('T')
    random.shuffle(key)
    # random.shuffle(not_comm)
    # print key
    if flag == "read_queries":
        trans_command = [''] * no_of_queries
        j = 0
        while j < no_of_queries:
            rand = myPRNG.randint(0, no_of_queries - 1)
            if trans_command[rand] == 'READ':
                continue
            else:
                j += 1
                trans_command[rand] = 'READ'
        for i in range(no_of_comm_users):
            trans_command[i] += str(trans_no) + '(' + key[i] + ')\n'
        for i in range(no_of_queries):
            if '(' in trans_command[i]:
                continue
            else:
                trans_command[i] += str(trans_no) + '(' + not_comm[myPRNG.randint(0, 18 - no_of_comm_users)] + ')\n'
        random.shuffle(trans_command)

        return trans_command

    elif flag == "med_contention":
        no_of_reads = 6
        no_of_writes = no_of_queries - no_of_reads
        trans_command = [''] * no_of_queries
        j = 0
        while j < no_of_reads:
            rand = myPRNG.randint(0, no_of_queries - 1)
            if trans_command[rand] == 'READ':
                continue
            else:
                j += 1
                trans_command[rand] = 'READ'
        for i in range(no_of_queries):
            if trans_command[i] == '':
                trans_command[i] = 'WRITE'
        for i in range(no_of_comm_users):
            trans_command[i] += str(trans_no) + '(' + key[i] + ')\n'
        for i in range(no_of_queries):
            if '(' in trans_command[i]:
                continue
            else:
                trans_command[i] += str(trans_no) + '(' + not_comm[myPRNG.randint(0, 18 - no_of_comm_users)] + ')\n'
        random.shuffle(trans_command)

        return trans_command

    else:
        no_of_reads = 6
        no_of_writes = 2
        trans_command = [''] * no_of_queries
        j = 0
        while j < no_of_reads:
            rand = myPRNG.randint(0, no_of_queries - 1)
            if trans_command[rand] == 'READ':
                continue
            else:
                j += 1
                trans_command[rand] = 'READ'
        for i in range(no_of_queries):
            if trans_command[i] == '':
                trans_command[i] = 'WRITE'
        for i in range(no_of_comm_users):
            trans_command[i] += str(trans_no) + '(' + key[i] + ')\n'
        for i in range(no_of_queries):
            if '(' in trans_command[i]:
                continue
            else:
                trans_command[i] += str(trans_no) + '(' + not_comm[myPRNG.randint(0, 18 - no_of_comm_users)] + ')\n'
        random.shuffle(trans_command)

        return trans_command

def read_only():
    variable_value = {}
    global trans_reqd, commit_read_only
    total_trans_read = []
    total_trans_read_to = []
    flag = "read_queries"
    for i in range(1, trans_reqd + 1):
        total_trans_read += create_trans(i, flag)

    random.shuffle(total_trans_read)

    commit_read_only = len(total_trans_read)
    total_trans_read = ['T = ' + str(trans_reqd) + '\n'] + total_trans_read
    # print total_trans_read
    for i in range(len(total_trans_read)):
        if '(' in total_trans_read[i]:
            variable_name = total_trans_read[i].split('(')[1][0]
            if variable_name in variable_value.keys():
                continue
            elif variable_name in ['A', 'B', 'C', 'D', 'E']:
                variable_value[variable_name] = comm_user_id[myPRNG.randint(0, contention_size-1)]
            else:
                variable_value[variable_name] = myPRNG.randint(0, data_size)
    # print variable_value
    for entry in variable_value:
        # print entry, variable_value[entry]
        total_trans_read.insert(1, entry + ' = ' + str(variable_value[entry]) + '\n')

    # print ''.join(total_trans_read)
    total_trans_read_to = [','.join(['T' + str(i + 1) for i in range(trans_reqd)]) + '\n']\
                          + total_trans_read

    ycsb_test = ''.join(total_trans_read)
    ycsb_test_to = ''.join(total_trans_read_to)
    # print ycsb_test_to
    return ycsb_test, ycsb_test_to

def medium_contention():
    global trans_reqd, commit_medium_contention
    variable_value = {}
    total_trans = []
    total_trans_read_to = []
    flag = "med_contention"
    for i in range(1, trans_reqd + 1):
        total_trans += create_trans(i, flag)

    random.shuffle(total_trans)

    total_trans = ['T = ' + str(trans_reqd) + '\n'] + total_trans
    for i in range(len(total_trans)):
        if '(' in total_trans[i]:
            variable_name = total_trans[i].split('(')[1][0]
            if variable_name in variable_value.keys():
                continue
            elif variable_name in ['A', 'B', 'C', 'D', 'E']:
                variable_value[variable_name] = comm_user_id[myPRNG.randint(0, contention_size - 1)]
            else:
                variable_value[variable_name] = myPRNG.randint(0, data_size)
    # print variable_value
    for entry in variable_value:
        # print entry, variable_value[entry]
        total_trans.insert(1, entry + ' = ' + str(variable_value[entry]) + '\n')
    length = len(total_trans)
    i = 0
    commit_medium_contention = 0
    finishset = []
    # for i in range(len(total_trans)):
    j = length - 1
    while j > 0 :
        if 'READ' in total_trans[j]:
            breakup = total_trans[j].split('(')[0][4:]
            if not breakup in finishset:
                total_trans.insert(j + 1, 'COMMIT' + breakup + '\n')
                finishset.append(breakup)
                length += 1
                commit_medium_contention += 1
        elif 'WRITE' in total_trans[j]:
            breakup = total_trans[j].split('(')[0][5:]
            if not breakup in finishset:
                total_trans.insert(j + 1, 'COMMIT' + breakup + '\n')
                finishset.append(breakup)
                length += 1
                commit_medium_contention += 1
        else:
            pass
        j -= 1

    total_trans_read_to = [','.join(['T' + str(i + 1) for i in range(trans_reqd)]) + '\n'] \
                          + total_trans
    ycsb_test_to = ''.join(total_trans_read_to)
    ycsb_test = ''.join(total_trans)

    return ycsb_test, ycsb_test_to

def high_contention():
    global trans_reqd, commit_high_contention
    variable_value = {}
    total_trans = []
    flag = "high_contention"
    for i in range(1, trans_reqd + 1):
        total_trans += create_trans(i, flag)

    random.shuffle(total_trans)

    total_trans = ['T = ' + str(trans_reqd) + '\n'] + total_trans
    for i in range(len(total_trans)):
        if '(' in total_trans[i]:
            variable_name = total_trans[i].split('(')[1][0]
            if variable_name in variable_value.keys():
                continue
            elif variable_name in ['A', 'B', 'C', 'D', 'E', 'F']:
                variable_value[variable_name] = comm_user_id[myPRNG.randint(0, contention_size - 1)]
            else:
                variable_value[variable_name] = myPRNG.randint(0, data_size)
    # print variable_value
    for entry in variable_value:
        # print entry, variable_value[entry]
        total_trans.insert(1, entry + ' = ' + str(variable_value[entry]) + '\n')

    length = len(total_trans)
    i = 0
    commit_high_contention = 0
    finishset = []
    # for i in range(len(total_trans)):
    j = length - 1
    while j > 0 :
        if 'READ' in total_trans[j]:
            breakup = total_trans[j].split('(')[0][4:]
            if not breakup in finishset:
                total_trans.insert(j + 1, 'COMMIT' + breakup + '\n')
                finishset.append(breakup)
                length += 1
                commit_high_contention += 1
        elif 'WRITE' in total_trans[j]:
            breakup = total_trans[j].split('(')[0][5:]
            if not breakup in finishset:
                total_trans.insert(j + 1, 'COMMIT' + breakup + '\n')
                finishset.append(breakup)
                length += 1
                commit_high_contention += 1
        else:
            pass
        j -= 1
        
    total_trans_read_to = [','.join(['T' + str(i + 1) for i in range(trans_reqd)]) + '\n'] \
                          + total_trans
    ycsb_test_to = ''.join(total_trans_read_to)
    ycsb_test = ''.join(total_trans)
    # print ycsb_test
    return ycsb_test, ycsb_test_to


# Test write and read requests
def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    provider = Web3.HTTPProvider("your web3 provider")
    web3 = Web3(provider)
    contract_address = 'your smart contract address'
    with open('/home/linqi/zksoltest/build/contracts/Verifier.json', 'r') as f:
        contract_abi = json.load(f)['abi']
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)
    acct = web3.eth.account.from_key("your wallet key")
    current_root = str(contract.functions.look_oplast_root().call())
    # print("Running client")
    ycsb_test, ycsb_test_to = high_contention()
    options = [('grpc.max_receive_message_length', 1024 * 1024 * 1024)]
    # with grpc.insecure_channel('10.140.83.115:50051', options=options) as channel:
    with grpc.insecure_channel('localhost:50051', options=options) as channel:
        stub = usgrpc.UpdateNodeStub(channel)
        request_start_time = time.perf_counter()
        for i in range(2048):
            task = us.Transaction(key = ycsb_test[i],val = ycsb_test[i] +'a', sequenceNumber=i)
            Task.append(task)
        request_end_time = time.perf_counter()
        print(request_end_time-request_start_time)
        star_time = time.perf_counter()
        for item in Task:
            response = stub.Update(item)
        #response = stub.Update(Task0)
        ReadTask = []
        options = [('grpc.max_receive_message_length', 1024 * 1024 * 1024)]
        with grpc.insecure_channel('localhost:50053', options=options) as channel:
            stub = bsgrpc.BackupNodeStub(channel)
            for i in range(2048):
                Readtask = bs.searchKey(key = ycsb_test[i])
                ReadTask.append(Readtask)

            for item in ReadTask:
                res = stub.Search(item)



        options = [('grpc.max_receive_message_length', 1024 * 1024 * 1024)]
        with grpc.insecure_channel('localhost:50053', options=options) as channel:
            stub = bsgrpc.BackupNodeStub(channel)
            Task = bs.ValidIndex(Index = 41)
            response1 = stub.Insertlog(Task)
            print(response1.Index)
            print('finished verify block')

        options = [('grpc.max_receive_message_length', 1024 * 1024 * 1024)]
    # with grpc.insecure_channel('10.140.83.115:50051', options=options) as channel:
        with grpc.insecure_channel('localhost:50053', options=options) as channel:
            stub = bsgrpc.BackupNodeStub(channel)
            Read0 = bs.searchKey(key = ycsb_test[i])
            res = stub.Search(Read0)
            print(res.value)

        if response.proof is not None:
            proof_check(response.proof,response.Opindex,item)
        
        

        # print(response.Opindex)
        # print(response.width)
        # response = stub.Update(Task1)
        # print(response.Opindex)
        # print(response.width)
        # response = stub.Update(Task2)
        # print(response.Opindex)
        # print(response.width)
        # response = stub.Update(Task3)
        # print(response.Opindex)
        # print(response.width)


# Test write request
def run1():
    provider = Web3.HTTPProvider("your web3 provider")
    web3 = Web3(provider)
    contract_address = 'your smart contract address'
    with open('/home/linqi/zksoltest/build/contracts/Verifier.json', 'r') as f:
        contract_abi = json.load(f)['abi']
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)
    acct = web3.eth.account.from_key("your wallet key")
    current_root = str(contract.functions.look_oplast_root().call())
    # print("Running client")
    ycsb_test, ycsb_test_to = medium_contention()
    options = [('grpc.max_receive_message_length', 1024 * 1024 * 1024)]
    # with grpc.insecure_channel('10.140.83.115:50051', options=options) as channel:
    with grpc.insecure_channel('localhost:50051', options=options) as channel:
        stub = usgrpc.UpdateNodeStub(channel)
        Task = []
        request_start_time = time.perf_counter()
        for i in range(128):
            task = us.Transaction(key = ycsb_test[i],val = ycsb_test[i] +'a', sequenceNumber=i)
            Task.append(task)
        request_end_time = time.perf_counter()
        print(request_end_time-request_start_time)
        star_time = time.perf_counter()
        for item in Task:
            response = stub.Update(item)

# Test read request
def run2():
    ReadTask = []
    ycsb_test, ycsb_test_to = read_only()
    options = [('grpc.max_receive_message_length', 1024 * 1024 * 1024)]
    with grpc.insecure_channel('localhost:50053', options=options) as channel:
        stub = bsgrpc.BackupNodeStub(channel)
        for i in range(128):
            Readtask = bs.searchKey(key = ycsb_test[i])
            ReadTask.append(Readtask)

        for item in ReadTask:
            res = stub.Search(item)


if __name__ == '__main__':
    #run()
    run1()
