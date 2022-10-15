# Componet of LSM
from Block import Block

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
            b.createBlock(levelName,i+1,maxNumOfElementsPerBlock)
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


 
