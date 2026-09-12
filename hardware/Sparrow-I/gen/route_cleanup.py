#!/usr/bin/env python3
"""Naprawia znany, jednostronnie uzyty artefakt A* bez zmiany connectivity.

Uzycie:
    python3 route_cleanup.py WEJSCIE.kicad_pcb WYJSCIE.kicad_pcb

Router czasem laczy pad przez via, ktora na F.Cu mostkuje ostatnia szczeline,
ale zostawia ja bez miedzi B.Cu. Krotki odcinek B.Cu do tego samego pada usuwa
`via_dangling`. Skrypt odrzuca zapis przy dowolnej regresji connectivity.
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


BRIDGES = (
    (("/RSV_PA4", 154.950, 80.300), (155.800, 79.450)),
    (("/RSV_PB12", 150.750, 119.900), (151.620, 120.750)),
)
MM = pcbnew.FromMM


def rounded_position(item):
    pos = item.GetPosition()
    return round(pos.x / 1_000_000, 3), round(pos.y / 1_000_000, 3)


def same_point(a, point):
    return (round(a.x / 1_000_000, 3), round(a.y / 1_000_000, 3)) == point


def main():
    if len(sys.argv) != 3:
        print(f"uzycie: {sys.argv[0]} WEJSCIE.kicad_pcb WYJSCIE.kicad_pcb")
        return 2
    src, dst = sys.argv[1:]
    board = pcbnew.LoadBoard(src)
    if board is None:
        print(f"nie mozna wczytac: {src}")
        return 2

    before_parts = kb.all_pad_partitions(board)
    before_unrouted = kb.unrouted(board)
    actions = []
    for via_key, pad_point in BRIDGES:
        vias = [item for item in board.GetTracks()
                if isinstance(item, pcbnew.PCB_VIA)
                and (item.GetNetname(), *rounded_position(item)) == via_key]
        if not vias:
            actions.append((via_key[0], "brak via — pominieto"))
            continue
        if len(vias) != 1:
            print(f"ODRZUCONO: oczekiwano najwyzej jednej via {via_key}, "
                  f"jest {len(vias)}")
            return 1

        endpoints = {rounded_position(vias[0]), pad_point}
        bridge_exists = any(
            isinstance(item, pcbnew.PCB_TRACK)
            and not isinstance(item, pcbnew.PCB_VIA)
            and item.GetNetname() == via_key[0]
            and board.GetLayerName(item.GetLayer()) == "B.Cu"
            and endpoints == {
                tuple(round(c / 1_000_000, 3) for c in
                      (item.GetStart().x, item.GetStart().y)),
                tuple(round(c / 1_000_000, 3) for c in
                      (item.GetEnd().x, item.GetEnd().y)),
            }
            for item in board.GetTracks()
        )
        if not bridge_exists:
            bridge = pcbnew.PCB_TRACK(board)
            bridge.SetNetCode(board.FindNet(via_key[0]).GetNetCode())
            bridge.SetLayer(board.GetLayerID("B.Cu"))
            bridge.SetStart(pcbnew.VECTOR2I(MM(via_key[1]), MM(via_key[2])))
            bridge.SetEnd(pcbnew.VECTOR2I(MM(pad_point[0]), MM(pad_point[1])))
            bridge.SetWidth(MM(0.20))
            board.Add(bridge)
        actions.append((via_key[0], "byl" if bridge_exists else "dodany"))

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()
    after_parts = kb.all_pad_partitions(board)
    after_unrouted = kb.unrouted(board)
    regressions = kb.partition_regressions(before_parts, after_parts)
    if regressions or after_unrouted != before_unrouted:
        print(f"ODRZUCONO: UC {before_unrouted} -> {after_unrouted}, "
              f"regresje {regressions[:8]}")
        return 1

    pcbnew.SaveBoard(dst, board)
    print(f"zapisano {dst}: mosty {actions}; UC {after_unrouted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
