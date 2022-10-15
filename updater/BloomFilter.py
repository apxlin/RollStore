# Componet of LSM
from bitarray import bitarray
import hashlib

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

