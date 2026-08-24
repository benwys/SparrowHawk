#!/usr/bin/env python3
"""Apply an exact, idempotent pcbnew track/via manifest to a KiCad board."""

import argparse
import hashlib
import json
from pathlib import Path

import pcbnew


def mm(value):
    return pcbnew.FromMM(float(value))


def track_key(net, layer, start, end, width):
    a = (mm(start[0]), mm(start[1]))
    b = (mm(end[0]), mm(end[1]))
    return (net, layer, min(a, b), max(a, b), mm(width))


def existing_items(board):
    tracks, vias = {}, {}
    for item in board.GetTracks():
        net = item.GetNetname()
        if isinstance(item, pcbnew.PCB_VIA):
            p = item.GetPosition()
            key = (net, p.x, p.y, item.GetWidth(pcbnew.F_Cu), item.GetDrillValue())
            vias.setdefault(key, []).append(item)
        else:
            a, b = item.GetStart(), item.GetEnd()
            an, bn = (a.x, a.y), (b.x, b.y)
            key = (net, board.GetLayerName(item.GetLayer()), min(an, bn), max(an, bn), item.GetWidth())
            tracks.setdefault(key, []).append(item)
    return tracks, vias


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("board")
    parser.add_argument("manifest")
    parser.add_argument("--allow-sha-mismatch", action="store_true")
    args = parser.parse_args()

    board_path = Path(args.board)
    data = json.loads(Path(args.manifest).read_text())
    digest = hashlib.sha256(board_path.read_bytes()).hexdigest()
    expected = data.get("expected_sha256")
    if expected and digest != expected and not args.allow_sha_mismatch:
        raise SystemExit(f"SHA mismatch: expected {expected}, got {digest}")

    board = pcbnew.LoadBoard(str(board_path))
    tracks, vias = existing_items(board)
    removed_tracks = removed_vias = made_tracks = made_vias = 0

    # Delete before adding so a manifest can atomically replace local geometry.
    # Missing deletion targets are accepted to keep re-application idempotent.
    for item in data["items"]:
        if item["kind"] == "remove_track":
            key = track_key(item["net"], item["layer"], item["start"], item["end"], item["width"])
            matches = tracks.pop(key, [])
            for match in matches:
                board.Remove(match)
                removed_tracks += 1
        elif item["kind"] == "remove_via":
            key = (item["net"], mm(item["at"][0]), mm(item["at"][1]), mm(item["diameter"]), mm(item["drill"]))
            matches = vias.pop(key, [])
            for match in matches:
                board.Remove(match)
                removed_vias += 1

    for item in data["items"]:
        net = board.FindNet(item["net"])
        if not net:
            raise SystemExit(f"Unknown net: {item['net']}")
        if item["kind"] == "track":
            key = track_key(item["net"], item["layer"], item["start"], item["end"], item["width"])
            if key in tracks:
                continue
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(mm(item["start"][0]), mm(item["start"][1])))
            t.SetEnd(pcbnew.VECTOR2I(mm(item["end"][0]), mm(item["end"][1])))
            t.SetWidth(mm(item["width"]))
            t.SetLayer(board.GetLayerID(item["layer"]))
            t.SetNetCode(net.GetNetCode())
            board.Add(t)
            tracks.setdefault(key, []).append(t)
            made_tracks += 1
        elif item["kind"] == "via":
            key = (item["net"], mm(item["at"][0]), mm(item["at"][1]), mm(item["diameter"]), mm(item["drill"]))
            if key in vias:
                continue
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(key[1], key[2]))
            v.SetWidth(key[3])
            v.SetDrill(key[4])
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetNetCode(net.GetNetCode())
            board.Add(v)
            vias.setdefault(key, []).append(v)
            made_vias += 1
        elif item["kind"] in {"remove_track", "remove_via"}:
            continue
        else:
            raise SystemExit(f"Unknown item kind: {item['kind']}")

    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(str(board_path))
    print(
        f"removed tracks={removed_tracks}, vias={removed_vias}; "
        f"added tracks={made_tracks}, vias={made_vias}"
    )


if __name__ == "__main__":
    main()
