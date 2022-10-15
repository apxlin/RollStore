# test the proof parameters and send it to the smart contract
from eth_abi import encode_abi
from web3 import Web3
import json

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


provider = Web3.HTTPProvider("http://127.0.0.1:9545")
web3 = Web3(provider)
contract_address = '0xb44E9A279BA318bb20838Fff7c8ee75e9DaD504E' #change
with open('/home/linqi/zk_lsm/prover/Verifier.json', 'r') as f:
    contract_abi = json.load(f)['abi']
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

acct = web3.eth.accounts[0]

# ac = encode_abi(['uint256[2]'], [[12345,12568]])
# print(ac)
# ac = encode_abi(['uint256[2][2]'], [[12345,12568,12356,45895]])
# print(ac)

a = ["0x08aeb9d0a4a3e126bb0b3a4e1fdbb315e5c35bd06a808dbae934ee91ba68c31c","0x23ef1c03d1574589cf77a704212a73ee2a86919d173c47c5d58499d254f9cca2"]
b = [["0x0ef77e873d496301df0ffcb0faa49be3fa55a03426fc0d0b6318ca60b762ffa6","0x1ef71384f88c3375f8567e9c8e250d88de597f25cbf1800f763277156c79b13d"],
["0x0adfeef35c102618bfd8282ff027cd3b661b43e4d8fb3e7b1ca86c9b77d2a5d3","0x293899cd2dc2a3843f77518cedd7a31bc4a5feb5d834ac0f65a6af874cc61069"]]
c = ["0x1ea31262d3d04449d9f2540d1bb3ea76c63d129ca7a1d5c6c0f36d6d98d223b6","0x2f91158a5765d88e2b37673e901e30016cee3168b464cc78e285ec0b819abe64"]
inputs = ["0x29256c25cff8f019088e1e0cd24ad161160ee19e88f61e5f7a7ad81081569c81","0x0000000000000000000000000000000000000000000000000000000000000002",
"0x0e77c759b81e5104d25b4cb1b6daf9e294e48e1526872a556a601540bf9eb316","0x10d833c66ce555433fc615df73cfcee9db68c778c1b464c162a2c50f09be58c0",
"0x25f95ce77e2836304ddbc9fec27f8d605b75f56cc86e4a8fe1205c61c957e06e","0x2fe2522c643eedfafa02a46faf040d45f1c48b535a1ddbef58df93f1ae62d5df",
"0x245d4086402bd1251821d64a8886c7e276b47663a9bf774feba11485da477476","0x0000000000000000000000000000000000000000000000000000000000000001"]

aint = [int(a[0],16),int(a[1],16)]
bint = [[int(b[0][0],16),int(b[0][1],16)],[int(b[1][0],16),int(b[1][1],16)]]
cint = [int(c[0],16),int(c[1],16)]
inputsint = [int(inputs[0],16),int(inputs[1],16),int(inputs[2],16),int(inputs[3],16),int(inputs[4],16),int(inputs[5],16),int(inputs[6],16),int(inputs[7],16)]
#contract.encodeABI(fn_name="verifyTx", args=[a,b,c,inputs])
ac = encode_abi(['uint256[2]','uint256[2][2]','uint256[2]','uint256[8]'], [aint,bint,cint,inputsint])
estimatedGas = contract.functions.verifyTx(a,b,c,inputsint).estimateGas()
tx = contract.functions.verifyTx(aint,bint,cint,inputsint).buildTransaction({
            'gas': estimatedGas,
            'from': acct.address,
            'nonce': web3.eth.getTransactionCount(acct.address)})
signed = acct.signTransaction(tx) 
tx_id = web3.eth.sendRawTransaction(signed.rawTransaction)
print(tx_id)