#!/usr/bin/env python3
"""Domyka dwie ostatnie grupy +5V po automatycznym routingu 0,5 mm.

Uzycie:
    python3 route_5v_manual.py WEJSCIE.kicad_pcb WYJSCIE.kicad_pcb

Trasa 0,30 mm przez polnocny/wschodni obwod jest tylko redundantnym
polaczeniem dwoch pinow +5V BlackPilla (modul laczy je wewnetrznie). Galaz
0,40 mm do GPS/RX przenosi wylacznie prad tych dwoch zlacz. Pelny prad bucka
pozostaje na jawnych odcinkach 0,8/1,0 mm z route_power_seed.py.
"""

import sys

import pcbnew


MM = pcbnew.FromMM


def v(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def segment(board, start, end, width, layer):
    item = pcbnew.PCB_TRACK(board)
    item.SetNetCode(board.FindNet("+5V").GetNetCode())
    item.SetLayer(board.GetLayerID(layer))
    item.SetStart(v(*start))
    item.SetEnd(v(*end))
    item.SetWidth(MM(width))
    board.Add(item)


def via(board, at):
    item = pcbnew.PCB_VIA(board)
    item.SetNetCode(board.FindNet("+5V").GetNetCode())
    item.SetPosition(v(*at))
    item.SetWidth(MM(0.60))
    item.SetDrill(MM(0.30))
    item.SetViaType(pcbnew.VIATYPE_THROUGH)
    item.SetLayerPair(board.GetLayerID("F.Cu"), board.GetLayerID("B.Cu"))
    board.Add(item)


def chain(board, points, width, layer):
    for start, end in zip(points, points[1:]):
        segment(board, start, end, width, layer)


def main():
    if len(sys.argv) != 3:
        print(f"uzycie: {sys.argv[0]} WEJSCIE.kicad_pcb WYJSCIE.kicad_pcb")
        return 2
    src, dst = sys.argv[1:]
    board = pcbnew.LoadBoard(src)
    if board is None:
        print(f"nie mozna wczytac: {src}")
        return 2

    # Zachodnia grupa +5V ma juz via w (137,95;80,60). Prowadzimy B.Cu pod
    # elementami polnocnymi, potem obwodem wschodnim do escape A1.38.
    chain(board, [
        (137.950, 80.600),
        (137.950, 77.900),
        (174.200, 77.900),
        (176.000, 80.200),
        (176.000, 110.500),
        (168.000, 110.500),
        (167.350, 107.150),
    ], 0.30, "B.Cu")

    # SMD GPS wychodzi krotkim neckdownem F.Cu do via, a dalej 0,40 mm B.Cu
    # omija prawy otwor A2 i H3 od poludnia.
    segment(board, (144.150, 117.200), (143.500, 116.550), 0.40, "F.Cu")
    via(board, (143.500, 116.550))
    chain(board, [
        (143.500, 116.550),
        (143.500, 117.650),
        (158.500, 117.650),
        (161.200, 119.250),
        (168.000, 119.250),
        (168.000, 110.500),
    ], 0.40, "B.Cu")

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()
    pcbnew.SaveBoard(dst, board)
    print(f"zapisano {dst}: domkniecie +5V BlackPill i GPS/RX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
