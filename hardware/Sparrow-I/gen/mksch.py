#!/usr/bin/env python3
"""Generuje schemat Sparrow-I (jedna kartka A3).

Styl: kazde polaczenie realizowane etykieta lokalna albo symbolem zasilania na
krotkim odcinku przy pinie. Nie ma dlugich przewodow miedzy elementami - dzieki
temu generacja jest deterministyczna, a netlista jednoznaczna.
"""
import os, re, uuid, math
import symlib

SCH = "/home/benio/Desktop/SparrowHawk/hardware/Sparrow-I/Flight Controller - carrier board.kicad_sch"
PROJECT = "Flight Controller - carrier board"
ROOT_UUID = "b5f653e5-5bf2-409a-8571-503c5bbe7196"   # zachowane z istniejacego pliku
G = 1.27

def U(): return str(uuid.uuid4())
def snap(v): return round(round(v / G) * G, 4)

POWER_NETS = {"GND": ("power:GND", 0), "+5V": ("power:+5V", 0), "+3V3": ("power:+3V3", 0)}

# ---------------------------------------------------------------- model
class Comp:
    def __init__(self, ref, lib_id, value, fp, x, y, nets=None, nc=(), rot=0, descr=""):
        self.ref, self.lib_id, self.value, self.fp = ref, lib_id, value, fp
        self.x, self.y, self.rot = snap(x), snap(y), rot
        self.nets = nets or {}
        self.nc = set(nc)
        self.descr = descr
        self.pins = symlib.pins_for(lib_id)
        for p in list(self.nets) + list(self.nc):
            if p not in self.pins:
                raise KeyError(f"{ref}: pin {p} nie istnieje w {lib_id}")

    def pin_xy(self, num):
        px, py, _, _, _ = self.pins[num]
        return (round(self.x + px, 4), round(self.y - py, 4))

    def pin_out(self, num):
        """kierunek 'na zewnatrz' w ukladzie schematu"""
        _, _, a, _, _ = self.pins[num]
        r = math.radians(a)
        return (round(-math.cos(r), 4), round(math.sin(r), 4))

COMPS = []
def C(*a, **kw):
    c = Comp(*a, **kw); COMPS.append(c); return c

R04 = "Resistor_SMD:R_0402_1005Metric"
C04 = "Capacitor_SMD:C_0402_1005Metric"
C08 = "Capacitor_SMD:C_0805_2012Metric"
C12 = "Capacitor_SMD:C_1210_3225Metric"
SH8 = "Connector_JST:JST_SH_SM08B-SRSS-TB_1x08-1MP_P1.00mm_Horizontal"
SH4 = "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"
def PH(n): return f"Connector_PinHeader_2.54mm:PinHeader_1x{n:02d}_P2.54mm_Vertical"
TP  = "TestPoint:TestPoint_Pad_D1.5mm"

# ---------------------------------------------------------------- A1 BlackPill
C("A1", "SparrowHawk_Modules:Module_BlackPill_STM32F411_WeAct_V31",
  "BlackPill V3.1", "SparrowHawk_Modules:Module_BlackPill_STM32F411_WeAct_V31",
  95.25, 130.81,
  nets={
    "1": "+5V", "2": "GND", "3": "+3V3", "4": "CS_IMU", "5": "RSV_PB2",
    "6": "M4", "7": "M3", "8": "SPI_MOSI", "9": "SPI_MISO", "10": "SPI_SCK",
    "11": "RSV_PA4", "12": "PA3_AUX", "13": "CURR_SENSE", "14": "VBAT_SENSE",
    "15": "RSV_PA0", "16": "NRST", "17": "RSV_PC15", "18": "RSV_PC14",
    "19": "RSV_PC13", "20": "RSV_VBAT_RTC",
    "21": "RSV_PB12", "22": "RSV_PB13", "23": "RSV_PB14", "24": "RSV_PB15",
    "25": "IMU_INT1", "26": "RSV_PA9", "27": "RSV_PA10",
    "30": "CS_BARO", "31": "RSV_PB3", "32": "M1", "33": "M2",
    "34": "UART1_TX", "35": "UART1_RX", "36": "I2C_SCL", "37": "I2C_SDA",
    "38": "+5V", "39": "GND", "40": "+3V3",
    "41": "+3V3", "42": "SWDIO", "43": "SWCLK", "44": "GND"},
  nc=("28", "29"),          # PA11/PA12 = USB D-/D+ na module, nie ruszamy
  descr="WeAct BlackPill V3.1, STM32F411CEU6. PA11/PA12 zajete przez USB modulu.")

# ---------------------------------------------------------------- czujniki
C("A2", "SparrowHawk_Modules:Module_LSM6DSO32_Adafruit_4692",
  "LSM6DSO32", "SparrowHawk_Modules:Module_LSM6DSO32_Adafruit_4692",
  215.9, 55.88,
  nets={"1": "+3V3", "3": "GND", "4": "SPI_SCK", "5": "SPI_MOSI",
        "6": "SPI_MISO", "7": "CS_IMU", "8": "IMU_INT1"},
  nc=("2", "9"),
  descr="IMU na spodzie, wysrodkowany w rastrze srub. VIN z 3V3 (nie 5 V).")

C("A3", "SparrowHawk_Modules:Module_BMP280_6pin",
  "BMP280", "SparrowHawk_Modules:Module_BMP280_6pin",
  215.9, 101.6,
  nets={"1": "+3V3", "2": "GND", "3": "SPI_SCK", "4": "SPI_MOSI",
        "5": "CS_BARO", "6": "SPI_MISO"},
  descr="Barometr na spodzie obok IMU, ta sama magistrala SPI1.")

# ---------------------------------------------------------------- zlacza
C("J_ESC1", "Connector_Generic:Conn_01x08", "ESC 1x8 SH", SH8, 330.2, 45.72,
  nets={"1": "VBAT", "2": "GND", "3": "CURR_RAW", "4": "M1", "5": "M2",
        "6": "M3", "7": "M4", "8": "ESC_SPARE"},
  descr="Standard SparrowHawk: VBAT, GND, prad, M1-M4, zapas.")
C("J_RX1", "Connector_Generic:Conn_01x04", "RX 1x4 SH", SH4, 330.2, 92.71,
  nets={"1": "+5V", "2": "GND", "3": "UART1_RX", "4": "UART1_TX"},
  descr="Odbiornik na USART1 (PB7 = RX, PB6 = TX).")
C("J_GPS1", "Connector_Generic:Conn_01x04", "GPS 1x4 SH", SH4, 330.2, 118.11,
  nets={"1": "+5V", "2": "GND", "3": "I2C_SCL", "4": "I2C_SDA"},
  descr="GPS/magnetometr na I2C1 (PB8/PB9).")
C("J_SWD1", "Connector_Generic:Conn_01x04", "SWD 1x4", PH(4), 330.2, 143.51,
  nets={"1": "+3V3", "2": "SWDIO", "3": "SWCLK", "4": "GND"},
  descr="SWD wyprowadzone z gniazda 1x4 pod modulem na krawedz plytki.")
C("J_PA3_1", "Connector_Generic:Conn_01x04", "PA3 / zapas ESC", PH(4), 330.2, 166.37,
  nets={"1": "PA3_AUX", "2": "ESC_SPARE", "3": "GND", "4": "+3V3"},
  descr="Zworka PA3 (analog albo USART2_RX) plus zapasowa linia ze zlacza ESC.")
C("J_AUX_A1", "Connector_Generic:Conn_01x08", "Rezerwa rzad A", PH(8), 330.2, 199.39,
  nets={"1": "RSV_PA4", "2": "RSV_PB2", "3": "RSV_PA0", "4": "NRST",
        "5": "RSV_PC15", "6": "RSV_PC14", "7": "RSV_PC13", "8": "RSV_VBAT_RTC"},
  descr="Nieuzyte piny rzedu A na goldpiny.")
C("J_AUX_B1", "Connector_Generic:Conn_01x07", "Rezerwa rzad B", PH(7), 330.2, 240.03,
  nets={"1": "RSV_PB12", "2": "RSV_PB13", "3": "RSV_PB14", "4": "RSV_PB15",
        "5": "RSV_PA9", "6": "RSV_PA10", "7": "RSV_PB3"},
  descr="Nieuzyte piny rzedu B na goldpiny. PA11/PA12 pominiete - to USB.")

# ---------------------------------------------------------------- mechanika
# Otwory musza byc elementami schematu. Footprinty dodane tylko w mkboard.py
# sa traktowane przez F8 jako nadmiarowe i znikaja przy synchronizacji PCB.
for i, y in enumerate((101.60, 116.84, 132.08, 147.32), start=1):
    C(f"H{i}", "Mechanical:MountingHole", "MountingHole M3",
      "MountingHole:MountingHole_3.2mm_M3", 288.29, y,
      descr="Otwor M3 rastra 30,5 x 30,5 mm; pozycja mechaniczna ustalana na PCB.")

# ---------------------------------------------------------------- przetwornica 5 V
C("U_BUCK1", "LMR14030SDDAR:LMR14030SDDAR", "LMR14030SDDAR",
  "SparrowHawk_Modules:SOIC127P600X170-9N", 215.9, 187.96,
  nets={"1": "BUCK_BOOT", "2": "VBAT", "4": "BUCK_RT", "5": "BUCK_FB",
        "6": "BUCK_SS", "7": "GND", "8": "BUCK_SW", "9": "GND"},
  nc=("3",),   # EN ma wewnetrzne podciagniecie - przetwornica zawsze zalaczona
  descr="Przetwornica 5 V, 40 V wejscia - zapas na 6S. Uklad jak w Sparrow-II.")

def passive(ref, lib, val, fp, x, y, top, bot, descr=""):
    return C(ref, lib, val, fp, x, y, nets={"1": top, "2": bot}, descr=descr)

BX, BY = 38.1, 196.85        # rzad 1: wejscie i sterowanie przetwornicy
STEP = 20.32
passive("C_BUCK_IN1", "Device:C", "4.7uF/50V", C12, BX + 0*STEP, BY, "VBAT", "GND")
passive("C_BUCK_IN2", "Device:C", "4.7uF/50V", C12, BX + 1*STEP, BY, "VBAT", "GND")
passive("C_BUCK_IN3", "Device:C", "100nF/50V", C04, BX + 2*STEP, BY, "VBAT", "GND")
passive("C_BUCK_BOOT1", "Device:C", "100nF",   C04, BX + 3*STEP, BY, "BUCK_BOOT", "BUCK_SW")
passive("C_BUCK_SS1", "Device:C", "22nF",      C04, BX + 4*STEP, BY, "BUCK_SS", "GND")
passive("R_BUCK_RT1", "Device:R", "49.9k",     R04, BX + 5*STEP, BY, "BUCK_RT", "GND")

BY2 = BY + 25.4              # rzad 2: wyjscie przetwornicy
passive("R_BUCK_FB1", "Device:R", "100k",      R04, BX + 0*STEP, BY2, "+5V", "BUCK_FB")
passive("R_BUCK_FB2", "Device:R", "17.8k",     R04, BX + 1*STEP, BY2, "BUCK_FB", "GND")
passive("C_BUCK_OUT1", "Device:C", "47uF/16V", C12, BX + 2*STEP, BY2, "+5V", "GND")
passive("C_5V_BULK1", "Device:C", "10uF/16V",  C08, BX + 3*STEP, BY2, "+5V", "GND")
passive("L_BUCK1", "Device:L", "6.8uH",
        "SparrowHawk_Modules:L_Sunlord_SWPA6028S", BX + 4*STEP, BY2, "+5V", "BUCK_SW")
C("D_BUCK1", "Device:D_Schottky", "B260A-13-F", "Diode_SMD:D_SMA", BX + 7*STEP, BY2,
  nets={"1": "BUCK_SW", "2": "GND"}, descr="Dioda gaszaca - LMR14030 jest asynchroniczna.")
C("D_TVS1", "Device:D_TVS", "SMAJ28A", "Diode_SMD:D_SMA", BX + 9*STEP, BY2,
  nets={"1": "VBAT", "2": "GND"}, descr="Ochrona przepieciowa VBAT, 28 V standoff (6S = 25,2 V).")

# ---------------------------------------------------------------- pomiary i podciagniecia
SX, SY = 38.1, 247.65        # rzad 3: pomiary
SY4 = SY + 25.4              # rzad 4: sciagacze i podciagniecia
passive("R_VBAT_D1", "Device:R", "100k", R04, SX + 0*STEP, SY, "VBAT", "VBAT_SENSE")
passive("R_VBAT_D2", "Device:R", "10k",  R04, SX + 1*STEP, SY, "VBAT_SENSE", "GND")
passive("C_VBAT_ADC1", "Device:C", "100nF", C04, SX + 2*STEP, SY, "VBAT_SENSE", "GND")

passive("R_CURR_TOP1", "Device:R", "0R",  R04, SX + 3*STEP, SY, "CURR_RAW", "CURR_DIV")
passive("R_CURR_BOT1", "Device:R", "DNP", R04, SX + 4*STEP, SY, "CURR_DIV", "GND")
passive("R_CURR_S1", "Device:R", "1k",   R04, SX + 5*STEP, SY, "CURR_DIV", "CURR_SENSE")
passive("C_CURR1", "Device:C", "100nF",  C04, SX + 6*STEP, SY, "CURR_SENSE", "GND")

MX = SX
for i, m in enumerate(("M1", "M2", "M3", "M4")):
    passive(f"R_PD_{m}", "Device:R", "4.7k", R04, MX + i*STEP, SY4, m, "GND",
            descr="Sciagacz - PB4 to JTRST z wewnetrznym podciagnieciem ~40k.")

passive("R_I2C1", "Device:R", "4.7k", R04, MX + 4*STEP, SY4, "+3V3", "I2C_SCL")
passive("R_I2C2", "Device:R", "4.7k", R04, MX + 5*STEP, SY4, "+3V3", "I2C_SDA")

passive("C_3V3_BULK1", "Device:C", "10uF/16V", C08, SX + 6*STEP, SY4, "+3V3", "GND")
passive("C_3V3_1", "Device:C", "100nF", C04, SX + 7*STEP, SY4, "+3V3", "GND")

# ---------------------------------------------------------------- punkty pomiarowe
TPX, TPY = 154.94, 60.96
for i, (nm, net) in enumerate([("TP_M1", "M1"), ("TP_M2", "M2"), ("TP_M3", "M3"),
                               ("TP_M4", "M4"), ("TP_VBAT1", "VBAT"), ("TP_5V1", "+5V"),
                               ("TP_3V3_1", "+3V3"), ("TP_GND1", "GND"), ("TP_GND2", "GND")]):
    C(nm, "Connector:TestPoint", nm.replace("TP_", ""), TP,
      TPX, TPY + i * 12.7, nets={"1": net})

# flaga zasilania dla VBAT (siec bez zrodla mocy w rozumieniu ERC)
C("#FLG01", "power:PWR_FLAG", "PWR_FLAG", "", 288.29, 45.72, nets={"1": "VBAT"})
C("#FLG02", "power:PWR_FLAG", "PWR_FLAG", "", 288.29, 60.96, nets={"1": "+5V"})
C("#FLG03", "power:PWR_FLAG", "PWR_FLAG", "", 288.29, 76.20, nets={"1": "GND"})

# ================================================================ emisja
def esc(s): return s.replace("\\", "\\\\").replace('"', '\\"')

def sym_block(libfile, name, lib_id):
    """wyciaga surowy blok (symbol "name" ...) i przemianowuje na lib_id"""
    txt = open(libfile).read()
    m = re.search(r'\n\t\(symbol "' + re.escape(name) + r'"', txt)
    if not m:
        raise KeyError(f"{name} w {libfile}")
    i = m.start() + 1
    d = 0
    for j in range(i, len(txt)):
        if txt[j] == '(':
            d += 1
        elif txt[j] == ')':
            d -= 1
            if d == 0:
                break
    blk = txt[i:j + 1]
    blk = blk.replace(f'(symbol "{name}"', f'(symbol "{esc(lib_id)}"', 1)
    return "\t\t" + blk.replace("\n\t", "\n\t\t").rstrip() + "\n"

out = []
out.append(f'''(kicad_sch
\t(version 20250114)
\t(generator "sparrowhawk-mksch")
\t(generator_version "10.0")
\t(uuid "{ROOT_UUID}")
\t(paper "A3")
\t(title_block
\t\t(title "Sparrow-I - carrier board")
\t\t(company "Politechnika Warszawska - Wydzial Elektryczny")
\t\t(rev "v0.1")
\t\t(comment 1 "Carrier dla WeAct BlackPill V3.1 - wariant B, silniki na TIM3")
\t\t(comment 2 "Czujniki na spodzie, wewnatrz rastra M3 30,5 x 30,5")
\t)
''')

# --- lib_symbols
used = {}
for c in COMPS:
    used[c.lib_id] = None
for lid, _ in POWER_NETS.values():          # GND/+5V/+3V3 stawiane poza COMPS
    used[lid] = None
out.append("\t(lib_symbols\n")
for lid in sorted(used):
    lib, name = lid.split(":", 1)
    out.append(sym_block(symlib.lib_path(lib), name, lid))
out.append("\t)\n")

# --- przewody, etykiety, symbole zasilania
wires, labels, powers, ncs = [], [], [], []
STUB = 2.54

for c in COMPS:
    if c.lib_id.startswith("power:"):
        continue
    done = {}
    for pin, net in c.nets.items():
        px, py = c.pin_xy(pin)
        if (px, py) in done:
            continue
        done[(px, py)] = net
        dx, dy = c.pin_out(pin)
        ex, ey = round(px + dx * STUB, 4), round(py + dy * STUB, 4)
        wires.append((px, py, ex, ey))
        # Symbol zasilania tylko wtedy, gdy odcinek wychodzi w strone, w ktora
        # symbol i tak jest zwrocony - zadnych kolanek. Kolanko o dlugosci rastra
        # pinow (2,54) ladowalo na odcinku sasiedniego pinu i zwieralo zlacza.
        canonical = dx == 0 and ((net == "GND" and dy > 0) or (net != "GND" and dy < 0))
        if net in POWER_NETS and canonical:
            lid, _ = POWER_NETS[net]
            powers.append((lid, net, ex, ey, 0))
        else:
            just = "right" if dx < 0 else ("left" if dx > 0 else ("left" if dy < 0 else "left"))
            lrot = 0 if dx else 90
            labels.append((net, ex, ey, lrot, just))
    for pin in c.nc:
        px, py = c.pin_xy(pin)
        dx, dy = c.pin_out(pin)
        ncs.append((round(px + dx * STUB, 4), round(py + dy * STUB, 4)))
        wires.append((px, py, round(px + dx * STUB, 4), round(py + dy * STUB, 4)))

for x1, y1, x2, y2 in wires:
    out.append(f'\t(wire (pts (xy {x1} {y1}) (xy {x2} {y2}))\n'
               f'\t\t(stroke (width 0) (type default))\n\t\t(uuid "{U()}")\n\t)\n')
for x, y in ncs:
    out.append(f'\t(no_connect (at {x} {y}) (uuid "{U()}"))\n')
for net, x, y, rot, just in labels:
    out.append(f'\t(label "{esc(net)}"\n\t\t(at {x} {y} {rot})\n\t\t(fields_autoplaced yes)\n'
               f'\t\t(effects (font (size 1.27 1.27)) (justify {just} bottom))\n'
               f'\t\t(uuid "{U()}")\n\t)\n')

# --- instancje symboli
def text_slots(x, y, pins):
    """gdzie postawic Reference/Value, zeby nie wlazly na etykiety przy pinach"""
    pts = {(round(px, 4), round(py, 4)) for px, py, _, _, _ in pins.values()}
    if not pts:                                                    # np. otwor montazowy
        return (x, y - 2.54, "center"), (x, y + 2.54, "center")
    if len(pts) == 2 and all(abs(px) < 0.01 for px, _ in pts):        # pionowy dwunozny
        return (x + 2.54, y - 1.27, "left"), (x + 2.54, y + 1.27, "left")
    if len(pts) == 1:                                                 # punkt pomiarowy
        return (x + 2.54, y + 1.27, "left"), (x + 2.54, y + 3.81, "left")
    top = y - max(py for _, py in pts)
    return (x, top - 3.81, "center"), (x, top - 1.27, "center")

def emit_symbol(ref, lib_id, value, fp, x, y, rot, descr, pins, hide_ref=False):
    u = U()
    s = [f'\t(symbol\n\t\t(lib_id "{esc(lib_id)}")\n\t\t(at {x} {y} {rot})\n\t\t(unit 1)\n'
         f'\t\t(exclude_from_sim no)\n\t\t(in_bom {"no" if ref.startswith("#") else "yes"})\n'
         f'\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(fields_autoplaced yes)\n\t\t(uuid "{u}")\n']
    (rx, ry, rj), (vx, vy, vj) = text_slots(x, y, pins)
    def p(nm, val, px, py, hide, just=None):
        h = "\n\t\t\t(hide yes)" if hide else ""
        j = f" (justify {just})" if just and just != "center" else ""
        return (f'\t\t(property "{nm}" "{esc(val)}"\n\t\t\t(at {round(px,4)} {round(py,4)} 0){h}\n'
                f'\t\t\t(effects (font (size 1.27 1.27)){j})\n\t\t)\n')
    s.append(p("Reference", ref, rx, ry, hide_ref, rj))
    s.append(p("Value", value, vx, vy, False, vj))
    s.append(p("Footprint", fp, x, y, True))
    s.append(p("Datasheet", "", x, y, True))
    s.append(p("Description", descr, x, y, True))
    seen = set()
    for num in pins:
        if num in seen:
            continue
        seen.add(num)
        s.append(f'\t\t(pin "{num}" (uuid "{U()}"))\n')
    s.append(f'\t\t(instances\n\t\t\t(project "{PROJECT}"\n\t\t\t\t(path "/{ROOT_UUID}"\n'
             f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
    return "".join(s)

for c in COMPS:
    if c.lib_id.startswith("power:"):
        continue
    out.append(emit_symbol(c.ref, c.lib_id, c.value, c.fp, c.x, c.y, c.rot, c.descr, c.pins))

pn = 1
for lid, net, x, y, rot in powers:
    out.append(emit_symbol(f"#PWR{pn:03d}", lid, net, "", x, y, rot, "", symlib.pins_for(lid), hide_ref=True))
    pn += 1
for c in COMPS:
    if c.lib_id.startswith("power:"):
        px, py = c.pin_xy("1")
        net = c.nets["1"]
        out.append(emit_symbol(c.ref, c.lib_id, c.value, "", c.x, c.y, c.rot, "", c.pins, hide_ref=True))
        labels.append((net, px, py, 0, "left"))
        out.append(f'\t(label "{esc(net)}"\n\t\t(at {px} {py} 0)\n\t\t(fields_autoplaced yes)\n'
                   f'\t\t(effects (font (size 1.27 1.27)) (justify left bottom))\n'
                   f'\t\t(uuid "{U()}")\n\t)\n')

out.append(f'\t(sheet_instances\n\t\t(path "/" (page "1"))\n\t)\n\t(embedded_fonts no)\n)\n')

open(SCH, "w").write("".join(out))
print(f"zapisano {SCH}")
print(f"  elementow: {len(COMPS)}   przewodow: {len(wires)}   etykiet: {len(labels)}"
      f"   symboli zasilania: {len(powers)}   no-connect: {len(ncs)}")
