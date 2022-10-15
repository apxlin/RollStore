# Componet of LSM
from Block import MinMaxPair
import math
from Block import Block
import copy

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

def merge_sort_component(keys, values):
    if len(keys)<=1: 
        return; # small list don't need to be merged


    mid = int(len(keys)/2); # estimate half the size

    leftKey = []
    rightKey = []
    leftValue = []
    rightValue = []

    for i in range(mid):
        leftKey.append(keys.pop(0))
        leftValue.append(values.pop(0))

    while len(keys)!=0:
        rightKey.append(keys.pop(0))
        rightValue.append(values.pop(0))
    
    merge_sort_component(leftKey,leftValue)
    merge_sort_component(rightKey,rightValue)

    while len(leftKey)!= 0 and len(rightKey) != 0:
        if leftKey[0] <= rightKey[0]:
            keys.append(leftKey.pop(0))
            values.append(leftValue.pop(0))
        else:
            keys.append(rightKey.pop(0))
            values.append(rightValue.pop(0))
    
    while len(leftKey) != 0:
        keys.append(leftKey.pop(0))
        values.append(leftValue.pop(0))

    while len(rightKey) != 0:
        keys.append(rightKey.pop(0))
        values.append(rightValue.pop(0))



def merge_sort_blockComponent(component):
    keys = []
    values = []
    for i in range(len(component.blocks)):
        keys.extend(component.blocks[i].keys)
        values.extend(component.blocks[i].values)
    component.blocks.clear()
    merge_sort_component(keys,values)
    numOfElementsPerBlock = int(component.maxNoOfElements/component.numOfBlocks)
    counter = math.ceil(len(keys)/numOfElementsPerBlock)
    cnt = 0
    blist = []
    b = Block()
    for i in range(counter):
        b.createBlock(component.levelName, i, numOfElementsPerBlock)
        j = 0
        while j<numOfElementsPerBlock and cnt < len(keys):
            b.keys.append(keys[cnt])
            b.values.append(values[cnt])
            cnt += 1
            j += 1
        page = copy.deepcopy(b)
        blist.append(page)
        b.keys.clear()
        b.values.clear()
    for i in range(component.numOfBlocks):
        component.blocks.append(blist[i])
        component.blocks[i].actualNoOfElements = len(blist[i].keys)
    
    keys.clear()
    values.clear()

def mergeList_forComponent(current, next):
    currentKeys = []
    currentValues = []
    nextKeys = []
    nextValues = []
    for i in range(len(current.blocks)):
        currentKeys.extend(current.blocks[i].keys)
        currentValues.extend(current.blocks[i].values)

    for j in range(len(next.blocks)):
        nextKeys.extend(next.blocks[j].keys)
        nextValues.extend(next.blocks[j].values)

    return mergeLists_forBlocks(currentKeys, currentValues, nextKeys, nextValues)

def mergeLists_forBlocks(currentKeys, currentValues, nextKeys, nextValues):
    mergedKeys = []
    mergedValues = []
    left = 0
    right = 0
    while left < len(currentKeys) and right < len(nextKeys):
        if currentKeys[left] < nextKeys[right]:
            mergedKeys.append(currentKeys[left])
            mergedValues.append(currentValues[left])
            left += 1

        elif currentKeys[left] > nextKeys[right]:
            mergedKeys.append(nextKeys[right])
            mergedValues.append(nextValues[right])
            right += 1
        else:
            mergedKeys.append(nextKeys[right])
            mergedValues.append(nextValues[right])
            right += 1

    if left < len(currentKeys):
        while left < len(currentKeys):
            mergedKeys.append(currentKeys[left])
            mergedValues.append(currentValues[left])
            left += 1

    if right < len(nextKeys):
        while right < len(nextKeys):
            mergedKeys.append(nextKeys[right])
            mergedValues.append(nextValues[right])
            right += 1

    return mergedKeys, mergedValues

def clear_component(current):
    for i in range(len(current.blocks)):
        current.blocks[i].keys.clear()
        current.blocks[i].values.clear()
        current.blocks[i].setActualNoOfElements(0)
    current.actualNoOfElements = 0
    current.indexOfFirstEmptyBlock = 0
def moveToNextComponent(current, next):
        sum = 0
        blocks = []
        for i in range(current.numOfBlocks):
            blocks.append(current.blocks[i])
            sum += current.blocks[i].actualNoOfElements
        
        next.blocks[next.indexOfFirstEmptyBlock].keys.extend(blocks[0].keys)
        next.blocks[next.indexOfFirstEmptyBlock].values.extend(blocks[0].values)
        next.actualNoOfElements += sum
        next.blocks[next.indexOfFirstEmptyBlock].actualNoOfElements +=sum
        next.indexOfFirstEmptyBlock += 1
        next.numOfEmptyBlocks = next.numOfBlocks - next.indexOfFirstEmptyBlock
        current.actualNoOfElements -= sum
        current.blocks[0].keys.clear()
        current.blocks[0].values.clear()
        current.blocks[0].actualNoOfElements -= sum
        blocks.clear()

if __name__ == '__main__':
    merge_sort_component([45,27,46,27,27,87,45,27],['45','27','46','272','273','87','451','274'])
    key, va = mergeLists_forBlocks([27,27,27,27,45,45,46,87],['27','272','273','274','45','451','46','87'],[27,45,89,100],['270','450','89','100'])
    compact(key,va)