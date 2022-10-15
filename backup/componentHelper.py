# LSMTree component algorithm
import math
#from LSMTree import Block
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



def merge_sort_blockComponent(component, index):
    keys = []
    values = []
    keys.extend(component.blocks[0].keys)
    values.extend(component.blocks[0].values)
    component.blocks.clear()
    merge_sort_component(keys,values)
    numOfElementsPerBlock = component.maxNoOfElements/component.numOfBlocks
    counter = math.ceil(len(keys)/numOfElementsPerBlock)
    cnt = 0
    b = Block()
    for i in range(counter):
        b.createBlock(component.levelName, 1, numOfElementsPerBlock)
        j = 0
        while j<numOfElementsPerBlock and cnt < len(keys):
            b.keys.append(keys[cnt])
            b.values.append(values[cnt])
            cnt += 1
            j += 1
    
    component.blocks.append(b)
    component.blocks[0].actualNoOfElements = len(b.keys)
    keys.clear()
    values.clear()

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

def compact(mergedKeys, mergedValues):
        keys = mergedKeys
        values = mergedValues
        length = len(keys)
        lastItem = keys[length - 1]

        for i in range(length - 2,-1,-1):
                currentItem = keys[i]
                if currentItem == lastItem:
                        values.pop(keys.index(currentItem))
                        keys.remove(currentItem)
                else:
                        lastItem = currentItem
        return keys,values

def modifiedLinearSearch(keys, key):
    length = len(keys)
    blocksToBeSearched = []
    for i in range(length):
        if key >= keys[i].getMin() and key <= keys[i].getMax():
            blocksToBeSearched.append(i)

    return blocksToBeSearched

def binarySearch(keys, key, low, high):
    if low <= high:
        middle = int(low+(high - low)/2)
        if key == keys[middle]:
            return middle
        elif key < keys[middle]:
            return binarySearch(keys,key,low,middle-1)
        else:
            return binarySearch(keys,key,middle+1,high)

    return -1
if __name__ == '__main__':
    merge_sort_component([45,27,46,27,27,87,45,27],['45','27','46','272','273','87','451','274'])
    key, va = mergeLists_forBlocks([27,27,27,27,45,45,46,87],['27','272','273','274','45','451','46','87'],[27,45,89,100],['270','450','89','100'])
    compact(key,va)