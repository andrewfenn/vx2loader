#!/usr/bin/python

import array
import struct
import gzip
import os
import sys
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename",
                  help="attempt to load file", metavar="FILE")
(options, args) = parser.parse_args()


def enum(**enums):
    return type('Enum', (), enums)

class switch(object):
    value = None
    def __new__(class_, value):
        class_.value = value
        return True

def case(*args):
    return any((arg == switch.value for arg in args))


ChunkTypeEnum = enum(
    StorageMetaData      = 1,
    MaterialIndexTable   = 2,
    MacroContentNodes    = 3,
    MacroMaterialNodes   = 4,
    ContentLeafProvider  = 5,
    ContentLeafOctree    = 6,
    MaterialLeafProvider = 7,
    MaterialLeafOctree   = 8,
    DataProvider         = 9,
    EndOfFile            = 65535,
)

def Read7BitInt(vx2_file):
    num3 = 255
    num = 0;
    num2 = 0;
    while ((num3 & 0x80) != 0):
        if num2 == 0x23:
            return -1;

        num3 = struct.unpack("<B", vx2_file.read(1))[0]
        num |= (num3 & 0x7f) << num2;
        num2 += 7;

    return int(num)

def ReadVector3(vx2_file):
    x       = int(struct.unpack("<i", vx2_file.read(4))[0])
    y       = int(struct.unpack("<i", vx2_file.read(4))[0])
    z       = int(struct.unpack("<i", vx2_file.read(4))[0])
    return (x,y,z)

def ReadString(vx2_file):
    length = Read7BitInt(vx2_file)
    ret_string = ""
    for i in range(length):
        ret_string += struct.unpack_from("<c", vx2_file.read(1))[0]
    return ret_string

def ReadChunkInfo(vx2_file):
    chunktype = Read7BitInt(vx2_file)
    chunkversion = Read7BitInt(vx2_file)
    chunksize = Read7BitInt(vx2_file)
    return [chunktype, chunkversion, chunksize]

def ReadStorageMetaData(vx2_file):
    print "--------------------------"
    print "Meta Data"
    leafLodCount = int(struct.unpack("<i", vx2_file.read(4))[0])
    size_x       = int(struct.unpack("<i", vx2_file.read(4))[0])
    size_y       = int(struct.unpack("<i", vx2_file.read(4))[0])
    size_z       = int(struct.unpack("<i", vx2_file.read(4))[0])
    defaultMaterial = Read7BitInt(vx2_file)
    print(leafLodCount, size_x, size_y, size_z, defaultMaterial)

def ReadMaterialTable(vx2_file):
    print "--------------------------"
    print "Material Data"
    materialCount = int(struct.unpack("<i", vx2_file.read(4))[0])
    for i in range(materialCount):
        index = Read7BitInt(vx2_file)
        name  = ReadString(vx2_file)
        print(index, name)

def ReadDataProvider(vx2_file, chunk):
    print "--------------------------"
    print "Data Provider"

    if chunk[0] == 1:
        print "terrain data, need to figure this out"
    else:
        print "something else?, ignored"

    data = ''
    for j in range(chunk[2]):
        data += str(struct.unpack("<B", vx2_file.read(1))[0])

    print "Data: "+str(data)



def ReadOctreeNodes(vx2_file, chunk):
    print "--------------------------"
    print "Read Octree Nodes"

    version = chunk[1]
    print "Version: "+str(version)

    if version == 1:
        # VERSION_OCTREE_NODES_32BIT_KEY
        print "VERSION_OCTREE_NODES_32BIT_KEY"
    else:
        # CURRENT_VERSION_OCTREE_NODES
        print "CURRENT_VERSION_OCTREE_NODES"

    nodes_count = int(chunk[2]/16)
    print "Node Count: "+str(nodes_count)
    print "size: "+str(chunk[2])

    for i in range(nodes_count):
        node_key = long(struct.unpack("<Q", vx2_file.read(8))[0])
        node_mask = struct.unpack_from("<B", vx2_file.read(1))[0]

        node_data = ''
        for j in range(8):
            node_data += str(struct.unpack("<B", vx2_file.read(1))[0])

        print " --- "
        print "    |"
        print " Node Key: "+str(node_key)
        print " Node Mask:"+str(node_mask)
        print " Node Data:"+str(node_data)


def ReadProviderLeaf(vx2_file, chunk):
    print "--------------------------"
    print "Read Provider Leaf"
    VERSION_OCTREE_LEAVES_32BIT_KEY = 2
    CURRENT_VERSION_OCTREE_LEAVES = 3;

    version = chunk[1]
    if (version <= VERSION_OCTREE_LEAVES_32BIT_KEY):
        key = int(struct.unpack("<i", vx2_file.read(4))[0])
        print "Unimplemented"
    else:
        key = long(struct.unpack("<Q", vx2_file.read(8))[0])
        vx2_file.read(chunk[2]-8)

    print "Key: "+str(key)

def ReadOctreeLeaf(vx2_file, chunk):
    print "--------------------------"
    print "Read Octree Leaf"

    VERSION_OCTREE_LEAVES_32BIT_KEY = 2
    CURRENT_VERSION_OCTREE_LEAVES = 3;

    version = chunk[1]
    print "Version: "+str(version)

    if (version <= VERSION_OCTREE_LEAVES_32BIT_KEY):
        key = int(struct.unpack("<i", vx2_file.read(4))[0])
    else:
        key = long(struct.unpack("<Q", vx2_file.read(8))[0])

    tree_height = int(struct.unpack("<i", vx2_file.read(4))[0])
    tree_width  = 1 << tree_height
    default_content = str(struct.unpack("<B", vx2_file.read(1))[0])

    chunk[2] -= 9
    nodes_count = int(chunk[2] / 13)
    print "Key: "+str(key)
    print "Tree Height: "+str(tree_height)
    print "Tree Width: "+str(tree_width)
    print "Default Content: "+str(default_content)
    print "Node Count: "+str(nodes_count)
    for i in range(nodes_count):
        node_key = int(struct.unpack("<I", vx2_file.read(4))[0])
        node_mask = struct.unpack_from("<B", vx2_file.read(1))[0]
        node_data=''
        for j in range(8):
            node_data += str(struct.unpack("<B", vx2_file.read(1))[0])
        print " --- "
        print "    |"
        print " Node Key: "+str(node_key)
        print " Node Mask:"+str(node_mask)
        print " Node Data:"+str(node_data)

def LoadInternal(vx2_file, file_size):

    while True:

        chunk = ReadChunkInfo(vx2_file)

        chunktype    = chunk[0]
        chunkversion = chunk[1]
        chunksize    = chunk[2]

        while switch (chunktype):
            if case (ChunkTypeEnum.StorageMetaData):
                ReadStorageMetaData(vx2_file)
                break
            if case (ChunkTypeEnum.MaterialIndexTable):
                ReadMaterialTable(vx2_file)
                break

            if case (ChunkTypeEnum.MacroContentNodes):
                ReadOctreeNodes(vx2_file, chunk)
                break

            if case (ChunkTypeEnum.MacroMaterialNodes):
                ReadOctreeNodes(vx2_file, chunk)
                break

            if case (ChunkTypeEnum.ContentLeafProvider):
                ReadProviderLeaf(vx2_file, chunk)
                break

            if case (ChunkTypeEnum.DataProvider):
                ReadDataProvider(vx2_file, chunk)
                break

            if case (ChunkTypeEnum.MaterialLeafProvider):
                ReadProviderLeaf(vx2_file, chunk)
                break

            if case (ChunkTypeEnum.ContentLeafOctree):
                ReadOctreeLeaf(vx2_file, chunk)
                break

            if case (ChunkTypeEnum.MaterialLeafOctree):
                ReadOctreeLeaf(vx2_file, chunk)
                break

            if case (ChunkTypeEnum.EndOfFile):
                return
                break


with gzip.open(options.filename, 'rb') as vx2_file:

    file_size = int(vx2_file.seek(-1, 0))-1
    vx2_file.seek(0)

    storageType = ReadString(vx2_file)
    version     = Read7BitInt(vx2_file)

    print "file size: "+str(file_size)
    LoadInternal(vx2_file, file_size)


sys.exit(0)

