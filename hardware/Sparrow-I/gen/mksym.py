#!/usr/bin/env python3
"""Generuje symbole modulow dla Sparrow-I."""
import os

SYM = "/home/benio/Desktop/SparrowHawk/hardware/Sparrow-I/Libraries/Symbols"
os.makedirs(SYM, exist_ok=True)

def pin(etype, x, y, ang, name, num, length=5.08):
    return f'''\t\t\t(pin {etype} line
\t\t\t\t(at {x} {y} {ang})
\t\t\t\t(length {length})
\t\t\t\t(name "{name}" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "{num}" (effects (font (size 1.27 1.27))))
\t\t\t)
'''

def prop(nm, val, x, y, hide=False, size=1.27, justify=None):
    h = "\n\t\t\t(hide yes)" if hide else ""
    j = f"\n\t\t\t\t(justify {justify})" if justify else ""
    return f'''\t\t(property "{nm}" "{val}"
\t\t\t(at {x} {y} 0){h}
\t\t\t(effects (font (size {size} {size})){j})
\t\t)
'''

def sym_head(name, ref, value, fp, ds, descr, kw, refpos, valpos):
    return f'''\t(symbol "{name}"
\t\t(pin_names (offset 0.508))
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
''' + prop("Reference", ref, refpos[0], refpos[1], justify="left") \
    + prop("Value", value, valpos[0], valpos[1], size=0.9, justify="left") \
    + prop("Footprint", fp, 0, 0, hide=True) \
    + prop("Datasheet", ds, 0, 0, hide=True) \
    + prop("Description", descr, 0, 0, hide=True) \
    + prop("ki_keywords", kw, 0, 0, hide=True)

def body(name, x1, y1, x2, y2):
    return f'''\t\t(symbol "{name}_0_1"
\t\t\t(rectangle
\t\t\t\t(start {x1} {y1})
\t\t\t\t(end {x2} {y2})
\t\t\t\t(stroke (width 0.254) (type default))
\t\t\t\t(fill (type background))
\t\t\t)
\t\t)
'''

out = ['(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "sparrowhawk-mksym")\n\t(generator_version "10.0")\n']

# ------------------------------------------------------------- BlackPill
N = "Module_BlackPill_STM32F411_WeAct_V31"
ROW_A = [("5V","power_in"),("GND","power_in"),("3V3","power_out"),("PB10","bidirectional"),
         ("PB2","bidirectional"),("PB1","bidirectional"),("PB0","bidirectional"),("PA7","bidirectional"),
         ("PA6","bidirectional"),("PA5","bidirectional"),("PA4","bidirectional"),("PA3","bidirectional"),
         ("PA2","bidirectional"),("PA1","bidirectional"),("PA0","bidirectional"),("NRST","bidirectional"),
         ("PC15","bidirectional"),("PC14","bidirectional"),("PC13","bidirectional"),("VBAT_RTC","passive")]
ROW_B = [("PB12","bidirectional"),("PB13","bidirectional"),("PB14","bidirectional"),("PB15","bidirectional"),
         ("PA8","bidirectional"),("PA9","bidirectional"),("PA10","bidirectional"),("PA11","bidirectional"),
         ("PA12","bidirectional"),("PA15","bidirectional"),("PB3","bidirectional"),("PB4","bidirectional"),
         ("PB5","bidirectional"),("PB6","bidirectional"),("PB7","bidirectional"),("PB8","bidirectional"),
         ("PB9","bidirectional"),("5V","power_in"),("GND","power_in"),("3V3","passive")]
SWD = [("3V3","passive"),("SWDIO","bidirectional"),("SWCLK","input"),("GND","power_in")]

s = sym_head(N, "A", N, f"SparrowHawk_Modules:{N}",
             "https://github.com/WeActStudio/WeActStudio.MiniSTM32F4x1",
             "WeAct BlackPill V3.1 - modul STM32F411CEU6, HSE 25 MHz, gniazda 2x1x20 + SWD 1x4",
             "module blackpill stm32f411 weact", (-20.32, 31.75), (-20.32, -31.75))
s += body(N, -20.32, 27.94, 20.32, -27.94)
s += f'\t\t(symbol "{N}_1_1"\n'
for i, (nm, et) in enumerate(ROW_A):
    s += pin(et, -25.4, round(24.13 - i*2.54, 2), 0, nm, i+1)
for i, (nm, et) in enumerate(ROW_B):
    s += pin(et, 25.4, round(24.13 - i*2.54, 2), 180, nm, i+21)
for i, (nm, et) in enumerate(SWD):
    s += pin(et, -7.62 + i*5.08, -33.02, 90, nm, i+41)
s += "\t\t)\n\t)\n"
out.append(s)

# ------------------------------------------------------------- LSM6DSO32
N = "Module_LSM6DSO32_Adafruit_4692"
IMU = [("VIN","power_in"),("3Vo","power_out"),("GND","power_in"),("SCK","input"),
       ("SDI","input"),("SDO","tri_state"),("~{CS}","input"),("INT1","output"),("INT2","output")]
s = sym_head(N, "A", N, f"SparrowHawk_Modules:{N}", "https://www.adafruit.com/product/4692",
             "Adafruit LSM6DSO32 6DoF IMU breakout. SCK/SDI przez translator BSS138 + 10k "
             "(zegar praktycznie do ~2 MHz). SDO/INT1/INT2 wprost z czujnika. Zasilac VIN z 3V3.",
             "module imu lsm6dso32 adafruit spi", (-12.7, 15.24), (-12.7, -16.51))
s += body(N, -12.7, 12.7, 12.7, -12.7)
s += f'\t\t(symbol "{N}_1_1"\n'
for i, (nm, et) in enumerate(IMU):
    s += pin(et, -17.78, round(10.16 - i*2.54, 2), 0, nm, i+1)
s += "\t\t)\n\t)\n"
out.append(s)

# ------------------------------------------------------------- BMP280
N = "Module_BMP280_6pin"
BARO = [("VCC","power_in"),("GND","power_in"),("SCK","input"),
        ("SDI","input"),("~{CSB}","input"),("SDO","tri_state")]
s = sym_head(N, "A", N, f"SparrowHawk_Modules:{N}", "",
             "Modul BMP280 6-pin (GY-BMP280-3.3) na SPI. CSB nisko = SPI, SDO = MISO.",
             "module baro bmp280 spi", (-10.16, 10.16), (-10.16, -11.43))
s += body(N, -10.16, 7.62, 10.16, -7.62)
s += f'\t\t(symbol "{N}_1_1"\n'
for i, (nm, et) in enumerate(BARO):
    s += pin(et, -15.24, round(6.35 - i*2.54, 2), 0, nm, i+1)
s += "\t\t)\n\t)\n"
out.append(s)

out.append(")\n")
open(f"{SYM}/SparrowHawk_Modules.kicad_sym", "w").write("".join(out))
print("zapisane:", f"{SYM}/SparrowHawk_Modules.kicad_sym")
