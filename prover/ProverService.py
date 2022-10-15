import proveService_pb2_grpc as psgrpc
import proveService_pb2 as ps
import grpc
import backupService_pb2_grpc as bsgrpc
import backupService_pb2 as bs
from concurrent.futures.thread import ThreadPoolExecutor
import logging
from prover import prover

class proveService(psgrpc.ProverNodeServicer):
    def __init__(self):
        self.edge_node = 0
        self.batch_size = 1000
        self.total_service_time = 0
        self.provernode = prover()
    # execute the proof tasks
    def Execute(self, request: [ps.Task], context):
        print(request)
        current_root = request.current_root
        current_width = request.current_width
        
        current_peaksx = request.current_peaksx
        current_peaksy = request.current_peaksy
        items_to_updatex = request.items_to_updatex
        items_to_updatey = request.items_to_updatey
        new_root = request.new_root
        proof = self.provernode.generate_proof(current_root, current_width, current_peaksx, current_peaksy, items_to_updatex, items_to_updatey, new_root)
        vdindex = self.provernode.send_proof(0, proof)


        options = [('grpc.max_receive_message_length', 1024 * 1024 * 1024)]

        with grpc.insecure_channel('localhost:50053', options=options) as channel:
            stub = bsgrpc.BackupNodeStub(channel)
            Task = bs.ValidIndex(Index = vdindex)
            response1 = stub.Insertlog(Task)
            print(response1.Index)
            print('finished insert log')
        response = ps.ProvedResponse(Status = 'inserted log')
        
        return response
    
def serve():
    options = [('grpc.max_receive_message_length', 1024 * 1024 * 1024),
            ('grpc.http2.max_ping_strikes', 0)]
    server = grpc.server(ThreadPoolExecutor(max_workers=10), options=options)
    psgrpc.add_ProverNodeServicer_to_server(
        proveService(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()