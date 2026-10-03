# Sparrow-III — zamówienie w JLCPCB, rewizja III-order-20261003

Stan na 03.10.2026. Zamówienie składa użytkownik: wymaga konta JLCPCB i płatności.

## Pliki do wgrania

Pliki są w tym katalogu (`hardware/Sparrow-III/Production/`).

| Krok w JLC | Plik |
|---|---|
| PCB — „Add gerber file” | `Flight_Controller-III-order-20261003-gerbers.zip` |
| PCBA — BOM | `Flight_Controller-III-order-20261003-bom-jlcpcb.csv` (kolumny Comment, Designator, Footprint, LCSC) |
| PCBA — CPL | `Flight_Controller-III-order-20261003-cpl-jlcpcb.csv` (Designator, Mid X, Mid Y, Rotation, Layer) |
| Kontrola obrotów w podglądzie | `kontrola/polaryzacja-top.png`, `polaryzacja-bottom.png`, `polaryzacja.csv` |
| Lista części ze stanem i zamiennikami | `BOM-zamowienie.csv` |

## Parametry płytki

| Pole w JLC | Wybór | Dlaczego |
|---|---|---|
| Layers | 4 | stackup projektu |
| Dimensions | 40 × 40 mm (wczyta się z Gerberów) | |
| PCB Thickness | 1.6 mm | |
| Impedance Control / Stackup | **Yes — JLC04161H-7628** | na tym stackupie liczono parę USB (0,25/0,15 mm ≈ 90 Ω) i rozkład warstw In1/In2 |
| Surface Finish | **ENIG** | płaskie pady pod LGA (IMU, baro, magnetometr) |
| Outer / Inner Copper | 1 oz / 0.5 oz | stackup JLC04161H-7628 |
| Via Covering | **Tented** | przelotki zakryte maską z obu stron (ustawienie płytki) |
| Min via hole size/diameter | 0.3 / 0.6 mm (bez dopłaty) | najmniejsza przelotka projektu |
| PCB Color / Silkscreen | Green / White | decyzja z 01.10 |
| Board outline tolerance | standard (±0.2 mm) | |
| Mark on PCB (numer zamówienia) | „Remove Mark” albo zostawić | w projekcie nie ma pola „JLCJLCJLCJLC” na numer |
| Castellated / Edge plating / Gold fingers | No | |
| Remark / uwagi do zamówienia | patrz niżej | tolerancja otworów ustalających USB |

**Uwaga do zamówienia (pole „Remark”):**

> J_USB1 (USB-C JAE DX07S016JA1R1500) has two NPTH locating holes, 0.65 mm and 0.80 mm, 6.00 mm apart, for connector pegs 0.52 ±0.05 mm. Please drill them to nominal size with finished tolerance +0.05/-0.00 mm (no undersize). Thank you.

JLC podaje dla NPTH typową tolerancję ±0,08 mm i dopuszcza ciaśniejszą na życzenie. Przy otworach mniejszych o 0,05 mm i skrajnych tolerancjach złącza kołki mogłyby nie wejść. Dotyczyłoby to także oryginalnego wzoru JAE.

## Parametry montażu

| Pole w JLC | Wybór | Dlaczego |
|---|---|---|
| PCBA Type | **Standard** | LIS2MDLTR i DPS368XTSA1 są dostępne tylko w Standard; montaż dwustronny |
| Assembly Side | **Both sides** | Top 22 elementy, Bottom 55 |
| Tooling holes / edge rails | dodane przez JLC (jeśli zaproponuje) | płytka nie ma fiducjali ani ramek |
| Confirm Parts Placement | **Yes** | weryfikacja obrotów przez JLC przed produkcją |

## Części wymagające uwagi przy zamówieniu

- **C_B1, C_B5 — Panasonic EEE-FT1H470AP (C92059):** brak w magazynie JLC. JLC proponuje zamówienie wstępne (pre-order): min. 35 szt., ok. 8,8 USD, termin kilka dni.
  - Natychmiastowy zamiennik: KNSCHA 126RV0135 (C7461266), 47 µF/50 V, 6,3 × 5,4 mm, w magazynie.
  - Ma nieokreślony ESR, więc słabiej tłumi dzwonienie przy podłączaniu pakietu.
- **U_LDO1 — TLV75533PDYDR (C28642215):** w magazynie JLC tylko 29 szt., czyli najwyżej 29 płytek w tej partii.
- **D_BUCK1 — STPS3H100U (C283521):** 185 szt. w magazynie.
- **Kontrola RTG:** JLC może ją doliczyć dla obudów z padami pod spodem (ICM-42688-P, LIS2MDL, DPS368, W25Q128 WSON).
- **Opłaty za części extended:** 45 z 46 pozycji to „extended” (jedna „basic”), więc doliczona będzie opłata za każdą unikalną pozycję extended.

## Obroty (CPL)

Plik CPL zawiera obroty z KiCada bez poprawek. Biblioteki JLC mają czasem inny punkt zerowy obrotu niż KiCad, więc w podglądzie montażu sprawdź każdy element spolaryzowany:
- **Góra (10):** U_MCU1, U_BUCK1, D_BUCK1, D_USB_VBUS1, LED_PWR1, LED_STAT1, LED_STAT2, C_B1, C_B5, J_USB1.
- **Spód (10):** U_IMU1, U_MAG1, U_BARO1, U_FLASH1, U_LDO1, U_ESD1, Y_HSE1, D_TVS1, J_ESC1, J_GPS1.

Czerwona kropka na obrazach kontrolnych oznacza pin 1, katodę albo biegun „+”. Obraz spodu jest lustrzany, czyli widok od spodu, tak jak w podglądzie JLC.

## Zamienniki względem BOM z 01.10

Pełna lista ze stanami magazynowymi i uzasadnieniem: `BOM-zamowienie.csv`. W skrócie:

| Oznaczenie | Było | Jest (LCSC) | Uzasadnienie |
|---|---|---|---|
| C_BUCK_IN1/2 | TDK C3225X7S2A475K200AB | TDK C3225X7S2A475KT000N (C342614) | ten sam wyrób TDK pod starszym kodem |
| C_BUCK_OUT1 | TDK C3225X5R1A107M250AC (10 V) | Taiyo Yuden EMK325ABJ107MM-T (C394395, 16 V) | więcej pojemności przy 5 V; LMR14030 określa tylko minimum COUT |
| C_LDO_IN1/OUT1 | TDK C1608X7S1E225K080AB | Murata GRM188Z71E225KE43D (C415535) | 2,2 µF/25 V X7R; TLV755P wymaga > 0,47 µF efektywnie |
| C_VCAP1, R_VCAP_ESR1 | TDK 4,7 µF; Panasonic 0,15 Ω | Samsung CL21B475KPFNNNE (C87998); UNI-ROYAL 0603WAF150LT5E (C45879) | ESR gałęzi 0,15 Ω w zakresie 0,1–0,2 Ω (DS11853 tab. 19) |
| Y_HSE1 | Abracon ABM8AIG (CL 12 pF, ESR 150 Ω, kod nieosiągalny) | YXC X32258MOB4SI (C2682775, CL 12 pF, ESR 180 Ω) | gm_crit ≈ 0,41 mA/V < 1 mA/V (STM32F722); kondensatory 12 pF bez zmian |
| U_BARO1 | Infineon DPS310XTSA1 (wycofany w LCSC/JLC) | Infineon DPS368XTSA1 (C3232508) | ta sama obudowa i rozkład pinów, wyższy o 0,1 mm; ten sam interfejs rejestrów |
| FB_VDDA1 | TE 1-2176742-6 | TAI-TECH HCB1005KF-101T10 (C356953) | 100 Ω przy 100 MHz, DCR 0,2 Ω |
| pozostałe 4 kondensatory | TDK | Samsung, te same parametry | bulk 10 µF, MAG 22 µF i 220 nF |

## Zmiany na płytce w tej rewizji

- **J_USB1:** otwory ustalające NPTH Ø0,6 mm i owal 0,85 × 0,6 mm zastąpiono okrągłymi Ø0,65 i Ø0,80 mm, bo JLC nie wykonuje szczelin NPTH węższych niż 1,0 mm.
  - Rysunek JAE SJ121836 rev.3 podaje kołki 2 × Ø0,52 ±0,05 mm w rozstawie 6 ±0,1 mm.
  - Pierwsza wersja (Ø0,60 + Ø0,75) nie mieściła kołków w skrajnych tolerancjach, co wykazał audyt Codexa.
  - Obecne otwory dają w osi rozstawu sumę luzów 0,155 mm przy nominalnych otworach i 0,125 mm przy otworach mniejszych o 0,03 mm, czyli tyle samo co owal JAE.
  - Odstęp od padów: 0,275 mm i 0,20 mm (minimum JLC dla NPTH to 0,2 mm).
- **J_BAT1:** usunięto pastę z padów przewodów baterii. Przelotki w padach nie wciągną lutu przy montażu, a przewody lutuje się ręcznie.
- **Pozostałe:** pole LCSC we wszystkich 77 elementach, usunięte nieaktualne wykluczenia DRC, rewizja „III-order-20261003”.

## Po montażu

- **Firmware:**
  - IMU obrócony o 180°, ustawić wyrównanie CW180.
  - Barometr DPS368: sterownik DPS310 musi zaakceptować ten układ (rodzina DPS3xx).
- **Pomiary:** napięcia +5 V i +3V3 pod obciążeniem, start i częstotliwość kwarcu HSE, temperatura LDO i przetwornicy, szumy czujników przy pracującym napędzie.
