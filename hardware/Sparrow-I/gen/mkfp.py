#!/usr/bin/env python3
"""Generuje footprinty modułów dla Sparrow-I (KiCad 10 s-expr)."""
import os, uuid, math

LIB = "/home/benio/Desktop/SparrowHawk/hardware/Sparrow-I/Libraries/Footprints"
os.makedirs(LIB, exist_ok=True)
VER = "20260206"

def U(): return str(uuid.uuid4())

def head(name, descr, tags, attr="through_hole"):
    return f'''(footprint "{name}"
\t(version {VER})
\t(generator "sparrowhawk-mkfp")
\t(generator_version "10.0")
\t(layer "F.Cu")
\t(descr "{descr}")
\t(tags "{tags}")
\t(attr {attr})
'''

def prop(nm, val, x, y, layer, hide=False, size=1.0):
    h = "\n\t\t(hide yes)" if hide else ""
    return f'''\t(property "{nm}" "{val}"
\t\t(at {x} {y} 0)
\t\t(layer "{layer}"){h}
\t\t(uuid "{U()}")
\t\t(effects (font (size {size} {size}) (thickness 0.15)))
\t)
'''

def line(x1, y1, x2, y2, layer, w=0.12):
    return (f'\t(fp_line (start {x1} {y1}) (end {x2} {y2})'
            f' (stroke (width {w}) (type solid)) (layer "{layer}") (uuid "{U()}"))\n')

def rect(x1, y1, x2, y2, layer, w=0.12):
    return "".join([line(x1, y1, x2, y1, layer, w), line(x2, y1, x2, y2, layer, w),
                    line(x2, y2, x1, y2, layer, w), line(x1, y2, x1, y1, layer, w)])

def circle(cx, cy, r, layer, w=0.12):
    return (f'\t(fp_circle (center {cx} {cy}) (end {cx+r} {cy})'
            f' (stroke (width {w}) (type solid)) (fill no) (layer "{layer}") (uuid "{U()}"))\n')

def pad_tht(num, x, y, drill=1.0, size=1.7, shape="circle"):
    return (f'\t(pad "{num}" thru_hole {shape} (at {x} {y}) (size {size} {size})'
            f' (drill {drill}) (layers "*.Cu" "*.Mask") (remove_unused_layers no) (uuid "{U()}"))\n')

def pad_npth(x, y, drill):
    return (f'\t(pad "" np_thru_hole circle (at {x} {y}) (size {drill} {drill})'
            f' (drill {drill}) (layers "F&B.Cu" "*.Mask") (uuid "{U()}"))\n')

def text_fab(txt, x, y, layer="F.Fab", size=0.8):
    return (f'\t(fp_text user "{txt}" (at {x} {y} 0) (layer "{layer}") (uuid "{U()}")'
            f' (effects (font (size {size} {size}) (thickness 0.12))))\n')

# ---------------------------------------------------------------- BlackPill
# Zmierzone z WeAct "MiniF4x1Cx_V31 Board Shape":
#   korpus 52,81 x 20,78 ; pin 1 = 1,40 mm od krawędzi USB
#   rozstaw rzędów 15,198 -> przyjęte 15,24 (6 x 2,54, rastrowo)
#   SWD 1x4 dokładnie 17,5 x 2,54 za pinem 1, na osi płytki
BX, BY = 52.81/2, 20.78/2          # 26.405, 10.39
P1X = -BX + 1.40                   # -25.005
ROWY = 15.24/2                     # 7.62
SWDX = P1X + 17.5*2.54             # 19.445

ROW_A = ["5V","GND","3V3","PB10","PB2","PB1","PB0","PA7","PA6","PA5",
         "PA4","PA3","PA2","PA1","PA0","NRST","PC15","PC14","PC13","VBAT_RTC"]
ROW_B = ["PB12","PB13","PB14","PB15","PA8","PA9","PA10","PA11","PA12","PA15",
         "PB3","PB4","PB5","PB6","PB7","PB8","PB9","5V","GND","3V3"]
SWD_N = ["3V3","SWDIO","SWCLK","GND"]

s = head("Module_BlackPill_STM32F411_WeAct_V31",
         "WeAct BlackPill V3.1 (STM32F411CEU6) - gniazda 2x1x20 raster 2,54 + SWD 1x4. "
         "Wymiary wg WeAct MiniF4x1Cx_V31 Board Shape. Modul ~8,5 mm nad plytka. "
         "Courtyard opisuje gniazda przy powierzchni carrier-a; pelny korpus jest na F.Fab.",
         "module blackpill stm32f411 weact socket")
s += prop("Reference", "A**", 0, -BY-1.2, "F.SilkS")
s += prop("Value", "Module_BlackPill_STM32F411_WeAct_V31", 0, BY+1.2, "F.Fab", size=0.8)
s += prop("Footprint", "", 0, 0, "F.Fab", hide=True)
s += prop("Datasheet", "https://github.com/WeActStudio/WeActStudio.MiniSTM32F4x1", 0, 0, "F.Fab", hide=True)
s += prop("Description", "Carrier socket for WeAct BlackPill V3.1", 0, 0, "F.Fab", hide=True)

for i, nm in enumerate(ROW_A):
    s += pad_tht(i+1, round(P1X + i*2.54, 3), -ROWY, shape="rect" if i == 0 else "circle")
for i, nm in enumerate(ROW_B):
    s += pad_tht(i+21, round(P1X + i*2.54, 3), ROWY)
for i, nm in enumerate(SWD_N):
    s += pad_tht(i+41, round(SWDX, 3), round(3.81 - i*2.54, 3))

# obrys korpusu
s += rect(-BX, -BY, BX, BY, "F.Fab", 0.1)
# BlackPill jest uniesiony na gniazdach i dopuszcza niskie SMD pod korpusem.
# Courtyard 2D musi wiec opisywac elementy zajmujace poziom carrier-a, a nie
# rzut calego modulu. Pelny obrys i strefa wtyku USB pozostaja na F.Fab.
SOCKET_X0 = P1X - 1.55
SOCKET_X1 = P1X + 19*2.54 + 1.55
s += rect(SOCKET_X0, -ROWY-1.55, SOCKET_X1, -ROWY+1.55, "F.CrtYd", 0.05)
s += rect(SOCKET_X0,  ROWY-1.55, SOCKET_X1,  ROWY+1.55, "F.CrtYd", 0.05)
s += rect(SWDX-1.55, -3.81-1.55, SWDX+1.55, 3.81+1.55, "F.CrtYd", 0.05)
# silk tylko na krancach, zeby nie kolidowac z padami
for x0, x1 in ((-BX, P1X-1.6), (P1X+19*2.54+1.6, BX)):
    s += rect(x0, -BY, x1, BY, "F.SilkS", 0.15) if x1 > x0 else ""
s += line(-BX, -BY, BX, -BY, "F.SilkS", 0.15)
s += line(-BX, BY, BX, BY, "F.SilkS", 0.15)
# marker pinu 1
s += circle(P1X, -ROWY-1.55, 0.15, "F.SilkS", 0.3)
# opisy pinow na F.Fab
for i, nm in enumerate(ROW_A):
    s += text_fab(nm, round(P1X + i*2.54, 3), -ROWY-1.3, size=0.55)
for i, nm in enumerate(ROW_B):
    s += text_fab(nm, round(P1X + i*2.54, 3), ROWY+1.3, size=0.55)
s += text_fab("USB-C", -BX+3.5, 0)
s += text_fab("SWD", SWDX, -5.4, size=0.6)
s += ")\n"
open(f"{LIB}/Module_BlackPill_STM32F411_WeAct_V31.kicad_mod", "w").write(s)

# ---------------------------------------------------------------- LSM6DSO32
# Adafruit 4692, geometria z plikow Eagle Adafruit-LSM6DSOX-PCB (ta sama plytka)
IX, IY = 25.4/2, 17.78/2
s = head("Module_LSM6DSO32_Adafruit_4692",
         "Adafruit LSM6DSO32 / LSM6DSOX breakout 25,4 x 17,78 mm - listwa 1x9 raster 2,54 "
         "+ 2x M2,5 rozstaw 20,32. Montaz na spodzie, elementy w dol, dystans 2,5 mm. "
         "Courtyard opisuje listwe i mocowania przy carrierze; pelny modul jest na F.Fab.",
         "module imu lsm6dso32 adafruit stemma")
s += prop("Reference", "A**", 0, -IY-1.2, "F.SilkS")
s += prop("Value", "Module_LSM6DSO32_Adafruit_4692", 0, IY+1.2, "F.Fab", size=0.8)
s += prop("Footprint", "", 0, 0, "F.Fab", hide=True)
s += prop("Datasheet", "https://www.adafruit.com/product/4692", 0, 0, "F.Fab", hide=True)
s += prop("Description", "6DoF IMU breakout on SPI", 0, 0, "F.Fab", hide=True)

IMU_N = ["VIN","3Vo","GND","SCL_SCK","SDA_SDI","SDO","CS","INT1","INT2"]
for i, nm in enumerate(IMU_N):
    s += pad_tht(i+1, round(-10.16 + i*2.54, 3), -6.35, shape="rect" if i == 0 else "circle")
for x in (-10.16, 10.16):
    s += pad_npth(x, 6.35, 2.6)
s += rect(-IX, -IY, IX, IY, "F.Fab", 0.1)
# Modul jest uniesiony; na poziomie carrier-a zajmuje listwe oraz mocowania.
s += rect(-11.71, -7.90, 11.71, -4.80, "F.CrtYd", 0.05)
for x in (-10.16, 10.16):
    s += circle(x, 6.35, 2.50, "F.CrtYd", 0.05)
s += rect(-IX, -IY, IX, IY, "F.SilkS", 0.15)
s += circle(-10.16, -6.35-1.55, 0.15, "F.SilkS", 0.3)
for i, nm in enumerate(IMU_N):
    s += text_fab(nm, round(-10.16 + i*2.54, 3), -4.6, size=0.5)
# gniazdo pomocnicze JP2 na module (nieobsadzone) - tylko informacyjnie
for i in range(5):
    s += circle(-5.08 + i*2.54, 6.35, 0.5, "F.Fab", 0.08)
s += text_fab("JP2 AUX (nieobsadzone)", 0, 8.2, size=0.5)
s += text_fab("M2,5", -10.16, 4.0, size=0.5)
s += text_fab("M2,5", 10.16, 4.0, size=0.5)
s += ")\n"
open(f"{LIB}/Module_LSM6DSO32_Adafruit_4692.kicad_mod", "w").write(s)

# ---------------------------------------------------------------- BMP280
BPX, BPY = 15.0/2, 11.5/2
s = head("Module_BMP280_6pin",
         "Modul BMP280 6-pin (GY-BMP280-3.3) 15 x 11,5 mm, listwa 1x6 raster 2,54. "
         "UWAGA: obrys nominalny - zweryfikowac suwmiarka.",
         "module baro bmp280")
s += prop("Reference", "A**", 0, -BPY-1.2, "F.SilkS")
s += prop("Value", "Module_BMP280_6pin", 0, BPY+1.2, "F.Fab", size=0.8)
s += prop("Footprint", "", 0, 0, "F.Fab", hide=True)
s += prop("Datasheet", "", 0, 0, "F.Fab", hide=True)
s += prop("Description", "Barometer module on SPI", 0, 0, "F.Fab", hide=True)
BARO_N = ["VCC","GND","SCL_SCK","SDA_SDI","CSB","SDO"]
for i, nm in enumerate(BARO_N):
    s += pad_tht(i+1, round(-6.35 + i*2.54, 3), -3.75, shape="rect" if i == 0 else "circle")
s += rect(-BPX, -BPY, BPX, BPY, "F.Fab", 0.1)
s += rect(-BPX-0.25, -BPY-0.25, BPX+0.25, BPY+0.25, "F.CrtYd", 0.05)
s += rect(-BPX, -BPY, BPX, BPY, "F.SilkS", 0.15)
s += circle(-6.35, -3.75-1.55, 0.15, "F.SilkS", 0.3)
for i, nm in enumerate(BARO_N):
    s += text_fab(nm, round(-6.35 + i*2.54, 3), -2.1, size=0.5)
s += ")\n"
open(f"{LIB}/Module_BMP280_6pin.kicad_mod", "w").write(s)

print("zapisane:", *sorted(os.listdir(LIB)), sep="\n  ")
