import math
import svgwrite
from kicad import KiCad
from color import *

class SVG:
    def __init__(self):
        self.kicad = KiCad()
        self.svgs = []
        self.max = self.kicad.layer + 1

        x0 = self.kicad.pcbdata.box.minx
        y0 = self.kicad.pcbdata.box.miny
        dx = self.kicad.pcbdata.box.maxx - x0
        dy = self.kicad.pcbdata.box.maxy - y0
        view = str(x0) + " ," + str(y0) + " ," + str(dx) + " ," + str(dy)
        print(view)

        #print("layer")
        for n in range(1, self.max):
            file = "L"+str(n)+".svg"
            dwg = svgwrite.Drawing(filename=file, size=(2000, 2000), viewBox=view)
            self.svgs.append(dwg)

        #self.dwg = svgwrite.Drawing(filename="test.svg", size=(500, 500), viewBox="107.2873, 7.23873, 50.1, 122.4127")
        
    def draw(self):
        
        for pad in self.kicad.pcbdata.pads:
            if pad.type == "smd" and pad.shape == "circle":
                x = pad.pos.x
                y = pad.pos.y
                r = pad.size.x/2
                color = ''
                check = -1
                for i, v in enumerate(self.kicad.netclasses):
                    if pad.net in v.netnames:
                        check = i
                        color = Colors[i]
                for j, v in enumerate(self.kicad.layers):
                    if pad.layer == v:
                        if check >= 0:
                            self.svgs[j].add(self.svgs[j].circle((x, y), r, stroke_width=0, stroke=color, fill=color))
                        else:
                            self.svgs[j].add(self.svgs[j].circle((x, y), r, stroke_width=0, stroke="black", fill="black"))

            if pad.type == "smd" and pad.shape == "rect":
                x = pad.size.x
                y = pad.size.y
                x0 = pad.pos.x - x/2
                y0 = pad.pos.y - y/2
                color = ''
                check = -1
                for i, v in enumerate(self.kicad.netclasses):
                    if pad.net in v.netnames:
                        check = i
                        color = Colors[i]
                for j, v in enumerate(self.kicad.layers):
                    if pad.layer == v:
                        if check >= 0:
                            self.svgs[j].add(self.svgs[j].rect((x0, y0), (x, y), stroke_width=0, stroke=color, fill=color))
                        else:
                            self.svgs[j].add(self.svgs[j].rect((x0, y0), (x, y), stroke_width=0, stroke="black", fill="black"))
            if pad.type == "smd" and pad.shape == "oval":
                if pad.angle == 0:
                    width = pad.size.y
                    sx = pad.pos.x + pad.size.x/2 - width/2
                    ex = pad.pos.x - pad.size.x/2 + width/2
                    sy = pad.pos.y
                    ey = pad.pos.y
                    for j, v in enumerate(self.kicad.layers):
                        if pad.layer == v:
                            self.svgs[j].add(self.svgs[j].line((sx, sy), (ex, ey), stroke="black", stroke_width=width, stroke_linecap="round"))
                else:
                    width = pad.size.y
                    sx = pad.pos.x
                    ex = pad.pos.x
                    sy = pad.pos.y + pad.size.x/2 - width/2
                    ey = pad.pos.y - pad.size.x/2 + width/2
                    for j, v in enumerate(self.kicad.layers):
                        if pad.layer == v:
                            self.svgs[j].add(self.svgs[j].line((sx, sy), (ex, ey), stroke="black", stroke_width=width, stroke_linecap="round"))

        for track in self.kicad.pcbdata.tracks:
            if track.type == "line":
                sx = track.start.x
                sy = track.start.y
                ex = track.end.x
                ey = track.end.y
                width = track.width
                color = ''
                check = -1
                for i, v in enumerate(self.kicad.netclasses):
                    if track.net in v.netnames:
                        check = i
                        color = Colors[i]
                for j, a in enumerate(self.kicad.layers):
                        
                        if track.layer == a:
                            if check >= 0:
                                self.svgs[j].add(self.svgs[j].line((sx, sy), (ex, ey), stroke=color, stroke_width=width, stroke_linecap="round"))
                            else:
                                self.svgs[j].add(self.svgs[j].line((sx, sy), (ex, ey), stroke="black", stroke_width=width, stroke_linecap="round"))
                    
            elif track.type == "arc":
                center = track.center
                radius = track.radius
                start = track.startangle
                end = track.endangle
                width = track.width
                color = ''
                check = -1
                for i, v in enumerate(self.kicad.netclasses):
                    if track.net in v.netnames:
                        check = i
                        color = Colors[i]
                for j, v in enumerate(self.kicad.layers):
                    if track.layer == v:
                        if check >= 0:
                            self.arc(center, radius, 0, start, end, width, j, color)
                        else:
                            self.arc(center, radius, 0, start, end, width, j)
        
        for track in self.kicad.pcbdata.tracks:
            if track.type == "via":
                cx = track.start.x
                cy = track.start.y
                color = ''
                check = -1
                for i, v in enumerate(self.kicad.netclasses):
                    if track.net in v.netnames:
                        check = i
                        color = Colors[i]
                for j, v in enumerate(self.kicad.layers):
                    if check >= 0:
                        #self.svgs[j].add(self.svgs[j].line((sx, sy), (ex, ey), stroke=color, stroke_width=width, stroke_linecap="round"))
                        self.svgs[j].add(self.svgs[j].circle((cx, cy), track.width/2, stroke_width=0, stroke=color, fill=color))
                    else:
                        self.svgs[j].add(self.svgs[j].circle((cx, cy), track.width/2, stroke_width=0, stroke="black", fill="black"))
                    self.svgs[j].add(self.svgs[j].circle((cx, cy), track.drill/2, stroke_width=0, stroke="white", fill="white"))
            
        for n in range(0, self.kicad.layer):
            #file = "L"+str(n)+".svg"
            self.svgs[n].save()
        #self.svgs[j].save()


    def arc(self, position, radius, rotation, start, end, width, index, color="black"):
        x0 = position.x + radius
        y0 = position.y
        x1 = position.x + radius
        y1 = position.y
        rad_start = math.radians(start % 360)
        rad_end = math.radians(end % 360)
        x0 -= (1 - math.cos(rad_start)) * radius
        y0 += math.sin(rad_start) * radius
        x1 -= (1 - math.cos(rad_end)) * radius
        y1 += math.sin(rad_end) * radius

        args = {'x0': x0,
                'y0': y0,
                'x1': x1,
                'y1': y1,
                'xradius': radius,
                'yradius': radius,
                'ellipseRotation': 0,
                'swap': 1 if end > start else 0,
                'large': 1 if abs(start - end) > 180 else 0,
        }

        # 'a/A' params: (rx,ry x-axis-rotation large-arc-flag,sweep-flag x,y)+ (case dictates relative/absolute pos)
        path = """M %(x0)f,%(y0)f
                A %(xradius)f,%(yradius)f %(ellipseRotation)f %(large)d,%(swap)d %(x1)f,%(y1)f
        """ % args
        arc = self.svgs[index].path(d=path, fill="none", stroke=color, stroke_width=width)
        p0 = (position.x, position.y)
        arc.rotate(rotation, p0)
        self.svgs[index].add(arc)

        # start/end points, just for reference
        #svg.add(svg.circle((x0, y0), r=2, stroke="green", fill="green"))
        #svg.add(svg.circle((x1, y1), r=2, stroke="red", fill="red"))


    # test it
    """
    svg = svgwrite.Drawing(filename="test.svg", size=(300, 300), viewBox="0, 0, 300, 300")
    p0 = (150, 150)

    svg.add(svg.rect((100, 100), (100, 100), stroke="orange", stroke_width=1, fill="none"))
    svg.add(svg.circle(p0, r=2, stroke="orange", fill="orange"))
    arc(svg, p0, 100, 0, 0, 210, color="black")
    svg.save()
    """