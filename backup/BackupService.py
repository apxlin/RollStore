import backupService_pb2_grpc as bsgrpc
import backupService_pb2 as bs
import grpc
from concurrent.futures.thread import ThreadPoolExecutor
import logging
from LSMTree import LSMTree
from LSMTree import KVPair
class backupService(bsgrpc.BackupNodeServicer):
    def __init__(self):
        self.edge_node = 0
        self.batch_size = 1000
        self.total_service_time = 0
        self.backupnode = LSMTree()
        self.backupnode.createLSMTree(2,100,100,1024,12,True)
        self.backupnode.buildLSMTreeInMemoryComponents()
        self.backupnode.buildLSMTreeDiskComponents()
    # stage 1 pages
    def InsertBlock(self, request: [bs.OpBatch], context):

        self.backupnode.add_buffle(request.current_root, request.new_root, KVPair([key for key in request.key], [value for value in request.value]),request.Index)


        return bs.OpIndex(Index = self.backupnode.opindex)
    # stage 2 pages
    def Insertlog(self, request: [bs.ValidIndex], context):
        print(request)
        self.backupnode.insert_disk(request.Index)
        return bs.VdIndex(Index = self.backupnode.validindex)
    # read service
    def Search(self, request: [bs.searchKey], context):

        self.backupnode.search_buffer(request.key)
        return bs.searchResult(value = str(self.backupnode.opindex))
        
def serve():
    options = [('grpc.max_receive_message_length', 1024 * 1024 * 1024),
            ('grpc.http2.max_ping_strikes', 0)]
    server = grpc.server(ThreadPoolExecutor(max_workers=10), options=options)
    bsgrpc.add_BackupNodeServicer_to_server(
        backupService(), server)
    server.add_insecure_port('[::]:50053')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()