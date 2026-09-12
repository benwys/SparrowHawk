#!/usr/bin/env python3
"""Deterministyczny placement Sparrow-I wedlug zatwierdzonego floorplanu.

Uzycie:
    python3 place.py ../"Flight Controller - carrier board.kicad_pcb" /tmp/placed.kicad_pcb

Skrypt celowo wymaga H1-H4 w PCB. Najpierw trzeba wykonac F8 po regeneracji
schematu; dzieki temu otwory maja powiazanie ze schematem i nie znikna przy
kolejnej synchronizacji.

Wspolrzedne strony: srodek rastra = (150, 100), +X na wschod (SWD
BlackPilla), +Y na poludnie (rzad B). Pelne obrysy uniesionych modulow sa na
Fab, a ich CrtYd opisuje elementy zajmujace poziom powierzchni carrier-a.
"""

import sys
import pcbnew


MM = pcbnew.FromMM


def v(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


# ref: (x, y, obrot, strona)
PLACEMENT = {
    # Mechanika — srodek plytki i rastra srub = (150, 100).
    "H1": (134.75, 84.75, 0, "F"),
    "H2": (165.25, 84.75, 0, "F"),
    "H3": (165.25, 115.25, 0, "F"),
    "H4": (134.75, 115.25, 0, "F"),
    "A1": (150.00, 100.00, 0, "F"),

    # Spod. A2 po flip+180: listwa Y=100, otwory M2,5 Y=112,70.
    "A2": (150.00, 106.35, 180, "B"),
    # A3: korpus nominalny X +/-7,5; Y=78,5..90,0; listwa ok. Y=88.
    # Przesuniecie 3 mm na zachod usuwa kolizje laminatu z J_AUX_A1.
    "A3": (146.10, 84.25, 0, "B"),

    # Pas polnocny. JST ESC otwiera sie ku krawedzi polnocnej.
    "J_ESC1": (147.80, 80.65, 180, "F"),
    # Rzad rezerwy cofniety od luku R3; jego pierwszy PTH nadal omija A3.
    "J_AUX_A1": (155.80, 79.45, 90, "F"),
    # Taka sama kolejnosc L->R jak na J_ESC1 po obrocie 180: M4,M3,M2,M1.
    # Pierwszy TP jest lekko odsuniety od luku R3.
    "TP_M4": (125.80, 79.10, 0, "F"),
    "TP_M3": (128.70, 79.10, 0, "F"),
    "TP_M2": (131.60, 79.10, 0, "F"),
    "TP_M1": (134.50, 79.10, 0, "F"),
    "TP_VBAT1": (137.20, 78.70, 0, "F"),
    "TP_5V1": (140.10, 78.70, 0, "F"),
    "TP_3V3_1": (125.60, 83.20, 0, "F"),
    "TP_GND1": (128.50, 83.20, 0, "F"),
    "TP_GND2": (140.10, 83.20, 0, "F"),

    # Niskie elementy w kanale nad rzedem A.
    "C_5V_BULK1": (125.50, 87.25, 90, "F"),
    "C_3V3_BULK1": (128.00, 87.25, 90, "F"),
    "C_3V3_1": (130.00, 87.25, 90, "F"),
    "D_TVS1": (158.00, 87.25, 0, "F"),

    # Buck w zachodnim kanale miedzy rzedami. Kolejnosc source/load:
    # bulk/100 nF -> U -> SW/diode -> L -> C_OUT. A2 zaczyna sie przy X=139,84,
    # dlatego cala petla mocy zostaje na zachod od jego listwy PTH.
    "L_BUCK1": (126.70, 98.00, 0, "F"),
    "U_BUCK1": (134.00, 98.00, 90, "F"),
    "C_BUCK_IN3": (136.15, 102.50, 0, "F"),
    "C_BUCK_BOOT1": (130.65, 98.00, 90, "F"),
    "C_BUCK_OUT1": (125.60, 104.00, 0, "F"),
    "D_BUCK1": (131.60, 103.75, 0, "F"),

    # Bulk wejscia oraz petle sterujace na spodzie zachodniego kanalu.
    # BUCK_SW pozostaje w calosci na F.Cu; przejscia warstw dotycza VBAT/GND
    # i wolnych petli FB/SS/RT.
    "C_BUCK_IN1": (133.80, 104.40, 180, "B"),
    "C_BUCK_IN2": (128.80, 104.40, 180, "B"),
    "R_BUCK_RT1": (135.60, 101.70, 180, "B"),
    "R_BUCK_FB1": (136.00, 94.50, 0, "B"),
    "R_BUCK_FB2": (138.05, 94.50, 0, "B"),
    "C_BUCK_SS1": (132.50, 94.50, 180, "B"),

    # Sciagacze silnikow przy odpowiadajacych im pinach A1.
    # Chirurgiczna korekta po escape-tescie bucka: oba sciagacze nadal leza
    # przy pinach M4/M3, ale nie blokuja via sprzezenia zwrotnego na X=137,025.
    "R_PD_M4": (139.60, 95.15, 270, "F"),
    "R_PD_M3": (141.70, 95.15, 270, "F"),
    "R_PD_M1": (152.935, 104.85, 90, "F"),
    "R_PD_M2": (155.475, 104.85, 90, "F"),

    # Wejscia analogowe na wschod od ostatniego pada PTH A2 (X=160,16).
    "C_CURR1": (155.475, 95.10, 270, "F"),
    "R_CURR_S1": (155.475, 97.30, 90, "F"),
    "R_CURR_BOT1": (157.50, 98.20, 0, "F"),
    "R_CURR_TOP1": (159.70, 98.20, 180, "F"),
    "C_VBAT_ADC1": (158.015, 95.10, 270, "F"),
    "R_VBAT_D2": (160.00, 96.20, 0, "F"),
    "R_VBAT_D1": (160.00, 94.65, 180, "F"),
    "R_I2C1": (163.095, 104.85, 90, "F"),
    "R_I2C2": (165.635, 104.85, 90, "F"),

    # Pas poludniowy. RX wychodzi na zachod, GPS na poludnie. PA3 omija lewy
    # otwor A2, SWD stoi pionowo przy wschodniej krawedzi, a rezerwa B biegnie
    # pod GPS-em bez wejscia pod prawy otwor A2.
    "J_RX1": (126.70, 116.00, 270, "F"),
    "J_GPS1": (145.65, 119.20, 0, "F"),
    "J_PA3_1": (139.62, 120.75, 270, "F"),
    "J_SWD1": (173.00, 120.22, 180, "F"),
    "J_AUX_B1": (151.62, 120.75, 90, "F"),
}


LOCKED = {
    "H1", "H2", "H3", "H4", "A1", "A2", "A3",
    "J_ESC1", "J_RX1", "J_GPS1", "J_SWD1", "J_PA3_1",
    "J_AUX_A1", "J_AUX_B1",
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

    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    missing = sorted(set(PLACEMENT) - set(fps))
    extra = sorted(set(fps) - set(PLACEMENT))
    if missing or extra:
        if missing:
            print("BRAK W PCB:", ", ".join(missing))
        if extra:
            print("BRAK W PLANIE:", ", ".join(extra))
        print("Najpierw wykonaj F8 i zapisz PCB; skrypt nie emuluje synchronizacji.")
        return 1

    for ref, (x, y, rot, side) in PLACEMENT.items():
        fp = fps[ref]
        if fp.IsFlipped() != (side == "B"):
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        fp.SetPosition(v(x, y))
        fp.SetOrientationDegrees(rot)
        fp.SetLocked(ref in LOCKED)

    pcbnew.SaveBoard(dst, board)
    print(f"zapisano {dst}: {len(PLACEMENT)} footprinty")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
