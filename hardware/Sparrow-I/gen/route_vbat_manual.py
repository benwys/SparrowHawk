#!/usr/bin/env python3
"""Trasuje wejscie /VBAT po zweryfikowanym placemencie Sparrow-I.

Uzycie:
    python3 route_vbat_manual.py WEJSCIE.kicad_pcb WYJSCIE.kicad_pcb

Glowny tor ma 1,2 mm i korzysta z warstwy mieszanej In2.Cu. Po refill strefa
+3V3 musi pozostac jedna skladowa. Rownolegle przejscie przy zrodle zmniejsza
opor vias; odnogi dzielnika i TP sa niskopradowe.
"""

import os
import sys

import pcbnew


DEFAULT_SKILL_SCRIPTS = "/home/benio/.agents/skills/kicad-route/scripts"
SKILL_SCRIPTS = os.environ.get("KICAD_ROUTE_SCRIPTS", DEFAULT_SKILL_SCRIPTS)
if not os.path.isdir(os.path.join(SKILL_SCRIPTS, "kr")):
    raise SystemExit("ustaw KICAD_ROUTE_SCRIPTS na katalog scripts skilla kicad-route")
sys.path.insert(0, SKILL_SCRIPTS)

from kr import board as kb  # noqa: E402


MM = pcbnew.FromMM


def v(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def segment(board, start, end, width, layer):
    item = pcbnew.PCB_TRACK(board)
    item.SetNetCode(board.FindNet("/VBAT").GetNetCode())
    item.SetLayer(board.GetLayerID(layer))
    item.SetStart(v(*start))
    item.SetEnd(v(*end))
    item.SetWidth(MM(width))
    board.Add(item)


def via(board, at, diameter=0.80, drill=0.40):
    item = pcbnew.PCB_VIA(board)
    item.SetNetCode(board.FindNet("/VBAT").GetNetCode())
    item.SetPosition(v(*at))
    item.SetWidth(MM(diameter))
    item.SetDrill(MM(drill))
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

    before_all = kb.all_pad_partitions(board)
    before = len(kb.pad_partitions(board, "/VBAT"))
    if before != 6:
        print(f"ODRZUCONO: oczekiwano 6 grup /VBAT, jest {before}")
        return 1

    # Wejscie ESC -> TVS. Pierwszy odcinek jest neckdownem do pada 0,6 mm.
    segment(board, (151.300, 82.650), (152.200, 83.550), 0.50, "F.Cu")
    segment(board, (152.200, 83.550), (156.000, 87.250), 0.80, "F.Cu")

    # Punkt pomiarowy: krotki stub na In2 omija sygnaly F/B.
    segment(board, (137.050, 79.400), (137.050, 79.450), 0.30, "F.Cu")
    via(board, (137.050, 79.450), diameter=0.60, drill=0.30)
    chain(board, [
        (137.050, 79.450),
        (147.350, 79.450),
        (151.350, 83.450),
    ], 0.30, "In2.Cu")
    via(board, (151.350, 83.450), diameter=0.60, drill=0.30)
    segment(board, (151.350, 83.450), (151.350, 83.400), 0.30, "F.Cu")

    # TVS -> szeroki trunk In2 -> lokalne kondensatory i VIN bucka.
    segment(board, (156.000, 87.250), (158.000, 88.000), 0.80, "F.Cu")
    via(board, (158.000, 88.000))
    via(board, (157.300, 87.750))
    segment(board, (157.300, 87.750), (158.400, 88.050), 1.20, "In2.Cu")
    chain(board, [
        (158.400, 88.050),
        (171.600, 88.050),
        (175.150, 91.600),
        (175.150, 93.150),
        (174.000, 94.300),
        (168.650, 94.300),
        (167.550, 95.400),
        (167.550, 95.750),
        (161.350, 101.950),
        (154.650, 101.950),
        (154.350, 101.650),
        (153.200, 101.650),
        (150.200, 104.650),
        (136.100, 104.650),
        (135.400, 103.950),
        (135.400, 103.400),
    ], 1.20, "In2.Cu")

    # Niskopradowy tap do dzielnika VBAT.
    segment(board, (160.800, 94.850), (162.950, 97.000), 0.40, "F.Cu")
    via(board, (162.950, 97.000), diameter=0.60, drill=0.30)
    segment(board, (162.950, 97.000), (164.200, 98.250), 0.40, "In2.Cu")

    # C_IN2 wychodzi na polnoc nad padem GND C_IN1 i wpina sie do lokalnej
    # miedzi VIN przy U_BUCK1.
    chain(board, [
        (130.700, 103.050),
        (131.700, 102.050),
        (133.150, 102.050),
    ], 0.70, "B.Cu")
    via(board, (133.150, 102.050), diameter=0.80, drill=0.40)

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()
    after = len(kb.pad_partitions(board, "/VBAT", rebuild=False))
    after_all = kb.all_pad_partitions(board)
    regressions = kb.partition_regressions(before_all, after_all)
    if after != 1 or regressions:
        print(f"ODRZUCONO: /VBAT {before} -> {after}, regresje {regressions[:8]}")
        return 1

    pcbnew.SaveBoard(dst, board)
    print(f"zapisano {dst}: /VBAT {before} -> {after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
