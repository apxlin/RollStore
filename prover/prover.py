from typing import List
from constant import G, H
import docker
from ethsnarks.field import FQ
from ethsnarks.jubjub import Point
import time
import json
from web3 import Web3
from jubjub import Field
from mmr import PedersenMMR



class prover:
    def __init__(self):
        self.proof = None
        self.mmr = PedersenMMR()
    
    def peak_existence(self,width, peak_height) -> bool:
        return width & (1 << (peak_height - 1)) != 0

    def width_from_peaks(self,peaks: List[Point]) -> int:
        width = 0
        for i in range(len(peaks)):
            peak_height = len(peaks) - i
            if peaks[i] != Point.infinity():
                width += 1 << (peak_height - 1)
        return width

    def peak_bagging(self, peaks: List[Point]) -> FQ:
        root_point = G
        width = self.width_from_peaks(peaks)
        for i in reversed(range(len(peaks))):
            # Starts from the right-most peak
            peak_height = len(peaks) - i
            peak = peaks[i]
            # With the mountain map, check the peak exists or not correctly
            assert (peak == Point.infinity()) is (False if self.peak_existence(width, peak_height) else True)
            # Update root point
            root_point = root_point * peak.y
        root_point = root_point * width
        return root_point.y
    # run docker to generate the proof parameters
    def zk_roll_up_proof(self, root, width, peaksx, peaksy, itemsx, itemsy, new_root):
        peaks = [Point(FQ(int(a)), FQ(int(b))) for a, b in zip(peaksx, peaksy)]
        items = [Point(FQ(int(a)), FQ(int(b))) for a, b in zip(itemsx, itemsy)]
        assert self.peak_bagging(peaks) == FQ(int(root))
        client = docker.from_env()
        assert len(items) in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048], "You can only roll up these items at once"
        start = time.time()
        proof_bytes = client.containers.run("test22",
                                            auto_remove=False,
                                            environment={"args": " ".join(map(str, [
                                                root,  # public
                                                width,  # public
                                                *[item.x for item in items],  # public
                                                *[item.y for item in items],  # public
                                                new_root,  # public
                                                *[peak.x for peak in peaks],
                                                *[peak.y for peak in peaks]
                                            ]))})
        print('Calculated zk roll up proof in {} seconds'.format(time.time() - start))
        client.close()
        proof = json.loads(proof_bytes.decode('utf-8'))
        return proof

    def generate_proof(self, current_root, current_width, current_peaksx, current_peaksy, items_to_updatex, items_to_updatey, new_root):
        proof = self.zk_roll_up_proof(current_root, current_width, current_peaksx, current_peaksy, items_to_updatex,items_to_updatey, new_root)
        with open('/home/linqi/zk_lsm/prover/proof.json', 'w+') as f:
            json.dump(proof, f)
        return proof
    # send proof parameters to the smart contract
    def send_proof(self, flag, proof):
        if flag == 0:
            provider = Web3.HTTPProvider("your web3 provider")
            web3 = Web3(provider)
            contract_address = 'your smart contract address'
            with open('/home/linqi/zksoltest/build/contracts/Verifier.json', 'r') as f:
                contract_abi = json.load(f)['abi']
            contract = web3.eth.contract(address=contract_address, abi=contract_abi)
            acct = web3.eth.account.from_key("your wallet key")

            #true argument
            a = proof['proof']['a']
            b = proof['proof']['b']
            c = proof['proof']['c']
            inputs = proof['inputs']
            # current argument
            # a = ["0x08aeb9d0a4a3e126bb0b3a4e1fdbb315e5c35bd06a808dbae934ee91ba68c31c","0x23ef1c03d1574589cf77a704212a73ee2a86919d173c47c5d58499d254f9cca2"]
            # b = [["0x0ef77e873d496301df0ffcb0faa49be3fa55a03426fc0d0b6318ca60b762ffa6","0x1ef71384f88c3375f8567e9c8e250d88de597f25cbf1800f763277156c79b13d"],
            #     ["0x0adfeef35c102618bfd8282ff027cd3b661b43e4d8fb3e7b1ca86c9b77d2a5d3","0x293899cd2dc2a3843f77518cedd7a31bc4a5feb5d834ac0f65a6af874cc61069"]]
            # c = ["0x1ea31262d3d04449d9f2540d1bb3ea76c63d129ca7a1d5c6c0f36d6d98d223b6","0x2f91158a5765d88e2b37673e901e30016cee3168b464cc78e285ec0b819abe64"]
            # inputs = ["0x29256c25cff8f019088e1e0cd24ad161160ee19e88f61e5f7a7ad81081569c81","0x0000000000000000000000000000000000000000000000000000000000000002",
            # "0x0e77c759b81e5104d25b4cb1b6daf9e294e48e1526872a556a601540bf9eb316","0x10d833c66ce555433fc615df73cfcee9db68c778c1b464c162a2c50f09be58c0",
            # "0x25f95ce77e2836304ddbc9fec27f8d605b75f56cc86e4a8fe1205c61c957e06e","0x2fe2522c643eedfafa02a46faf040d45f1c48b535a1ddbef58df93f1ae62d5df",
            # "0x245d4086402bd1251821d64a8886c7e276b47663a9bf774feba11485da477476","0x0000000000000000000000000000000000000000000000000000000000000001"]

            aint = [int(a[0],16),int(a[1],16)]
            bint = [[int(b[0][0],16),int(b[0][1],16)],[int(b[1][0],16),int(b[1][1],16)]]
            cint = [int(c[0],16),int(c[1],16)]
            inputsint = [0]*len(inputs)
            for i in range(len(inputs)):
                inputsint[i] = int(inputs[i],16)
            

            estimatedGas = contract.functions.verifyTx(aint,bint,cint,inputsint).estimateGas()
            tx = contract.functions.verifyTx(aint,bint,cint,inputsint).buildTransaction({
            'gas': estimatedGas,
            'from': acct.address,
            'nonce': web3.eth.getTransactionCount(acct.address)})
            signed = acct.signTransaction(tx) 
            tx_id = web3.eth.sendRawTransaction(signed.rawTransaction)
            response = web3.eth.wait_for_transaction_receipt(tx_id)
            vdindex =  int(response['logs'][0]['data'],16)
            return vdindex

        else:
            provider = Web3.HTTPProvider("http://127.0.0.1:7545")
            web3 = Web3(provider)
            contract_address = '0xb44E9A279BA318bb20838Fff7c8ee75e9DaD504E' #change
            with open('/home/linqi/zk_lsm/prover/Verifier.json', 'r') as f:
                contract_abi = json.load(f)['abi']
            contract = web3.eth.contract(address=contract_address, abi=contract_abi)
            acct = web3.eth.account.from_key("55d00b01cb19721d2ea129f04329a5d54d7f2257f51e8a4cbe23fea267484645")

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
            
            estimatedGas = contract.functions.verifyTx(aint,bint,cint,inputsint).estimateGas()
            tx = contract.functions.verifyTx(aint,bint,cint,inputsint).buildTransaction({
                "gasPrice": web3.eth.gas_price,
                'from': acct.address,
                'nonce': web3.eth.getTransactionCount(acct.address)})
            signed = acct.signTransaction(tx) 
            tx_id = web3.eth.sendRawTransaction(signed.rawTransaction)
           

            
            return tx_id

class TestProver:
    def setUp(self):
        txo1 = Field(1) * G + Field(11) * H
        txo2 = Field(2) * G + Field(12) * H
        
        self.mmr = PedersenMMR()

        self.mmr.append(txo1)
        self.mmr.append(txo2)

    def test_zk_roll_up_proof(self):
        current_root = self.mmr.root
        current_width = self.mmr.width
        current_peaks = self.mmr.peaks
        ## catch existed mmr peaks
        mmr = PedersenMMR.from_peaks(16, self.mmr.peaks)
        items_to_update = [
            Field(3) * G + Field(13) * H,
            Field(4) * G + Field(14) * H
        ]
        for item in items_to_update:
            mmr.append(item)
        new_root = mmr.root
        print(new_root)
        proof = None
        prove = prover()
        proof = prove.generate_proof(current_root, current_width, current_peaks, items_to_update, new_root)
        tx_id = prove.send_proof(1, proof)
        print(tx_id)
    def quick_test(self):
        with open('/home/linqi/zk_lsm/prover/proof.json', 'r') as f:
                proof = json.load(f)
        prove = prover()
        tx_id = prove.send_proof(0, proof)
        print(tx_id)

# def quick_test2():
#     with open('/home/linqi/zk_lsm/prover/proof.json', 'r') as f:
#             proof = json.load(f)
#     cmd = 'node -e "require(\\"%s\\").init(%s,%s)"' % ('./norm', 3, 5)
#     pipeline = os.popen(cmd)


#     result = pipeline.read()

#     print(':', result)


if __name__ == '__main__':
    # test = TestProver()
    # test.setUp()
    # test.test_zk_roll_up_proof()
    #test.quick_test()
    #quick_test2()
    test = prover()
    with open('/home/linqi/zk_lsm/prover/proof.json', 'r') as f:
            proof = json.load(f)
    prove = prover()
    tx_id = prove.send_proof(0, proof)
    print(tx_id)


    test.generate_proof('1',0,['0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0','0'],
    ['1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1', '1','1'],
    ['6240310263868600000907002249301600989512613534715775264104212946757955124544','3202682209309940320443565404587573493352466174713382045702345523299807201212'],
    ['13025130865061947581079042596343039487863282540950421438416374788683558862471','2287786568849528957623775936879296979146458038468859105955636463613947059280'],
    '13338087817907784051592757810517230450287288234474268901909769169482516545919'
)

