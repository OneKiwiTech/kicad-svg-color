from typing import List

class Box:
    def __init__(self, minx, miny, maxx, maxy):
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Track:
    def __init__(self, type, start, end, center, startangle, endangle, radius, drill, width, net, layer):
        self.type = type
        self.start:Point = start
        self.end:Point = end
        self.center:Point = center
        self.startangle = startangle
        self.endangle = endangle
        self.radius = radius
        self.drill = drill
        self.width = width
        self.net = net
        self.layer = layer

class Pad:
    def __init__(self, type, pos, size, angle, shape, net, layer):
        self.type = type
        self.pos:Point = pos
        self.size:Point = size
        self.angle = angle
        self.shape = shape
        self.net = net
        self.layer = layer

class PcbData:
    def __init__(self, box):
        self.box:Box = box
        self.tracks:List[Track] = []
        self.pads:List[Pad] = []

class NetClass:
    def __init__(self, name):
        self.classname = name
        self.netnames = []
