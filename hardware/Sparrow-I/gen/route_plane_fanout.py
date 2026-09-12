#!/usr/bin/env python3
"""Fanout rozlacznych grup GND/+3V3 do wewnetrznych plaszczyzn.

Uzycie:
    KICAD_ROUTE_SCRIPTS=/sciezka/do/kicad-route/scripts \
      python3 route_plane_fanout.py WEJSCIE.kicad_pcb WYJSCIE.kicad_pcb

Skrypt korzysta z tego samego modelu przeszkod i rasteryzacji co skill
kicad-route. Dla kazdej odcietej grupy SMD tworzy krotki escape F/B i via
0,6/0,3 do odpowiedniej plaszczyzny. Po kazdym via przelewa strefy i wymaga
rzeczywistego spadku liczby skladowych KiCada; w przeciwnym razie nie zapisuje
kandydata.
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
from kr import router as rt  # noqa: E402


def choose_smd(board, group):
    wanted = set(group)
    for label, pad in kb.pads_of(board, pad_netname(board, group[0])):
        if label in wanted and pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
            return label, pad
    return None


def pad_netname(board, label):
    ref, pad_name = label.split(".", 1)
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        raise RuntimeError(f"brak footprintu {ref}")
    for pad in fp.Pads():
        if pad.GetPadName() == pad_name:
            return pad.GetNetname()
    raise RuntimeError(f"brak pada {label}")


def special_escape(session, label):
    """Jawna geometria tam, gdzie via obok pada tworzy zbyt waska szyjke."""
    netcode = session.board.FindNet("GND").GetNetCode()
    if label == "U_BUCK1.7":
        rt.add_track(session, netcode, session.board.GetLayerID("F.Cu"),
                     (133.365, 95.525), (133.365, 96.800), 0.30)
        return {"tracks": 1, "vias": 0}
    if label == "J_ESC1.2":
        rt.add_track(session, netcode, session.board.GetLayerID("F.Cu"),
                     (150.300, 82.650), (150.300, 80.900), 0.30)
        rt.add_via(session, netcode, (150.300, 80.900), 0.60, 0.30)
        return {"tracks": 1, "vias": 1}
    return None


def main():
    if len(sys.argv) != 3:
        print(f"uzycie: {sys.argv[0]} WEJSCIE.kicad_pcb WYJSCIE.kicad_pcb")
        return 2

    src, dst = sys.argv[1:]
    session = rt.Session(src)
    if session.board.GetAreaCount() != 3:
        print(f"ODRZUCONO: oczekiwano 3 stref, jest {session.board.GetAreaCount()}")
        return 1

    before_all = kb.all_pad_partitions(session.board)
    before_counts = {n: len(kb.pad_partitions(session.board, n))
                     for n in ("GND", "+3V3")}
    made = 0

    for netname in ("GND", "+3V3"):
        for _ in range(64):
            parts = kb.pad_partitions(session.board, netname)
            if len(parts) <= 1:
                break
            main_group = max(parts, key=len)
            candidates = sorted((g for g in parts if g != main_group),
                                key=lambda g: (len(g), g))
            target = None
            for group in candidates:
                target = choose_smd(session.board, group)
                if target is not None:
                    break
            if target is None:
                print(f"    {netname}: zostaly tylko grupy bez pada SMD")
                break

            label, pad = target
            old = len(parts)
            session.refresh()
            result = special_escape(session, label)
            if result is None:
                ctx = session.ctx(netname,
                                  layers=[session.board.GetLayerID("F.Cu"),
                                          session.board.GetLayerID("B.Cu")],
                                  tight=True)
                result = rt.escape(session, ctx, pad, radius=3.5, verbose=True)
            if not result:
                print(f"ODRZUCONO: brak legalnego escape dla {label}")
                return 1

            pcbnew.ZONE_FILLER(session.board).Fill(session.board.Zones())
            session.board.BuildConnectivity()
            new = len(kb.pad_partitions(session.board, netname, rebuild=False))
            print(f"    {netname:<5} {label:<22} grupy {old} -> {new}")
            if new >= old:
                print(f"ODRZUCONO: escape {label} nie polaczyl plaszczyzny")
                return 1
            made += result["tracks"] + result["vias"]

    after_counts = {n: len(kb.pad_partitions(session.board, n))
                    for n in ("GND", "+3V3")}
    after_all = kb.all_pad_partitions(session.board)
    regressions = kb.partition_regressions(before_all, after_all)
    if regressions:
        print("ODRZUCONO: regresja skladow", regressions[:8])
        return 1
    if sum(after_counts.values()) >= sum(before_counts.values()):
        print("ODRZUCONO: brak poprawy skladow plaszczyzn")
        return 1

    pcbnew.SaveBoard(dst, session.board)
    print(f"zapisano {dst}: {before_counts} -> {after_counts}, obiektow {made}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
