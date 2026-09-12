#!/usr/bin/env python3
"""Dodaje szerokie, jawne odcinki wyjscia bucka przed routingiem +5V.

Uzycie:
    python3 route_power_seed.py WEJSCIE.kicad_pcb WYJSCIE.kicad_pcb

Reszta +5V i magistrala VBAT sa trasowane w kolejnych transakcjach. Ten etap
ma zagwarantowac, ze L->Cout nie zostanie zastapione domyslna sciezka 0,5 mm.
"""

import sys

import pcbnew


MM = pcbnew.FromMM


def v(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def segment(board, netname, start, end, width, layer="F.Cu"):
    net = board.FindNet(netname)
    if net is None:
        raise RuntimeError(f"brak sieci {netname}")
    item = pcbnew.PCB_TRACK(board)
    item.SetNetCode(net.GetNetCode())
    item.SetLayer(board.GetLayerID(layer))
    item.SetStart(v(*start))
    item.SetEnd(v(*end))
    item.SetWidth(MM(width))
    board.Add(item)


def main():
    if len(sys.argv) != 3:
        print(f"uzycie: {sys.argv[0]} WEJSCIE.kicad_pcb WYJSCIE.kicad_pcb")
        return 2
    src, dst = sys.argv[1:]
    board = pcbnew.LoadBoard(src)
    if board is None:
        print(f"nie mozna wczytac: {src}")
        return 2

    # L -> C_OUT: odcinek przenoszacy pelny prad wyjscia przetwornicy.
    segment(board, "+5V", (124.450, 98.000), (124.125, 104.000), 1.00)
    # L -> A1.1, nastepnie lokalny bulk: szeroko do pinu zasilania modulu.
    segment(board, "+5V", (124.450, 98.000), (124.995, 92.380), 0.80)
    segment(board, "+5V", (124.995, 92.380), (125.500, 88.200), 0.50)

    pcbnew.SaveBoard(dst, board)
    print(f"zapisano {dst}: 3 jawne odcinki +5V")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
