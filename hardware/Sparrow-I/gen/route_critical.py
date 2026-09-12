#!/usr/bin/env python3
"""Odtwarza prewalidowane escape'y bucka i CS_IMU Sparrow-I.

Uzycie:
    python3 route_critical.py WEJSCIE.kicad_pcb WYJSCIE.kicad_pcb

Geometria zostala przetestowana atomowo na tym samym placemencie. Skrypt
odmawia pracy na plytce z istniejacymi sciezkami/vias, aby nie zamieniac sie
w niekontrolowany importer delty. Po zapisie wymagane sa osobny refill i DRC.
"""

import sys

import pcbnew


MM = pcbnew.FromMM


def v(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def netcode(board, netname):
    net = board.FindNet(netname)
    if net is None:
        raise RuntimeError(f"brak sieci {netname}")
    return net.GetNetCode()


def segment(board, netname, layer_name, start, end, width):
    item = pcbnew.PCB_TRACK(board)
    item.SetNetCode(netcode(board, netname))
    item.SetLayer(board.GetLayerID(layer_name))
    item.SetStart(v(*start))
    item.SetEnd(v(*end))
    item.SetWidth(MM(width))
    board.Add(item)


def via(board, netname, at, diameter, drill):
    item = pcbnew.PCB_VIA(board)
    item.SetNetCode(netcode(board, netname))
    item.SetPosition(v(*at))
    item.SetWidth(MM(diameter))
    item.SetDrill(MM(drill))
    item.SetViaType(pcbnew.VIATYPE_THROUGH)
    item.SetLayerPair(board.GetLayerID("F.Cu"), board.GetLayerID("B.Cu"))
    board.Add(item)


SEGMENTS = (
    # BUCK_SW: cala goraca petla na F.Cu, bez vias. Odcinki 0,45 mm sa
    # najkrotszym neckdownem wymaganym przez pady U/Cboot; trunk L-D ma 1 mm.
    ("/BUCK_SW", "F.Cu", (130.650, 97.520), (128.950, 98.000), 0.45),
    ("/BUCK_SW", "F.Cu", (132.095, 95.525), (131.350, 96.400), 0.45),
    ("/BUCK_SW", "F.Cu", (131.350, 96.400), (130.650, 97.520), 0.45),
    ("/BUCK_SW", "F.Cu", (129.600, 100.600), (129.600, 103.750), 1.00),

    # Bootstrap, rowniez F-only.
    ("/BUCK_BOOT", "F.Cu", (132.095, 100.475), (131.350, 99.600), 0.30),
    ("/BUCK_BOOT", "F.Cu", (131.350, 99.600), (130.650, 98.480), 0.30),

    # Wejscie U + lokalne 100 nF schodzi do dolnego C_IN1. C_IN2 zostaje
    # bez kikuta i zostanie wlaczone dopiero razem z pelna magistrala VBAT.
    ("/VBAT", "F.Cu", (135.670, 102.500), (135.670, 103.300), 0.40),
    ("/VBAT", "F.Cu", (133.365, 102.000), (134.800, 102.000), 0.40),
    ("/VBAT", "F.Cu", (134.800, 102.000), (135.670, 102.500), 0.40),
    ("/VBAT", "F.Cu", (133.365, 100.475), (133.365, 102.000), 0.40),
    ("/VBAT", "B.Cu", (135.670, 103.300), (135.275, 104.400), 0.50),

    # Powroty mocy do litej In1.GND.
    ("GND", "F.Cu", (131.600, 104.400), (132.300, 104.400), 0.70),
    ("GND", "F.Cu", (133.600, 103.750), (133.600, 105.250), 1.00),
    ("GND", "F.Cu", (132.300, 104.400), (133.600, 103.750), 0.70),
    ("GND", "F.Cu", (136.630, 102.500), (136.630, 103.300), 0.40),
    ("GND", "F.Cu", (127.075, 104.000), (127.100, 105.450), 0.80),
    ("GND", "B.Cu", (132.325, 104.400), (131.600, 104.400), 0.70),
    ("GND", "B.Cu", (127.325, 104.400), (127.100, 105.450), 0.70),

    # FB/SS/RT przechodza na B przy samym U, z dala od wezla SW.
    ("/BUCK_FB", "F.Cu", (135.905, 95.525), (135.905, 94.150), 0.20),
    ("/BUCK_FB", "F.Cu", (135.905, 94.150), (137.025, 94.500), 0.20),
    ("/BUCK_FB", "B.Cu", (136.510, 94.500), (137.025, 94.500), 0.20),
    ("/BUCK_FB", "B.Cu", (137.025, 94.500), (137.540, 94.500), 0.20),
    ("/BUCK_SS", "F.Cu", (134.635, 95.525), (134.635, 94.100), 0.20),
    ("/BUCK_SS", "B.Cu", (132.980, 94.500), (134.635, 94.100), 0.20),
    ("/BUCK_RT", "F.Cu", (135.905, 100.475), (137.000, 100.475), 0.20),
    ("/BUCK_RT", "B.Cu", (137.000, 100.475), (136.110, 101.700), 0.20),

    # PB10/CS_IMU: sprawdzony dolny detour przez jedyny wolny gate rzedu A.
    ("/CS_IMU", "B.Cu", (141.510, 91.100), (141.510, 94.200), 0.20),
    ("/CS_IMU", "B.Cu", (132.615, 92.380), (132.615, 91.100), 0.20),
    ("/CS_IMU", "B.Cu", (132.615, 91.100), (141.510, 91.100), 0.20),
    ("/CS_IMU", "B.Cu", (141.510, 94.200), (144.920, 97.600), 0.20),
    ("/CS_IMU", "B.Cu", (144.920, 97.600), (144.920, 100.000), 0.20),
)


VIAS = (
    ("/VBAT", (135.670, 103.300), 0.60, 0.30),
    ("GND", (136.630, 103.300), 0.60, 0.30),
    ("GND", (131.600, 104.400), 0.80, 0.40),
    ("GND", (133.600, 105.250), 0.80, 0.40),
    ("GND", (127.100, 105.450), 0.80, 0.40),
    ("/BUCK_FB", (137.025, 94.500), 0.60, 0.30),
    ("/BUCK_SS", (134.635, 94.100), 0.60, 0.30),
    ("/BUCK_RT", (137.000, 100.475), 0.60, 0.30),
)


EXPECTED_POSITIONS = {
    "A1": (150.00, 100.00),
    "A2": (150.00, 106.35),
    "U_BUCK1": (134.00, 98.00),
    "L_BUCK1": (126.70, 98.00),
    "D_BUCK1": (131.60, 103.75),
}


def main():
    if len(sys.argv) != 3:
        print(f"uzycie: {sys.argv[0]} WEJSCIE.kicad_pcb WYJSCIE.kicad_pcb")
        return 2

    src, dst = sys.argv[1:]
    board = pcbnew.LoadBoard(src)
    if board is None:
        print(f"nie mozna wczytac: {src}")
        return 2
    if len(list(board.GetTracks())) != 0:
        print("ODRZUCONO: plytka ma juz sciezki lub vias")
        return 1
    if board.GetAreaCount() != 3:
        print(f"ODRZUCONO: oczekiwano 3 stref, jest {board.GetAreaCount()}")
        return 1

    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for ref, expected in EXPECTED_POSITIONS.items():
        fp = footprints.get(ref)
        if fp is None:
            print(f"ODRZUCONO: brak {ref}")
            return 1
        actual = (pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y))
        if any(abs(a - e) > 0.001 for a, e in zip(actual, expected)):
            print(f"ODRZUCONO: {ref} ma {actual}, oczekiwano {expected}")
            return 1

    for args in SEGMENTS:
        segment(board, *args)
    for args in VIAS:
        via(board, *args)

    pcbnew.SaveBoard(dst, board)
    print(f"zapisano {dst}: {len(SEGMENTS)} segmentow, {len(VIAS)} vias")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
