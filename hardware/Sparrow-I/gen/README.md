# Generatory Sparrow-I

Schemat, symbole, footprinty modułów i szkielet mechaniczny płytki powstały
z tych skryptów, nie z klikania w GUI. Trzymamy je, bo są jedynym zapisem tego,
**dlaczego** netlista wygląda tak, jak wygląda — i pozwalają odtworzyć całość po
zmianie w mapie pinów.

Kolejność uruchamiania (każdy nadpisuje swój produkt):

```bash
python3 mkfp.py      # Libraries/Footprints/Module_*.kicad_mod
python3 mksym.py     # Libraries/Symbols/SparrowHawk_Modules.kicad_sym
python3 mkboard.py   # obrys 54 x 46 + otwory M3   -- UWAGA: kasuje placement
python3 mksch.py     # schemat
```

**`mkboard.py` tworzy płytkę od zera.** Po rozpoczęciu placementu nie wolno go
uruchomić ponownie, bo skasuje rozmieszczenie elementów. Obrys zmienia się wtedy
ręcznie albo skillem `kicad-place`.

Footprinty A1 i A2 używają courtyardów powierzchni montażowej (gniazda/listwa
i mocowania), a pełne obrysy uniesionych modułów są na `Fab`. Dzięki temu niski
osprzęt pod BlackPillem i lutowane końcówki po przeciwnej stronie nie tworzą
fałszywych kolizji 2D; ograniczenie wysokości przy zachodnim USB nadal obowiązuje
mechanicznie.

Po każdej regeneracji schematu:

```bash
kicad-cli sch erc --format json -o /tmp/erc.json "../Flight Controller - carrier board.kicad_sch"
kicad-cli sch export netlist --format kicadsexpr -o /tmp/net.net "../Flight Controller - carrier board.kicad_sch"
python3 ~/.agents/skills/kicad-design/scripts/netcheck.py /tmp/net.net
python3 ~/.agents/skills/kicad-design/scripts/libcheck.py /tmp/net.net ..
```

Stan odniesienia schematu: ERC 0 naruszeń, 52/52 footprintów rozwiązanych
(w tym H1-H4 obecne w schemacie, aby F8 ich nie usuwało), netlista 51 sieci bez
zwarć. PCB jest w pełni rozprowadzone: 0 niepołączonych i 0 problemów parity;
In1 to GND, a In2 to mieszana płaszczyzna +3V3 z trasami `/VBAT` i rezerwową
`/RSV_PB14`. Ostrzeżenia DRC dotyczące sitodruku pozostają celowo do ręcznej
obróbki i trzeba je usunąć przed końcowym eksportem produkcyjnym.

`symlib.py` to lokalna kopia parsera pinów, na której te skrypty były pisane.
Nowszy i pełniejszy odpowiednik jest w skillu `kicad-design`
(`scripts/kd/libs.py`) — przy większych zmianach lepiej użyć jego.
