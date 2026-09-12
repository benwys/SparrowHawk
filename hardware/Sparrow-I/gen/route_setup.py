#!/usr/bin/env python3
"""Dodaje bazowe strefy routingu Sparrow-I do plytki po placemencie.

Uzycie:
    python3 route_setup.py WEJSCIE.kicad_pcb WYJSCIE.kicad_pcb

Stackup i klasy sieci sa przechowywane odpowiednio w .kicad_pcb oraz .kicad_pro.
Ten skrypt dodaje tylko dwie jawne plaszczyzny i keepout In2 pod wezlem SW.
Odmawia pracy, jesli na wejsciu sa juz jakiekolwiek strefy, aby ponowne
uruchomienie nie tworzylo duplikatow ani nie naruszalo pozniejszego routingu.
"""

import math
import sys

import pcbnew


MM = pcbnew.FromMM


def v(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def rounded_board_polygon(inset=0.50, segments=8):
    """Obrys 54x46 R3, odsuniety do srodka od Edge.Cuts."""
    centers = (
        (126.0, 80.0, 180.0, 270.0),
        (174.0, 80.0, 270.0, 360.0),
        (174.0, 120.0, 0.0, 90.0),
        (126.0, 120.0, 90.0, 180.0),
    )
    radius = 3.0 - inset
    pts = []
    for cx, cy, a0, a1 in centers:
        for i in range(segments + 1):
            a = math.radians(a0 + (a1 - a0) * i / segments)
            pts.append(v(cx + radius * math.cos(a),
                         cy + radius * math.sin(a)))
    return pts


def polygon(points):
    out = pcbnew.VECTOR_VECTOR2I()
    for point in points:
        out.append(point)
    return out


def add_plane(board, name, netname, layer_name):
    net = board.FindNet(netname)
    if net is None:
        raise RuntimeError(f"brak sieci {netname}")

    zone = pcbnew.ZONE(board)
    zone.SetZoneName(name)
    zone.SetLayer(board.GetLayerID(layer_name))
    zone.SetNetCode(net.GetNetCode())
    zone.SetAssignedPriority(10)
    zone.SetLocalClearance(MM(0.25))
    zone.SetMinThickness(MM(0.20))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    zone.SetThermalReliefGap(MM(0.30))
    zone.SetThermalReliefSpokeWidth(MM(0.40))
    zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    zone.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS)
    zone.SetBorderHatchPitch(MM(0.50))
    zone.AddPolygon(polygon(rounded_board_polygon()))
    board.Add(zone)


def add_switch_keepout(board):
    """Usuwa +3V3 In2 spod calej goracej petli SW, nie blokujac tras/vias."""
    zone = pcbnew.ZONE(board)
    zone.SetZoneName("NO_PLANE_BUCK_SW_In2")
    zone.SetLayer(board.GetLayerID("In2.Cu"))
    zone.SetIsRuleArea(True)
    zone.SetDoNotAllowZoneFills(True)
    zone.SetDoNotAllowTracks(False)
    zone.SetDoNotAllowVias(False)
    zone.SetDoNotAllowPads(False)
    zone.SetDoNotAllowFootprints(False)
    zone.AddPolygon(polygon([
        v(127.20, 94.50),
        v(133.00, 94.50),
        v(133.00, 104.70),
        v(127.20, 104.70),
    ]))
    board.Add(zone)


def main():
    if len(sys.argv) != 3:
        print(f"uzycie: {sys.argv[0]} WEJSCIE.kicad_pcb WYJSCIE.kicad_pcb")
        return 2

    src, dst = sys.argv[1:]
    board = pcbnew.LoadBoard(src)
    if board is None:
        print(f"nie mozna wczytac: {src}")
        return 2
    if board.GetAreaCount() != 0:
        print(f"ODRZUCONO: plytka ma juz {board.GetAreaCount()} stref")
        return 1

    add_plane(board, "GND_plane_In1", "GND", "In1.Cu")
    add_plane(board, "PWR_plane_In2_3V3", "+3V3", "In2.Cu")
    add_switch_keepout(board)
    pcbnew.SaveBoard(dst, board)
    print(f"zapisano {dst}: In1=GND, In2=+3V3, keepout SW")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
