"""Czyta pozycje pinow z bibliotek .kicad_sym (sexpr) - potrzebne, zeby etykiety
trafialy dokladnie w konce pinow."""
import re, os

def _tokenize(s):
    return re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', s)

def _parse(tokens, i=0):
    out = []
    while i < len(tokens):
        t = tokens[i]
        if t == '(':
            sub, i = _parse(tokens, i+1)
            out.append(sub)
        elif t == ')':
            return out, i+1
        else:
            out.append(t[1:-1] if t.startswith('"') else t)
            i += 1
    return out, i

def load_lib(path):
    tree, _ = _parse(_tokenize(open(path).read()))
    return tree[0]

def _walk(node, tag):
    for x in node:
        if isinstance(x, list) and x and x[0] == tag:
            yield x

def symbol_pins(lib_tree, name):
    """-> {pin_number: (x, y, angle, pin_name, etype)}"""
    for sym in _walk(lib_tree, "symbol"):
        if len(sym) > 1 and sym[1] == name:
            pins = {}
            def scan(n):
                for x in n:
                    if isinstance(x, list):
                        if x and x[0] == "pin":
                            etype = x[1]
                            at = next(_walk(x, "at"))
                            nm = next(_walk(x, "name"))[1]
                            num = next(_walk(x, "number"))[1]
                            pins[num] = (float(at[1]), float(at[2]),
                                         float(at[3]) if len(at) > 3 else 0.0, nm, etype)
                        else:
                            scan(x)
            scan(sym)
            return pins
    raise KeyError(f"{name} nie znaleziony w bibliotece")

_CACHE = {}
GLOBAL = "/usr/share/kicad/symbols"
PROJ = "/home/benio/Desktop/SparrowHawk/hardware/Sparrow-I/Libraries/Symbols"

def lib_path(lib):
    """projektowa biblioteka ma pierwszenstwo, potem globalna"""
    for d in (PROJ, GLOBAL):
        p = os.path.join(d, lib + ".kicad_sym")
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"brak biblioteki {lib}.kicad_sym")

def pins_for(lib_id):
    lib, name = lib_id.split(":", 1)
    if lib not in _CACHE:
        _CACHE[lib] = load_lib(lib_path(lib))
    return symbol_pins(_CACHE[lib], name)

if __name__ == "__main__":
    for lid in ["Device:R", "Device:C", "Device:L", "Device:D_Schottky", "Device:D_Zener",
                "power:GND", "power:+5V", "power:+3V3", "power:PWR_FLAG",
                "Connector_Generic:Conn_01x08", "Connector_Generic:Conn_01x04",
                "SparrowHawk_Modules:Module_LSM6DSO32_Adafruit_4692"]:
        try:
            p = pins_for(lid)
            print(f"{lid:52s} " + "  ".join(f"{k}:({v[0]},{v[1]},{int(v[2])}){v[3]}" for k, v in sorted(p.items())[:5]))
        except Exception as e:
            print(f"{lid:52s} BLAD {e}")
