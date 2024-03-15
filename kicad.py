try:
    import pcbnew
except:
    import sys
    sys.path.insert(0,"/usr/lib/python3.8/site-packages/")
    import pcbnew
import os
import json
from pcbdata import *
from typing import List

class KiCad:
    def __init__(self):
        filename = '/home/vanson/working/kicad/onekiwi/som-imx8qxp-fbga609/som-imx8qxp-fbga609.kicad_pcb'
        self.board = pcbnew.LoadBoard(filename)
        self.netclasses:List[NetClass] = []
        box = self.parse_edges()
        self.pcbdata = PcbData(box)
        self.layer = 0
        self.layers = []
        self.get_net_classes()
        self.get_layer_stackup()
        self.parse_tracks()
        self.parse_pad()

        #print("start")
        #for x in self.pcbdata.tracks:
            #if x.layer != 31:
                #print(x.layer)
    
    @staticmethod
    def normalize(point):
        return [point.x * 1e-6, point.y * 1e-6]

    @staticmethod
    def normalize_angle(angle):
        if isinstance(angle, int) or isinstance(angle, float):
            return angle * 0.1
        else:
            return angle.AsDegrees()
    
    def get_pcb_path(self):
        file_name = self.board.GetFileName()
        path = os.path.dirname(file_name)
        return path

    def get_layer_stackup(self):
        #board = get_board()
        layer = 0
        path = self.get_pcb_path()
        job_file = os.path.join(path, "jobfile.json")
        pcbnew.GERBER_JOBFILE_WRITER(self.board).CreateJobFile(job_file)
        pcbnew.GERBER_JOBFILE_WRITER(self.board).WriteJSONJobFile(job_file)

        # Opening JSON file
        f = open(job_file)
    
        # returns JSON object as 
        # a dictionaryget layge
        data = json.load(f)
    
        # Iterating through the json
        for obj in data['MaterialStackup']:
            if obj['Type'] == 'Copper':
                self.layers.append(layer)
                layer = layer + 1
                #self.stackups.append(obj['Name'])
        
        # Closing file
        f.close()
        self.layers[layer-1] = 31
        self.layer = layer
        #print("layer: ", layer)
        #for i in range(len(self.stackups)-1):
            #self.layers.append(i)
        #self.layers.append(31)
        # pcbnew.F_Cu = 0
        # pcbnew.In1_Cu = 1
        # pcbnew.B_Cu = 31
    
    def get_net_classes(self):
        nets = self.board.GetNetClasses()
        #self.classname = [str(k) for k, v in netclasses.items()]
        for k, v in nets.items():
            self.netclasses.append(NetClass(str(k)))
        
        netnames = self.board.GetNetsByName().values()
        for net in netnames:
            for netclass in self.netclasses:
                #print(net.GetNetClassName(), " ",netclass.classname)
                if net.GetNetClassName() == netclass.classname:
                    netname = net.GetNetname()
                    if len(netname): #ignore empty netname (e.g. found in Default netclass)
                        netclass.netnames.append(netname)
        
        #for netclass in self.netclasses:
            #print(netclass.classname)
            #print(netclass.netnames)

    def get_net_names(board, netclass):
        netnames = board.GetNetsByName().values()
        nets = []
        for net in netnames:
            if net.GetNetClassName() == netclass:
                netname = net.GetNetname()
                if len(netname): #ignore empty netname (e.g. found in Default netclass)
                    nets.append(netname)
        return nets
        
    def parse_edges(self):
        edges = []
        drawings = list(self.board.GetDrawings())
        bbox = None
        for f in self.board.GetFootprints():
            for g in f.GraphicalItems():
                drawings.append(g)
        for d in drawings:
            if d.GetLayer() == pcbnew.Edge_Cuts:
                for parsed_drawing in self.parse_drawing(d):
                    edges.append(parsed_drawing)
                    if bbox is None:
                        bbox = d.GetBoundingBox()
                    else:
                        bbox.Merge(d.GetBoundingBox())
        if bbox:
            bbox.Normalize()
        box = Box(bbox.GetPosition().x * 1e-6, bbox.GetPosition().y * 1e-6, 
                  bbox.GetRight() * 1e-6, bbox.GetBottom() * 1e-6)
        return box

    def get_arc_angles(self, d):
        # type: (pcbnew.PCB_SHAPE) -> tuple
        a1 = self.normalize_angle(d.GetArcAngleStart())
        if hasattr(d, "GetAngle"):
            a2 = a1 + self.normalize_angle(d.GetAngle())
        else:
            a2 = a1 + self.normalize_angle(d.GetArcAngle())
        if a2 < a1:
            a1, a2 = a2, a1
        return round(a1, 2), round(a2, 2)
    
    def parse_drawing(self, d):
        # type: (pcbnew.BOARD_ITEM) -> list
        result = []
        s = None
        if d.GetClass() in ["DRAWSEGMENT", "MGRAPHIC", "PCB_SHAPE"]:
            s = self.parse_shape(d)
        elif d.GetClass() in ["PTEXT", "MTEXT", "FP_TEXT", "PCB_TEXT", "PCB_FIELD"]:
            s = self.parse_text(d)
        elif (d.GetClass().startswith("PCB_DIM")
              and hasattr(pcbnew, "VECTOR_SHAPEPTR")):
            result.append(self.parse_dimension(d))
            if hasattr(d, "Text"):
                s = self.parse_text(d.Text())
            else:
                s = self.parse_text(d)
        else:
            self.logger.info("Unsupported drawing class %s, skipping",
                             d.GetClass())
        if s:
            result.append(s)
        return result
    
    def parse_shape(self, d):
        # type: (pcbnew.PCB_SHAPE) -> dict or None
        shape = {
            pcbnew.S_SEGMENT: "segment",
            pcbnew.S_CIRCLE: "circle",
            pcbnew.S_ARC: "arc",
            pcbnew.S_POLYGON: "polygon",
            pcbnew.S_CURVE: "curve",
            pcbnew.S_RECT: "rect",
        }.get(d.GetShape(), "")
        if shape == "":
            self.logger.info("Unsupported shape %s, skipping", d.GetShape())
            return None
        start = self.normalize(d.GetStart())
        end = self.normalize(d.GetEnd())
        if shape == "segment":
            return {
                "type": shape,
                "start": start,
                "end": end,
                "width": d.GetWidth() * 1e-6
            }

        if shape == "rect":
            if hasattr(d, "GetRectCorners"):
                points = list(map(self.normalize, d.GetRectCorners()))
            else:
                points = [
                    start,
                    [end[0], start[1]],
                    end,
                    [start[0], end[1]]
                ]
            shape_dict = {
                "type": "polygon",
                "pos": [0, 0],
                "angle": 0,
                "polygons": [points],
                "width": d.GetWidth() * 1e-6,
                "filled": 0
            }
            if hasattr(d, "IsFilled") and d.IsFilled():
                shape_dict["filled"] = 1
            return shape_dict

        if shape == "circle":
            shape_dict = {
                "type": shape,
                "start": start,
                "radius": d.GetRadius() * 1e-6,
                "width": d.GetWidth() * 1e-6
            }
            if hasattr(d, "IsFilled") and d.IsFilled():
                shape_dict["filled"] = 1
            return shape_dict

        if shape == "arc":
            a1, a2 = self.get_arc_angles(d)
            if hasattr(d, "GetCenter"):
                start = self.normalize(d.GetCenter())
            return {
                "type": shape,
                "start": start,
                "radius": d.GetRadius() * 1e-6,
                "startangle": a1,
                "endangle": a2,
                "width": d.GetWidth() * 1e-6
            }

        if shape == "polygon":
            if hasattr(d, "GetPolyShape"):
                polygons = self.parse_poly_set(d.GetPolyShape())
            else:
                self.logger.info(
                    "Polygons not supported for KiCad 4, skipping")
                return None
            angle = 0
            if hasattr(d, 'GetParentModule'):
                parent_footprint = d.GetParentModule()
            else:
                parent_footprint = d.GetParentFootprint()
            if parent_footprint is not None:
                angle = self.normalize_angle(parent_footprint.GetOrientation())
            shape_dict = {
                "type": shape,
                "pos": start,
                "angle": angle,
                "polygons": polygons
            }
            if hasattr(d, "IsFilled") and not d.IsFilled():
                shape_dict["filled"] = 0
                shape_dict["width"] = d.GetWidth() * 1e-6
            return shape_dict
        if shape == "curve":
            if hasattr(d, "GetBezierC1"):
                c1 = self.normalize(d.GetBezierC1())
                c2 = self.normalize(d.GetBezierC2())
            else:
                c1 = self.normalize(d.GetBezControl1())
                c2 = self.normalize(d.GetBezControl2())
            return {
                "type": shape,
                "start": start,
                "cpa": c1,
                "cpb": c2,
                "end": end,
                "width": d.GetWidth() * 1e-6
            }
    
    def parse_tracks(self):
        tracks = self.board.GetTracks()
        for track in tracks:
            if track.GetLayer() in self.layers:
                #print("layer1: ", track.GetLayer())
            #if track.GetLayer() == pcbnew.F_Cu:
                if track.GetClass() in ["VIA", "PCB_VIA"]:
                    layers_set = list(track.GetLayerSet().Seq())
                    #print(layers_set)
                    start = Point(track.GetStart().x * 1e-6, track.GetStart().y * 1e-6)
                    end = Point(track.GetEnd().x * 1e-6, track.GetEnd().y * 1e-6)
                    width = track.GetWidth() * 1e-6
                    net = track.GetNetname()
                    #print("layer2: ", track.GetLayer())
                    layer = track.GetLayer()
                    #print("layer3: ", layer)
                    drill = track.GetDrillValue() * 1e-6
                    via = Track("via", start, end, Point(0,0), 0, 0, 0, drill, width, net, layer)
                    self.pcbdata.tracks.append(via)
                else:
                    if track.GetClass() in ["ARC", "PCB_ARC"]:
                        a1, a2 = self.get_arc_angles(track)
                        center = Point(track.GetCenter().x * 1e-6, track.GetCenter().y * 1e-6)
                        startangle = a1
                        endangle = a2
                        radius = track.GetRadius() * 1e-6
                        width = track.GetWidth() * 1e-6
                        net = track.GetNetname()
                        layer = track.GetLayer()
                        #print("layerx: ", layer)
                        arc = Track("arc", Point(0,0), Point(0,0), center, startangle, endangle, radius, 0, width, net, layer)
                        self.pcbdata.tracks.append(arc)
                    else:
                        start = Point(track.GetStart().x * 1e-6, track.GetStart().y * 1e-6)
                        end = Point(track.GetEnd().x * 1e-6, track.GetEnd().y * 1e-6)
                        width = track.GetWidth() * 1e-6
                        net = track.GetNetname()
                        layer = track.GetLayer()
                        #print("layery: ", layer)
                        line =Track("line", start, end, Point(0,0), 0, 0, 0, 0, width, net, layer)
                        self.pcbdata.tracks.append(line)
    
    def parse_pad(self):
        for footprint in self.board.GetFootprints():
            for pad in footprint.Pads():
                layers_set = list(pad.GetLayerSet().Seq())
                #print(layers_set)
                if pcbnew.F_Cu in layers_set:
                    layer = 0
                    ptype = "th"
                    #position = self.normalize(pad.GetPosition())
                    pos = Point(pad.GetPosition().x * 1e-6, pad.GetPosition().y * 1e-6)
                    size = Point(pad.GetSize().x * 1e-6, pad.GetSize().y * 1e-6)
                    angle = self.normalize_angle(pad.GetOrientation())
                    net = pad.GetNetname()
                    shape = "custom"
                    if pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
                        shape = "circle"
                    elif pad.GetShape() == pcbnew.PAD_SHAPE_RECT:
                        shape = "rect"
                    elif pad.GetShape() == pcbnew.PAD_SHAPE_OVAL:
                        shape = "oval"
                    if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                        ptype = "smd"
                    pad = Pad(ptype, pos, size, angle, shape, net, layer)
                    self.pcbdata.pads.append(pad)
                if pcbnew.B_Cu in layers_set:
                    layer = 31
                    ptype = "th"
                    #position = self.normalize(pad.GetPosition())
                    pos = Point(pad.GetPosition().x * 1e-6, pad.GetPosition().y * 1e-6)
                    size = Point(pad.GetSize().x * 1e-6, pad.GetSize().y * 1e-6)
                    angle = self.normalize_angle(pad.GetOrientation())
                    net = pad.GetNetname()
                    shape = "custom"
                    if pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
                        shape = "circle"
                    elif pad.GetShape() == pcbnew.PAD_SHAPE_RECT:
                        shape = "rect"
                    elif pad.GetShape() == pcbnew.PAD_SHAPE_OVAL:
                        shape = "oval"
                    if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                        ptype = "smd"
                    pad = Pad(ptype, pos, size, angle, shape, net, layer)
                    self.pcbdata.pads.append(pad)