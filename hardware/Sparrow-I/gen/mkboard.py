#!/usr/bin/env python3
"""Szkielet mechaniczny Sparrow-I: obrys 54 x 46 mm R3, raster M3 30,5, 4 warstwy."""
import pcbnew, math, os

PCB = "/home/benio/Desktop/SparrowHawk/hardware/Sparrow-I/Flight Controller - carrier board.kicad_pcb"
CX, CY = 150.0, 100.0          # srodek plytki = srodek rastra srub
HX, HY = 27.0, 23.0            # polowy: 54 x 46
R = 3.0                        # promien narozy
M3 = 15.25                     # polrozstaw 30,5

def mm(v): return pcbnew.FromMM(v)
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

board = pcbnew.CreateEmptyBoard()
board.SetCopperLayerCount(4)
board.SetLayerName(pcbnew.In1_Cu, "In1.Cu")
board.SetLayerName(pcbnew.In2_Cu, "In2.Cu")
board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)   # lita masa
board.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_MIXED)   # zasilania + resztki sygnalow

def add_line(x1, y1, x2, y2):
    sh = pcbnew.PCB_SHAPE(board)
    sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
    sh.SetStart(V(x1, y1)); sh.SetEnd(V(x2, y2))
    sh.SetLayer(pcbnew.Edge_Cuts); sh.SetWidth(mm(0.1))
    board.Add(sh)

def add_arc(cx, cy, a_start, a_end):
    """luk R wokol (cx,cy), katy w stopniach, Y w dol"""
    def pt(a): return (cx + R*math.cos(math.radians(a)), cy + R*math.sin(math.radians(a)))
    sh = pcbnew.PCB_SHAPE(board)
    sh.SetShape(pcbnew.SHAPE_T_ARC)
    s = pt(a_start); m = pt((a_start + a_end)/2.0); e = pt(a_end)
    sh.SetArcGeometry(V(*s), V(*m), V(*e))
    sh.SetLayer(pcbnew.Edge_Cuts); sh.SetWidth(mm(0.1))
    board.Add(sh)

L, Rr = CX-HX, CX+HX
T, B = CY-HY, CY+HY
add_line(L+R, T, Rr-R, T)          # gora
add_line(Rr, T+R, Rr, B-R)         # prawo
add_line(Rr-R, B, L+R, B)          # dol
add_line(L, B-R, L, T+R)           # lewo
add_arc(L+R, T+R, 180, 270)        # NW
add_arc(Rr-R, T+R, 270, 360)       # NE
add_arc(Rr-R, B-R, 0, 90)          # SE
add_arc(L+R, B-R, 90, 180)         # SW

# otwory montazowe M3
MH_LIB = "/usr/share/kicad/footprints/MountingHole.pretty"
for i, (dx, dy) in enumerate([(-M3,-M3), (M3,-M3), (M3,M3), (-M3,M3)]):
    fp = pcbnew.FootprintLoad(MH_LIB, "MountingHole_3.2mm_M3")
    fp.SetPosition(V(CX+dx, CY+dy))
    fp.SetReference(f"H{i+1}")
    fp.Reference().SetVisible(False)
    board.Add(fp)

pcbnew.SaveBoard(PCB, board)

# --- weryfikacja ---
b = pcbnew.LoadBoard(PCB)
bb = b.GetBoardEdgesBoundingBox()
print("warstw miedzi:", b.GetCopperLayerCount())
print("obrys: %.3f x %.3f mm  (srodek %.2f, %.2f)" % (
    bb.GetWidth()/1e6, bb.GetHeight()/1e6,
    (bb.GetLeft()+bb.GetRight())/2e6, (bb.GetTop()+bb.GetBottom())/2e6))
hs = [f for f in b.GetFootprints()]
print("otwory:", [(f.GetReference(), round(f.GetPosition().x/1e6,2), round(f.GetPosition().y/1e6,2)) for f in hs])
seg = [d for d in b.GetDrawings() if d.GetLayer()==pcbnew.Edge_Cuts]
print("elementow Edge.Cuts:", len(seg), " typy:", sorted(set(d.GetShapeStr() for d in seg)))
