from bitarray import bitarray
import hashlib
import math
import componentHelper as componentHelper
from Rollup import Rollup
from web3 import Web3
import json
import copy
import pathlib
from merklelib import MerkleTree
import threading
import collections
import time
class KVPair:
    def __init__(self, keyList, valueList):
        self.keys = []
        self.values = []
        self.keys.extend(keyList)
        self.values.extend(valueList)  
    
    def getKeys(self):
        return self.keys
    
    def getValues(self):
        return self.values

class MinMaxPair:
    def __init__(self, min, max):
        self.min = min
        self.max = max
    
    def getMin(self):
        return self.min

    def getMax(self):
        return self.max

class DirectoryOfKeysPerBlock:
    def __init__(self):
        self.numOfComponents = 0
        self.numOfBlocksPerComp = []
        self.keyList = []

    def createDirectory(self, numOfComponents, numOfBlocksPerComponent):
        self.numOfComponents = numOfComponents
        self.numOfBlocksPerComp = numOfBlocksPerComponent
        mmPair = MinMaxPair(-1,-1)
        mmlist = []
        for i in range(self.numOfComponents):
            for j in range(self.numOfBlocksPerComp[i]):
                mmlist.append(mmPair)
            self.keyList.append(mmlist)
            mmlist = []

    def updateKeyPerBlock(self, level, blockNo, pair):
        self.keyList[level][blockNo] = pair

    def getKeysPerLevel(self, level):
        return self.keyList[level]

class Block:
    def __init__(self):
        self.blockName = ''
        self.maxNoOfElements = 0
        self.actualNoOfElements = 0
        self.keys = []
        self.values = []
        self.levelName = ''
        self.keyFilePath = ''
        self.valueFilePath = ''
    
    def createBlock(self, levelName, j, maxNoOfElementsPerBlock):
        self.levelName = levelName
        self.blockName = "B" + str(j)
        self.maxNoOfElements = maxNoOfElementsPerBlock
        self.actualNoOfElements = 0
        self.keys = []
        self.values = []
        self.keyFilePath = "/home/cc/rlsm_test/collector/data/key_" + self.levelName + "_" +self.blockName + ".txt"
        self.valueFilePath = "/home/cc/rlsm_test/collector/data/value_" + self.levelName + "_" +self.blockName + ".txt"

        pathlib.Path(self.keyFilePath).touch()
        pathlib.Path(self.valueFilePath).touch()


    def insertKV(self, key, value):
        self.keys.append(key)
        self.values.append(value)
        self.actualNoOfElements +=1
    
    def writeBlock(self, diskComp, directory):
        min = -1
        max = -1
        if diskComp:

            with open(self.keyFilePath,mode='r+',encoding='utf-8') as ff:
                ff.seek(0)
                ff.truncate()
            ff.close()
            with open(self.valueFilePath,mode='r+',encoding='utf-8') as ff:
                ff.seek(0)
                ff.truncate()
            ff.close()

            for i in range(len(self.keys)):
                if i == 0 and diskComp:
                    min = self.keys[i]
                if i == len(self.keys)-1 and diskComp:
                    max = self.keys[i]
                
                with open(self.keyFilePath,mode='a',encoding='utf-8') as ff:
                        ff.write(str(self.keys[i])+'\n')
                ff.close()    

            for value in self.values:
                with open(self.valueFilePath,mode='a',encoding='utf-8') as f:
                        f.write(value+'\n')
                f.close()
        self.actualNoOfElements = len(self.keys)
        if diskComp:
            if self.levelName[1] == '1':
                level = 1
            else: 
                level = 2
            
            blockNo = int(self.blockName[1:])
            pair = MinMaxPair(min, max)
            directory.updateKeyPerBlock(level - 1, blockNo, pair)

    def setActualNoOfElements(self, actualNoOfElements):
        self.actualNoOfElements = actualNoOfElements

class BlockComponent:
    def __init__(self):
        self.numOfBlocks = 0
        self.blocks = []
        self.numOfEmptyBlocks = 0
        self.indexOfFirstEmptyBlock = 0
        self.levelName = ''
        self.actualNoOfElements = 0
        self.maxNoOfElements = 0
    
    def createComponent(self, numOfBlocks, levelName, maxNumOfElementsPerBlock):

        self.numOfBlocks = numOfBlocks
        self.levelName = levelName
        for i in range(numOfBlocks):
            b = Block()
            b.createBlock(levelName,i,maxNumOfElementsPerBlock)
            self.blocks.append(b)

        self.numOfEmptyBlocks = 0
        self.indexOfFirstEmptyBlock = 0
        self.maxNoOfElements = numOfBlocks * maxNumOfElementsPerBlock
        self.actualNoOfElements = 0

    def insertInBlock(self, key,value):
        if self.actualNoOfElements < self.maxNoOfElements:
            self.blocks[0].insertKV(key, value)
            self.actualNoOfElements += 1
    
    def getMaxNoOfElements(self):
        return self.maxNoOfElements
    
    def getActualNoOfElements(self):
        return self.actualNoOfElements

    def writeComponent(self, diskComp, directory):
        for i in range(self.numOfBlocks):
            self.writeBlockOfComponent(i,diskComp, directory)

    def writeBlockOfComponent(self, index, diskComp, directory):
        self.blocks[index].writeBlock(diskComp, directory)

    def moveToNextComponent(self, current, next, index,  diskComp, directory):
        sum = 0
        blocks = []
        for i in range(current.numOfBlocks-index, current.numOfBlocks):
            blocks.append(current.blocks[i])
            sum += current.blocks[i].actualNoOfElements
        
        next.blocks[0].keys.extend(blocks[0].keys)
        next.blocks[0].values.extend(blocks[0].values)
        next.actualNoOfElements += sum
        next.blocks[0].actualNoOfElements +=sum
        current.actualNoOfElements -= sum
        current.blocks[0].keys.clear()
        current.blocks[0].values.clear()
        current.blocks[0].actualNoOfElements -= sum
        blocks.clear()
        current.writeComponent(diskComp, directory)
        next.writeComponent(diskComp, directory)

    def movePairsToNextComponent(self, pair, next, diskComp, directory):
        b = Block()
        b.createBlock(next.levelName,next.numOfBlocks+1,next.maxNumOfElementsPerBlock)
        next.blocks.append(b)
        next.blocks[next.numOfBlocks+1].keys.extend(pair.getKeys())
        next.blocks[next.numOfBlocks+1].values.extend(pair.getValues())
        next.blocks[next.numOfBlocks+1].actualNoOfElements = len(pair.getKeys())
        next.actualNoOfElements = next.actualNoOfElements + len(pair.getKeys())
        next.numOfBlocks += 1
        next.writeComponent(diskComp, directory)

    def compact(self, pair):
        keys = pair.getKeys()
        values = pair.getValues()
        length = len(keys)
        lastItem = keys[length - 1]

        for i in range(length - 2,-1,-1):
                currentItem = keys[i]
                if currentItem == lastItem:
                        values.pop(keys.index(currentItem))
                        keys.remove(currentItem)
                else:
                        lastItem = currentItem
        return KVPair(keys,values)

    def compactallblock(self, pair,Components,directory):
        ckeys = pair.getKeys()
        cvalues = pair.getValues()
        nkeys = []
        nvalues = []
        for i in range(Components.numOfBlocks):
            nkeys.extend(Components.blocks[i].keys)
            nvalues.extend(Components.blocks[i].values)

        mkeys, mvalues = componentHelper.mergeLists_forBlocks(ckeys, cvalues, nkeys, nvalues)
        total_pair = KVPair(mkeys, mvalues)
        total_compacted_pair = self.compact(total_pair)
        maxNoOfElements = Components.blocks[0].maxNoOfElements
        blocknum = math.ceil(len(total_compacted_pair.getKeys())/maxNoOfElements)
        for i in range(blocknum):
            
            Components.blocks[i].keys.clear()
            Components.blocks[i].values.clear()
            Components.blocks[i].setActualNoOfElements(0)
            if i == blocknum - 1:
                Components.blocks[i].keys.extend(total_compacted_pair.getKeys()[i*maxNoOfElements:])
                Components.blocks[i].values.extend(total_compacted_pair.getValues()[i*maxNoOfElements:])
                Components.blocks[i].setActualNoOfElements(len(total_compacted_pair.getKeys()[i*maxNoOfElements:]))
            else:
                Components.blocks[i].keys.extend(total_compacted_pair.getKeys()[i*maxNoOfElements:(i+1)*maxNoOfElements])
                Components.blocks[i].values.extend(total_compacted_pair.getValues()[i*maxNoOfElements:(i+1)*maxNoOfElements])
                Components.blocks[i].setActualNoOfElements(maxNoOfElements)
        
        Components.actualNoOfElements = len(total_compacted_pair.getKeys())
        Components.writeComponent(True,directory)


class BloomFilter:
    def __init__(self):
        self.valid_digit = 1  # range from 6 to 8
        self.array_size = 16 ** self.valid_digit
        self.bitArray = bitarray(self.array_size)
        self.bitArray.setall(False)
        self.actualNumOfElements = 0

    def createFilter(self, digit):
        self.valid_digit = digit  # range from 6 to 8
        self.array_size = 16 ** self.valid_digit
        self.bitArray = bitarray(self.array_size)
        self.bitArray.setall(False)

    def contains(self, key):
        ekey = str.encode(str(key))
        v1, v2, v3 = self.hash_functions(ekey)
        if self.bitArray[v1] and self.bitArray[v2] and self.bitArray[v3]:
            return True
        return False

    def add(self, key):
        ekey = str.encode(str(key))
        v1, v2, v3 = self.hash_functions(ekey)
        self.bitArray[v1] = True
        self.bitArray[v2] = True
        self.bitArray[v3] = True
        self.actualNumOfElements +=1

    def hash_functions(self, key):
        hash1 = hashlib.sha224(key)
        hash2 = hashlib.sha256(key)
        hash3 = hashlib.sha1(key)
        v1 = int(hash1.hexdigest()[-self.valid_digit:], 16)
        v2 = int(hash2.hexdigest()[-self.valid_digit:], 16)
        v3 = int(hash3.hexdigest()[-self.valid_digit:], 16)
        return v1, v2, v3


class LSMTree:
    def __init__(self):
        self.numOfComponents = 0
        self.numOfBlocksInMemory = 0
        self.numOfBlocksInDisk = 0
        self.factor = 0
        self.maxNumOfElementsPerBlock = 0
        self.valueSize = 0
        self.ImmutableMemtable = BlockComponent()
        self.diskComponents = BlockComponent()
        self.bloomFilter = BloomFilter()
        self.isBloomEnabled = True
        self.hashes = 3
        self.directory = DirectoryOfKeysPerBlock()
        self.num_append = 0
        self.level = 3
        self.dictpair = {}
        self.dictproof = {}
        self.dict_single_proof = {}
        self.checkedpair = []
        self.search_list = []
        self.opindex = 59
        self.validindex = 59
        self.backup_waiting_buffer = collections.OrderedDict()
        self.backup_manager_lock = threading.Lock()
        
        self.backup_verify_buffer = collections.OrderedDict()
        self.verify_manager_lock = threading.Lock()

        self.search_buffer_dict = collections.OrderedDict()
        self.search_manager_lock = threading.Lock()

        # stage 2 verify manager thread
        self.verfied_manager_thread = threading.Thread(
            target=self.verfied_manager, name="verfied_manager_thread", daemon=True)
        self.verfied_manager_thread.start()
        # stage 1 insert manager thread
        self.insert_manager_thread = threading.Thread(
            target=self.insert_manager, name="insert_manager_thread", daemon=True)
        self.insert_manager_thread.start()
        # read search manager thread
        self.search_manager_thread = threading.Thread(
            target=self.search_manager, name="search_manager_thread", daemon=True)
        self.search_manager_thread.start()

    def createLSMTree(self, numOfComponents, numOfBlocksInMemory, numOfBlocksInDisk, maxNumOfElementsPerBlock, valueSize, isBloomEnabled):
        self.numOfComponents = numOfComponents
        self.valueSize = valueSize
        self.numOfBlocksInMemory = numOfBlocksInMemory
        self.numOfBlocksInDisk = numOfBlocksInDisk
        self.maxNumOfElementsPerBlock = maxNumOfElementsPerBlock

        self.isBloomEnabled = isBloomEnabled

        if self.isBloomEnabled: 
            self.bloomFilter.createFilter(8)
        
    def buildLSMTreeInMemoryComponents(self):
        self.ImmutableMemtable.createComponent(self.numOfBlocksInMemory,"L1",self.maxNumOfElementsPerBlock)

    def buildLSMTreeDiskComponents(self):
        self.diskComponents.createComponent(self.numOfBlocksInDisk,"L2", self.maxNumOfElementsPerBlock)
        self.directory.createDirectory(self.numOfComponents,[self.numOfBlocksInMemory,self.numOfBlocksInDisk])
    # verify stage 1 pages
    def add_buffle(self, croot, nroot, pair, index):
        start_time = time.perf_counter()
        provider = Web3.HTTPProvider("web3 provider")
        web3 = Web3(provider)
        contract_address = 'smart contract address'
        with open('/home/cc/rlsm-test/contracts/Verifier.json', 'r') as f:
            contract_abi = json.load(f)['abi']
            
        contract = web3.eth.contract(address=contract_address, abi=contract_abi)
        new_root_hash = str(contract.functions.look_op_root(index).call())
        old_root_hash = str(contract.functions.look_op_root(index-1).call())
        print(new_root_hash)
        print(old_root_hash)
        print(croot)
        print(nroot)
        assert old_root_hash == croot
        assert new_root_hash == nroot

        keys = pair.getKeys()
        values = pair.getValues()
        newitem = []
        proofs = []
        tree = MerkleTree()
        for i in range(len(keys)):
            key = str(keys[i])
            val = values[i]
            stritem = key +';'+val
            newitem.append(stritem)
        for item in newitem:
            tree.append(item)
        print(int(tree.merkle_root,16))
        assert new_root_hash == str(int(tree.merkle_root,16))

        self.dictpair[str(index)] = pair
        self.backup_waiting_buffer[str(index)] = pair
        end_time = time.perf_counter()
        print('local process time:' + str(end_time - start_time))
        first_proof_time = time.perf_counter()
        for item in newitem:
            proof = tree.get_proof(item)
            self.dict_single_proof[item.split(';')[0]] = proof
            proofs.append(proof)
        last_proof_time = time.perf_counter()
        print('proofs process time:' + str(last_proof_time - first_proof_time))
        self.dictproof[str(index)] = proofs
    # insert stage 1 pages
    def insert_manager(self):
        while True:
            while len(self.backup_waiting_buffer) != 0:
                insert_start_time = time.perf_counter()
                self.backup_manager_lock.acquire()
                self.opindex += 1 
                print(str(self.opindex))
                print(self.dictpair)
                keys = self.dictpair[str(self.opindex)].getKeys()
                if self.isBloomEnabled:
                    for key in keys:
                        self.bloomFilter.add(key)
                        
                self.append_block()
                del self.backup_waiting_buffer[str(self.opindex)]
                self.backup_manager_lock.release()
                insert_end_time = time.perf_counter()
                print('insert process time:' + str(insert_end_time - insert_start_time))
                print('stage 1 finished')
                # options = [('grpc.max_receive_message_length', 1024 * 1024 * 1024)]
                # with grpc.insecure_channel('localhost:50053', options=options) as channel:
                #     stub = bsgrpc.BackupNodeStub(channel)
                #     Task = bs.OpBatch(current_root = str(start_root),new_root = str(new_root), Index = opindex, key = item.getKeys(), value = item.getValues())
                #     response1 = stub.InsertBlock(Task)
                #     print(response1.Index)
                #     print('stage 1 finished')

    
    def append_block(self):
        prepared_pair = copy.deepcopy(self.dictpair[str(self.opindex)])

        compacted_pair = self.ImmutableMemtable.compact(prepared_pair)
        b = Block()
        b.createBlock('L1',len(self.ImmutableMemtable.blocks),self.maxNumOfElementsPerBlock)
        self.ImmutableMemtable.blocks.append(b)
        self.ImmutableMemtable.blocks[self.opindex].keys.extend(compacted_pair.getKeys())
        self.ImmutableMemtable.blocks[self.opindex].values.extend(compacted_pair.getValues())
        self.ImmutableMemtable.blocks[self.opindex].actualNoOfElements = len(compacted_pair.getKeys())
        self.ImmutableMemtable.actualNoOfElements = self.ImmutableMemtable.actualNoOfElements + len(compacted_pair.getKeys())
        self.ImmutableMemtable.numOfBlocks += 1
        self.ImmutableMemtable.writeBlockOfComponent(self.opindex, True, self.directory)
        #print(self.ImmutableMemtable.blocks[self.opindex].keys)
        print('append block finished')
    
    def insert_disk(self, index):
        self.backup_verify_buffer[str(index)] = index
    
    def verfied_manager(self):
        while True:
            while len(self.backup_verify_buffer) != 0:
                self.verify_manager_lock.acquire()
                indexes = list(self.backup_verify_buffer.keys())
                if str(self.validindex+1) in indexes:
                    self.validindex += 1
                    self.insert_log_block(self.validindex)
                
                    del self.backup_verify_buffer[str(self.validindex)]
                    self.verify_manager_lock.release()
                    print('stage 2 finished')
    # insert stage 2 pages
    def insert_log_block(self,index):
        verfied_pair = copy.deepcopy(self.dictpair[str(index)])
        compacted_pair = self.ImmutableMemtable.compact(verfied_pair)
        self.diskComponents.compactallblock(compacted_pair,self.diskComponents, self.directory)
        self.ImmutableMemtable.blocks[index].keys.clear()
        self.ImmutableMemtable.blocks[index].values.clear()
        self.ImmutableMemtable.blocks[index].setActualNoOfElements(0)
        self.ImmutableMemtable.actualNoOfElements = self.ImmutableMemtable.actualNoOfElements - len(compacted_pair.getKeys())
        self.ImmutableMemtable.numOfBlocks -= 1
        self.ImmutableMemtable.writeBlockOfComponent(index, True, self.directory)

        print(self.diskComponents.blocks[self.validindex].keys)
        print('insert log finished')
    # read search
    def readkey(self, key):
        if self.isBloomEnabled and self.bloomFilter.contains(key)==False:
            return None,None
        index = -1
        for i in range(2):
            blocksToBeSearched = componentHelper.modifiedLinearSearch(self.directory.getKeysPerLevel(i),key)
            for j in range(len(blocksToBeSearched)):
                if i == 0:
                    keys = self.ImmutableMemtable.blocks[blocksToBeSearched[len(blocksToBeSearched)-1-j]].keys
                else:
                    keys = self.diskComponents.blocks[blocksToBeSearched[len(blocksToBeSearched)-1-j]].keys
                index = componentHelper.binarySearch(keys,key,0,len(keys)-1)
                if index != -1:
                    if i == 0:
                        value = self.ImmutableMemtable.blocks[blocksToBeSearched[len(blocksToBeSearched)-1-j]].values[index]
                    else:
                        value = self.diskComponents.blocks[blocksToBeSearched[len(blocksToBeSearched)-1-j]].values[index]
                    return value,i
        return None,None
    def search(self, key):
        search_start_time = time.perf_counter()
        result,level = self.readkey(key)
        if result != None:
            #print(self.dict_single_proof)
            response = [result,self.dict_single_proof[str(key)],level]
        else:
            response = [result, None, None]
        search_end_time = time.perf_counter()
        #print('search process time:' + str(search_end_time - search_start_time))
        return response

    def search_buffer(self, key):
        self.search_list.append(key)
        if len(self.search_list) == 8192:
            self.search_buffer_dict[str(self.opindex)] = self.search_list
            
    
    def search_manager(self):
         while True:
            while len(self.search_buffer_dict) != 0:
                result = []
                search_start_time = time.perf_counter()
                self.search_manager_lock.acquire()
                opindex = list(self.search_buffer_dict.keys())
                keys = self.search_buffer_dict[opindex[0]]
                for key in keys:
                    res = self.search(key)
                    result.append(res)
                self.search_list.clear()
                del self.search_buffer_dict[opindex[0]]
                self.search_manager_lock.release()
                search_end_time = time.perf_counter()
                print('search process time:' + str(search_end_time - search_start_time))
                # for item in result:
                #     print(item[0])
                print('search finished')
                

if __name__ == '__main__':
    # test = LSMTree()
    # mmr_L1 = Rollup()
    # mmr_L2 = Rollup()
    # test.createLSMTree(2,20,30,4,12,True)#numOfComponents, numOfBlocksInMemory, numOfBlocksInDisk, maxNumOfElementsPerBlock, valueSize, isBloomEnabled
    # test.buildLSMTreeInMemoryComponents()
    # test.buildLSMTreeDiskComponents()
    # pair = KVPair([5, 5, 5, 5, 5, 5, 5, 5], ['5ab0', '5ab1', '5ab2', '5ab3', '5ab4', '5ab5', '5ab6', '5ab7'])
    # pair2 = KVPair([5, 6, 6, 7, 7, 8, 8, 9], ['5ab8', '6ab0', '6ab1', '7ab0', '7ab1', '8ab0', '8ab1', '9ab0'])
    # test.add_buffle(pair,0)
    # test.insert_block(mmr_L1)
    # test.insert_log_block(mmr_L2)
    # test.add_buffle(pair2,1)
    # test.insert_block(mmr_L1)
    # test.insert_log_block(mmr_L2)
    # print(test.search(7))
    test = LSMTree()
    test.createLSMTree(2,20,30,4,12,True)
    test.buildLSMTreeInMemoryComponents()
    test.buildLSMTreeDiskComponents()
    pair = KVPair([10, 11], ['10a', '11a'])
    start_root = '1'
    new_root = '13338087817907784051592757810517230450287288234474268901909769169482516545919'
    opindex = 1
    test.add_buffle(start_root, new_root, pair,opindex)
    test.insert_block(opindex)
    print(test.search(10))