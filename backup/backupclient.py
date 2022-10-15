import grpc
import backupService_pb2_grpc as bsgrpc
import backupService_pb2 as bs

from mmr import PedersenMMR
from jubjub import Field
from constant import G, H
import copy
class ClientAgent:
    def __init__(self, client_id: int):
        self.stub = None
        self.id = client_id
        self.hash2_checking_interval = 3
        self.batch_size = 1  # 10000
        self.txn_key_size = 64
        self.txn_val_size = 1024
        self.mmr = PedersenMMR()

    def run(self):
        txo1 = Field(1) * G + Field(11) * H
        txo2 = Field(2) * G + Field(12) * H
        
        self.mmr = PedersenMMR()

        self.mmr.append(txo1)
        self.mmr.append(txo2)
        croot = self.mmr.root
        cwidth = self.mmr.width
        cpeaks = copy.deepcopy(self.mmr.peaks)
        peaksx = [r.x for r in cpeaks]
        peaksy = [r.y for r in cpeaks]
        peaksxstr = [str(r) for r in peaksx]
        peaksystr = [str(r) for r in peaksy]
        
        iupdate = [
            Field(3) * G + Field(13) * H,
            Field(4) * G + Field(14) * H
        ]
        for item in iupdate:
            self.mmr.append(item)
        nroot = self.mmr.root
        # NOTE(gRPC Python Team): .close() is possible on a channel and should be
        # used in circumstances in which the with statement does not fit the needs
        # of the code.
        strcroot = str(croot.n)
        
        itemsx = [r.x for r in iupdate]
        itemsy = [r.y for r in iupdate]
        itemsxstr = [str(r) for r in itemsx]
        itemsystr = [str(r) for r in itemsy]



        strnroot = str(nroot)
        # print("Running client")
        options = [('grpc.max_receive_message_length', 1024 * 1024 * 1024)]
        # with grpc.insecure_channel('10.140.83.115:50051', options=options) as channel:
        with grpc.insecure_channel('localhost:50053', options=options) as channel:
            stub = bsgrpc.BackupNodeStub(channel)

            OpBatch = bs.OpBatch(current_root = strcroot, current_width = cwidth, current_peaksx = peaksxstr, current_peaksy = peaksystr, items_to_updatex = itemsxstr, 
            items_to_updatey =itemsystr, new_root=strnroot, Index = 0, key = [5, 6], value = ['5ab8', '6ab0'])
            response = stub.InsertBlock(OpBatch)
            print(response.Index)

            ValidIndex = bs.ValidIndex(Index = 1)
            response2 = stub.Insertlog(ValidIndex)
            print(response2.Index)

if __name__ == '__main__':
    client = ClientAgent(0)
    client.run()