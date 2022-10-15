# Componet of LSM


class MinMaxPair:
    def __init__(self, min, max):
        self.min = min
        self.max = max

class Block:
    def __init__(self):
        self.blockName = ''
        self.maxNoOfElements = 0
        self.actualNoOfElements = 0
        self.keys = []
        self.values = []
        self.levelName = ''
    
    def createBlock(self, levelName, j, maxNoOfElementsPerBlock):
        self.levelName = levelName
        self.blockName = "B" + str(j)
        self.maxNoOfElements = maxNoOfElementsPerBlock
        self.actualNoOfElements = 0



    def insertKV(self, key, value):
        self.keys.append(key)
        self.values.append(value)
        self.actualNoOfElements +=1
    
    

    def setActualNoOfElements(self, actualNoOfElements):
        self.actualNoOfElements = actualNoOfElements
