# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: backupService.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x13\x62\x61\x63kupService.proto\x12\rbackupService\"\x18\n\tsearchKey\x12\x0b\n\x03key\x18\x01 \x01(\x05\"\x1d\n\x0csearchResult\x12\r\n\x05value\x18\x01 \x01(\t\"\\\n\x07OpBatch\x12\x14\n\x0c\x63urrent_root\x18\x01 \x01(\t\x12\x10\n\x08new_root\x18\x02 \x01(\t\x12\r\n\x05Index\x18\x08 \x01(\x05\x12\x0b\n\x03key\x18\t \x03(\x05\x12\r\n\x05value\x18\n \x03(\t\"\x1b\n\nValidIndex\x12\r\n\x05Index\x18\x01 \x01(\x05\"\x18\n\x07OpIndex\x12\r\n\x05Index\x18\x01 \x01(\x05\"\x18\n\x07VdIndex\x12\r\n\x05Index\x18\x01 \x01(\x05\x32\xcc\x01\n\nBackupNode\x12=\n\x0bInsertBlock\x12\x16.backupService.OpBatch\x1a\x16.backupService.OpIndex\x12>\n\tInsertlog\x12\x19.backupService.ValidIndex\x1a\x16.backupService.VdIndex\x12?\n\x06Search\x12\x18.backupService.searchKey\x1a\x1b.backupService.searchResultb\x06proto3')



_SEARCHKEY = DESCRIPTOR.message_types_by_name['searchKey']
_SEARCHRESULT = DESCRIPTOR.message_types_by_name['searchResult']
_OPBATCH = DESCRIPTOR.message_types_by_name['OpBatch']
_VALIDINDEX = DESCRIPTOR.message_types_by_name['ValidIndex']
_OPINDEX = DESCRIPTOR.message_types_by_name['OpIndex']
_VDINDEX = DESCRIPTOR.message_types_by_name['VdIndex']
searchKey = _reflection.GeneratedProtocolMessageType('searchKey', (_message.Message,), {
  'DESCRIPTOR' : _SEARCHKEY,
  '__module__' : 'backupService_pb2'
  # @@protoc_insertion_point(class_scope:backupService.searchKey)
  })
_sym_db.RegisterMessage(searchKey)

searchResult = _reflection.GeneratedProtocolMessageType('searchResult', (_message.Message,), {
  'DESCRIPTOR' : _SEARCHRESULT,
  '__module__' : 'backupService_pb2'
  # @@protoc_insertion_point(class_scope:backupService.searchResult)
  })
_sym_db.RegisterMessage(searchResult)

OpBatch = _reflection.GeneratedProtocolMessageType('OpBatch', (_message.Message,), {
  'DESCRIPTOR' : _OPBATCH,
  '__module__' : 'backupService_pb2'
  # @@protoc_insertion_point(class_scope:backupService.OpBatch)
  })
_sym_db.RegisterMessage(OpBatch)

ValidIndex = _reflection.GeneratedProtocolMessageType('ValidIndex', (_message.Message,), {
  'DESCRIPTOR' : _VALIDINDEX,
  '__module__' : 'backupService_pb2'
  # @@protoc_insertion_point(class_scope:backupService.ValidIndex)
  })
_sym_db.RegisterMessage(ValidIndex)

OpIndex = _reflection.GeneratedProtocolMessageType('OpIndex', (_message.Message,), {
  'DESCRIPTOR' : _OPINDEX,
  '__module__' : 'backupService_pb2'
  # @@protoc_insertion_point(class_scope:backupService.OpIndex)
  })
_sym_db.RegisterMessage(OpIndex)

VdIndex = _reflection.GeneratedProtocolMessageType('VdIndex', (_message.Message,), {
  'DESCRIPTOR' : _VDINDEX,
  '__module__' : 'backupService_pb2'
  # @@protoc_insertion_point(class_scope:backupService.VdIndex)
  })
_sym_db.RegisterMessage(VdIndex)

_BACKUPNODE = DESCRIPTOR.services_by_name['BackupNode']
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _SEARCHKEY._serialized_start=38
  _SEARCHKEY._serialized_end=62
  _SEARCHRESULT._serialized_start=64
  _SEARCHRESULT._serialized_end=93
  _OPBATCH._serialized_start=95
  _OPBATCH._serialized_end=187
  _VALIDINDEX._serialized_start=189
  _VALIDINDEX._serialized_end=216
  _OPINDEX._serialized_start=218
  _OPINDEX._serialized_end=242
  _VDINDEX._serialized_start=244
  _VDINDEX._serialized_end=268
  _BACKUPNODE._serialized_start=271
  _BACKUPNODE._serialized_end=475
# @@protoc_insertion_point(module_scope)
