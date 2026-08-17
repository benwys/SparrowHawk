#!/usr/bin/env python3
"""Sparrow-II — plan placementu, płytka 41 x 41 mm, środek (150, 100).

Podstawa: docs/sparrow-ii-placement.md.

Cel: zbić liczbę sygnałów wychodzących ze złego boku U_MCU1 (19 na płytce
41x41, 18 na 36x36) i cofnąć trzy regresje, które weszły razem z obrysem:
  * kwarc HSE 11,3 mm od pinów 5/6 zamiast pod nimi,
  * rozwarta pętla przetwornicy (Cin 8,6 mm od pinu VIN),
  * JP_BOOT0 w rogu przeciwległym do pinu 60 — 26,6 mm, najdłuższa sieć.

Plan jest listą RUCHÓW, nie pełnym floorplanem. Elementy, których tu nie ma,
zostają dokładnie tam, gdzie stoją, i wchodzą do silnika jako przeszkody —
reszta płytki jest zrobiona dobrze (sekcja 2 notatki) i przepisywanie jej
od nowa tylko psuje.

ANCHOR to pozycje wynikające z decyzji, SAT to satelity szukające miejsca
wokół kotwicy. Werdykt daje kontrola na WIELOKĄTACH courtyardu porównana
z płytką wejściową: płytka celowo wkłada 0402 w narożne kieszenie LQFP-64
i model prostokątny zgłasza tam kilkanaście kolizji, których nie ma.

Boki U_MCU1 (rot 0, F.Cu, środek 150,95) — z pinmap.py:
    N  x 143.75..156.25 @ y  89.33   BOOT0(60) I2C1(58,59) SPI3(55-57) VTX(51) SWCLK(49)
    W  x 144.32 @ y 91.25.. 98.75    BUZZER(2) OSC(5,6) NRST(7) VBAT_ADC(9) ESC_CURR(10)
                                     VDDA(13) GPS_TX(16)
    S  x 146.25..152.75 @ y 100.67   GPS_RX(17) IMU/SPI1(20-24) LED(25,26) OSD_CS(27)
                                     ESC_TEL(29) VCAP(30)
    E  x 155.68 @ y 91.25.. 98.75    SWDIO(46) USB(44,45) RC(42,43) M4..M1(40-37)
                                     SPI2(34-36) FLASH_CS(33)

Uruchomienie:
    python3 plan.py "Flight Controller.kicad_pcb" out.kicad_pcb
"""
import math
import sys

import pcbnew

MM = pcbnew.FromMM
GAP = 0.15      # wymagany prześwit między courtyardami [mm]
EDGE = 0.30     # courtyard zostaje tyle wewnątrz Edge.Cuts [mm]
MOUNT = 0.35    # prześwit od KRAWĘDZI otworu montażowego; 0,39 to dziś
                # najciaśniejsze miejsce na płytce (C_VID1 przy H_MNT1)

# =========================================================================
# ANCHOR — 'REF': (x, y, obrót, strona). Pozycje z decyzji.
# =========================================================================
ANCHOR = {
    # --- 1. KWARC HSE: regresja, 11,3 mm od pinów 5/6 -------------------
    # Wchodzi w slot po Y_OSD1; pin 3 (RCC_OSC_IN) ~1,2 mm od pinu 5 MCU.
    'Y_HSE1':      (142.30,  94.70,   90, 'B'),
    # Kwarc OSD ustępuje na północ. Do pinów 5/6 U_OSD1 (147, 91.3..92.0)
    # wychodzi ~5,2 mm zamiast 4,9 — na 27 MHz akceptowalne.
    'Y_OSD1':      (141.00,  89.60,   90, 'B'),

    # --- 2. J_ESC1 z dolnej krawędzi na WSCHODNIĄ (krok 1 z notatki) ----
    # M1..M4 siedzą na PC6..PC9 = bok E (155.68, y 95.25..96.75). Złącze na
    # dole dawało 19,3-20,8 mm dookoła obudowy; tutaj 15-18 mm i dobry bok.
    # Leży na B.Cu pod J_SWD1/JP_BOOT0 (F.Cu) — courtyardy się nie tną.
    # UWAGA: to przenosi wyjście wiązki ESC z dolnej krawędzi na prawą.
    'J_ESC1':      (167.30, 105.20,   90, 'B'),

    # --- 3. JP_BOOT0: regresja, 26,6 mm od pinu 60, najdłuższa sieć -----
    # BOOT0 = pin 60 (148.25, 89.33). Zworka na B.Cu na zachód od U_OSD1,
    # w szczelinę po podciągnięciach I2C.
    'JP_BOOT0':    (144.30,  85.60,   90, 'B'),

    # --- 4. pamięć SPI2 pod bok E MCU (krok 3 z notatki) ----------------
    # Było (162.50,106.50): SPI2_MOSI 15,7 / SCK 14,1 mm dookoła obudowy.
    # rot 180 kładzie rzędy padów wzdłuż osi X; zachodni ~2,1 mm od pinów
    # 33-36. J_USB1 jest przewlekany i blokuje B.Cu do y=99,07.
    'U_FLASH1':    (159.60, 103.10,  180, 'B'),

    # --- 5. barometr ustępuje na zachód, dalej pod bokiem S MCU ---------
    'U_BARO1':     (151.30, 105.40,  180, 'B'),

    # --- 6. PĘTLA PRZETWORNICY: regresja, Cin 8,6 mm od pinu VIN --------
    # U_BUCK1 rot 90 zostaje: VIN(2) na (134.57,104.87), SW(8) na
    # (133.29,99.92), BOOT(1) na (133.29,104.87).
    'L_BUCK1':     (137.20,  95.00,    0, 'F'),   # SW 5,3 mm zamiast 7,2
    'D_BUCK1':     (131.75,  94.70,   90, 'F'),   # K(1) 3,6 mm od SW
    # rot -90 obraca pad VBAT w stronę pinu VIN (rot 90 dawał go od tyłu)
    'C_BUCK_IN1':  (133.60, 108.90,  -90, 'F'),
    'C_BUCK_IN2':  (139.10, 108.90,  -90, 'F'),
    'C_BUCK_IN3':  (136.35, 107.95,   90, 'F'),   # 0603 HF pomiędzy nimi
}

# =========================================================================
# SAT — 'REF': (kotwica_x, kotwica_y, strony, [obroty]). Kolejność = pierwszeństwo.
# =========================================================================
SAT = {
    # --- kwarce: najciaśniejsze wymagania, idą pierwsze ------------------
    'C_HSE2':      (142.30,  94.70, 'B', [90, 0]),
    'C_HSE1':      (142.30,  94.70, 'B', [90, 0]),
    'R_HSE2':      (142.30,  94.70, 'B', [90, 0]),
    'C_OSD_XTAL1': (141.00,  89.60, 'B', [90, 0]),
    'C_OSD_XTAL2': (141.00,  89.60, 'B', [90, 0]),
    'R_HSE1':      (141.00,  89.60, 'B', [90, 0]),
    'R_BOOT0':     (144.30,  85.60, 'B', [90, 0]),

    # --- VDDA: pin 13 (144.32, 97.25). Dotąd 2,07 / 3,07 mm — nie psuć --
    'C_VDDA_HF1':  (144.32,  97.25, 'B', [90, 0]),
    'C_VDDA1':     (144.32,  97.25, 'B', [90, 0]),
    'FB_VDDA1':    (144.32,  97.25, 'B', [0, 90]),

    # --- tor analogowy: filtry PRZY pinach ADC, nie przy źródle ---------
    # ESC_CURR miał 22,2 mm (regresja z 12,0), VBAT_ADC 12,0 mm.
    'C_CURR_F1':   (144.32,  95.75, 'B', [90, 0]),   # pin 10
    'R_CURR_F1':   (144.32,  95.75, 'B', [90, 0]),
    'C_VBAT_ADC1': (144.32,  95.25, 'B', [90, 0]),   # pin 9
    'R_VBAT_D2':   (144.32,  95.25, 'B', [90, 0]),
    'R_VBAT_D1':   (144.32,  95.25, 'B', [90, 0]),

    # --- I2C: podciągnięcia PRZY barometrze, nie w rogu płytki ----------
    # Stały na (143.5, 86.75/88.0) — 19 mm od magistrali, którą obsługują.
    # I2C1_SDA/SCL to dwie najdłuższe sieci na płytce (35,3 / 35,0 mm).
    'R_I2C_SCL1':  (151.30, 105.40, 'B', [0, 90]),
    'R_I2C_SDA1':  (151.30, 105.40, 'B', [0, 90]),
    'C_BARO1':     (151.30, 105.40, 'B', [0, 90]),
    'C_BARO2':     (151.30, 105.40, 'B', [0, 90]),

    # --- pamięć SPI -----------------------------------------------------
    'R_USB_SH1':   (162.75,  98.60, 'FB', [0, 90]),   # ustępuje U_FLASH1
    'D_USB_VBUS1': (157.30,  97.60, 'FB', [90, 0]),   # ustępuje U_FLASH1
    # podciągnięcie CS na F.Cu wprost nad padem 1 — na B.Cu nie ma miejsca
    # (U_FLASH1 do x=164,0, J_ESC1 od 164,9, J_USB1 blokuje spód do y=99,2)
    'R_FLASH_CS1': (163.35, 101.40, 'FB', [0, 90]),
    'C_FLASH1':    (159.60, 103.10, 'B', [0, 90]),
    'R_FLASH_WP1': (159.60, 103.10, 'B', [0, 90]),
    'R_FLASH_HD1': (159.60, 103.10, 'B', [0, 90]),

    # --- przetwornica: co nie jest w pętli mocy, schodzi na spód --------
    # góra 60,1 % zajętości, dół 30,1 % — kanały brakują na górze
    'C_BUCK_OUT1': (139.45,  95.00, 'FB', [90, 0]),  # pin 2 dławika (+5V)
    'C_BUCK_SS1':  (135.84,  99.92, 'B', [0, 90]),   # SS(6)
    'R_BUCK_FB1':  (136.87,  99.92, 'B', [0, 90]),   # FB(5)
    'R_BUCK_FB2':  (136.87,  99.92, 'B', [0, 90]),
    'R_BUCK_RT1':  (136.87, 104.87, 'B', [0, 90]),   # RT/SYNC(4)
}


# ------------------------------------------------------------------ pomoc
def crtyd_poly(fp):
    fp.BuildCourtyardCaches()
    layer = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    return fp.GetCourtyard(layer)


def crtyd_bbox(fp):
    p = crtyd_poly(fp)
    bb = fp.GetBoundingBox(False, False) if p.OutlineCount() == 0 else p.BBox()
    return (bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
            bb.GetRight() / 1e6, bb.GetBottom() / 1e6)


def is_mount(fp):
    return any(p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH for p in fp.Pads())


def sides_of(fp):
    if any(p.GetDrillSizeX() > 0 for p in fp.Pads()):
        return ('F', 'B')                       # przewlekany zajmuje obie
    return ('B' if fp.IsFlipped() else 'F',)


def violations(board):
    """Zbiór naruszeń: kolizje wielokątów, obrys, strefy otworów."""
    fps = [f for f in board.GetFootprints()]
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, True)
    outline.Inflate(-MM(EDGE), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MM(0.01))

    mounts = []
    for fp in fps:
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                q = pad.GetPosition()
                mounts.append((fp.GetReference(), q.x / 1e6, q.y / 1e6,
                               max(pad.GetDrillSizeX(), pad.GetDrillSizeY()) / 2e6))

    items = [(f.GetReference(), f, crtyd_poly(f), crtyd_bbox(f), sides_of(f))
             for f in fps if not is_mount(f)]
    out = set()
    for ref, fp, pl, bb, _ in items:
        x0, y0, x1, y1 = bb
        for px, py in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            if not outline.Contains(pcbnew.VECTOR2I(MM(px), MM(py))):
                out.add(f'{ref}: poza obrysem (zapas {EDGE} mm)')
                break
        for mref, mx, my, rad in mounts:
            d = math.hypot(min(max(mx, x0), x1) - mx,
                           min(max(my, y0), y1) - my) - rad
            if d < MOUNT:
                out.add(f'{ref}: {d:.2f} mm od krawędzi {mref}')
    for i in range(len(items)):
        ra, _, pa, _, sa = items[i]
        for j in range(i + 1, len(items)):
            rb, _, pb, _, sb = items[j]
            if (set(sa) & set(sb)) and pa.OutlineCount() and pb.OutlineCount() \
                    and pa.Collide(pb, MM(GAP)):
                out.add(f'{min(ra, rb)} <-> {max(ra, rb)}: courtyardy < {GAP} mm')
    return out


def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else 'out.kicad_pcb'

    base = violations(pcbnew.LoadBoard(src))     # co już dziś jest naruszone

    board = pcbnew.LoadBoard(src)
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    unknown = sorted((set(ANCHOR) | set(SAT)) - set(fps))
    if unknown:
        print('!! NIE MA NA PŁYTCE:', ', '.join(unknown))
        return 1

    # --- zajętość: wszystko, czego nie ruszamy, jest przeszkodą ---------
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, True)
    outline.Inflate(-MM(EDGE), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MM(0.01))
    mounts = [(q.GetPosition().x / 1e6, q.GetPosition().y / 1e6,
               max(q.GetDrillSizeX(), q.GetDrillSizeY()) / 2e6 + MOUNT)
              for f in fps.values() for q in f.Pads()
              if q.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH]
    taken = {'F': [], 'B': []}
    for ref, fp in fps.items():
        if ref in ANCHOR or ref in SAT:
            continue
        bb = crtyd_bbox(fp)
        for sd in (('F', 'B') if is_mount(fp) else sides_of(fp)):
            taken[sd].append((bb, ref))

    def fits(fp, side, bb):
        x0, y0, x1, y1 = bb
        for px, py in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            if not outline.Contains(pcbnew.VECTOR2I(MM(px), MM(py))):
                return 'poza obrysem'
        for mx, my, r in mounts:
            if math.hypot(min(max(mx, x0), x1) - mx,
                          min(max(my, y0), y1) - my) < r:
                return 'strefa otworu montażowego'
        for sd in (('F', 'B') if is_mount(fp) else (side,)):
            for obb, oref in taken[sd]:
                if not (bb[2] + GAP <= obb[0] or obb[2] + GAP <= bb[0] or
                        bb[3] + GAP <= obb[1] or obb[3] + GAP <= bb[1]):
                    return f'kolizja z {oref}'
        return None

    def put(ref, x, y, rot, side):
        fp = fps[ref]
        if fp.IsFlipped() != (side == 'B'):
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        fp.SetOrientationDegrees(rot)
        fp.BuildCourtyardCaches()
        return fp

    problems, unplaced = [], []
    for ref, (x, y, rot, side) in ANCHOR.items():
        fp = put(ref, x, y, rot, side)
        bb = crtyd_bbox(fp)
        why = fits(fp, side, bb)
        if why:
            problems.append(f'{ref}: {why}')
        for sd in (('F', 'B') if is_mount(fp) else (side,)):
            taken[sd].append((bb, ref))

    for ref, (ax, ay, sds, rots) in SAT.items():
        fp, done = fps[ref], False
        for side in sds:
            r = 0.0
            while r <= 14.0 and not done:
                n = 1 if r == 0 else max(24, int(r * 24))
                cands = [(ax, ay)] if r == 0 else [
                    (ax + r * math.cos(2 * math.pi * i / n),
                     ay + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
                for rot in rots:
                    for cx, cy in cands:
                        cx, cy = round(cx * 20) / 20, round(cy * 20) / 20
                        f2 = put(ref, cx, cy, rot, side)
                        bb = crtyd_bbox(f2)
                        if fits(f2, side, bb) is None:
                            for sd in (side,):
                                taken[sd].append((bb, ref))
                            done = True
                            break
                    if done:
                        break
                r += 0.2
            if done:
                break
        if not done:
            unplaced.append(ref)

    if problems:
        print('!! KOLIZJE KOTWIC:')
        for p in problems:
            print('   ', p)
    if unplaced:
        print('!! NIE ZMIEŚCIŁO SIĘ:', ', '.join(unplaced))

    new = violations(board) - base
    gone = base - violations(board)
    if new:
        print('!! NOWE NARUSZENIA wobec płytki wejściowej:')
        for v in sorted(new):
            print('   ', v)
    if not (problems or unplaced or new):
        print(f'OK: {len(ANCHOR)} kotwic + {len(SAT)} satelitów, '
              f'zero nowych naruszeń wobec płytki wejściowej')
    if gone:
        print(f'   (przy okazji zniknęło {len(gone)} naruszeń wejściowych)')

    area = outline.Area() / 1e12
    for sd in ('F', 'B'):
        sel = [f for f in fps.values() if not is_mount(f) and sd in sides_of(f)]
        a = sum((crtyd_bbox(f)[2] - crtyd_bbox(f)[0]) *
                (crtyd_bbox(f)[3] - crtyd_bbox(f)[1]) for f in sel)
        print(f'  {sd}: {len(sel):3d} elem., courtyard {a:7.1f} mm2 '
              f'({a / area:.0%} pola płytki)')

    board.Save(dst)
    print('zapisano:', dst)
    return 1 if (problems or unplaced or new) else 0


if __name__ == '__main__':
    sys.exit(main())
