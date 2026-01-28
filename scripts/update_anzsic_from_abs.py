#!/usr/bin/env python3
"""
Fetches the official ANZSIC 2006 classification from the ABS Data API
and regenerates data/anzsic_codes.json with full hierarchy information.

ABS Data API: https://data.api.abs.gov.au
Codelist: CL_ANZSIC_2006

Usage:
    python scripts/update_anzsic_from_abs.py
"""

import json
import os
import sys
import xml.etree.ElementTree as ET
import requests

ABS_API_URL = "https://data.api.abs.gov.au/rest/codelist/ABS/CL_ANZSIC_2006"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "anzsic_codes.json")


def fetch_codelist() -> str:
    """Fetch the ANZSIC 2006 codelist XML from the ABS API."""
    print(f"Fetching codelist from {ABS_API_URL} ...")
    resp = requests.get(ABS_API_URL, timeout=30)
    resp.raise_for_status()
    print(f"  Received {len(resp.text):,} bytes")
    return resp.text


def parse_codes(xml_text: str) -> list:
    """Parse the SDMX XML into a list of {code, title} dicts for all levels."""
    root = ET.fromstring(xml_text)
    codes = []
    for el in root.iter():
        if el.tag.endswith("}Code"):
            code_id = el.attrib.get("id", "")
            name = ""
            for child in el:
                if child.tag.endswith("}Name"):
                    name = child.text or ""
                    break
            codes.append({"code": code_id, "title": name})
    return codes


def build_hierarchy(all_codes: list) -> list:
    """
    Build enriched 4-digit class entries with division, subdivision, and group info.

    ANZSIC structure:
      Division    = single letter (A-S)
      Subdivision = 2 digits
      Group       = 3 digits
      Class       = 4 digits
    """
    # Index by code for lookup
    by_code = {c["code"]: c["title"] for c in all_codes}

    # Division letter -> title
    divisions = {c["code"]: c["title"] for c in all_codes if c["code"].isalpha() and len(c["code"]) == 1}

    # Build a mapping: 2-digit subdivision -> division letter
    # ANZSIC assigns subdivision ranges to divisions. We derive this from the
    # official ABS structure. The standard mapping is:
    subdivision_to_division = _build_subdivision_division_map(divisions, all_codes)

    enriched = []
    four_digit = [c for c in all_codes if len(c["code"]) == 4 and c["code"].isdigit()]

    for entry in four_digit:
        code = entry["code"]
        subdivision_code = code[:2]
        group_code = code[:3]

        division_letter = subdivision_to_division.get(subdivision_code, "")
        division_title = divisions.get(division_letter, "")
        subdivision_title = by_code.get(subdivision_code, "")
        group_title = by_code.get(group_code, "")

        enriched.append({
            "code": code,
            "title": entry["title"],
            "division": division_letter,
            "division_title": division_title,
            "subdivision": subdivision_code,
            "subdivision_title": subdivision_title,
            "group": group_code,
            "group_title": group_title,
        })

    # Sort by code
    enriched.sort(key=lambda x: x["code"])
    return enriched


def _build_subdivision_division_map(divisions: dict, all_codes: list) -> dict:
    """
    Map each 2-digit subdivision to its parent division letter.
    Uses the official ANZSIC 2006 ranges.
    """
    # Official ANZSIC 2006 subdivision-to-division mapping
    ranges = {
        "A": range(1, 6),      # 01-05
        "B": range(6, 11),     # 06-10
        "C": range(11, 26),    # 11-25
        "D": range(26, 30),    # 26-29
        "E": range(30, 33),    # 30-32
        "F": range(33, 38),    # 33-37
        "G": range(38, 44),    # 38-43
        "H": range(44, 46),    # 44-45
        "I": range(46, 54),    # 46-53
        "J": range(54, 62),    # 54-61 (incl 60)
        "K": range(62, 65),    # 62-64
        "L": range(66, 68),    # 66-67
        "M": range(69, 72),    # 69-71 (incl 70)
        "N": range(72, 74),    # 72-73
        "O": range(75, 78),    # 75-77
        "P": range(80, 83),    # 80-82
        "Q": range(84, 88),    # 84-87
        "R": range(89, 93),    # 89-92
        "S": range(94, 97),    # 94-96
    }

    mapping = {}
    for div_letter, rng in ranges.items():
        for num in rng:
            mapping[f"{num:02d}"] = div_letter

    return mapping


def main():
    xml_text = fetch_codelist()
    all_codes = parse_codes(xml_text)

    # Stats
    four_d = [c for c in all_codes if len(c["code"]) == 4 and c["code"].isdigit()]
    three_d = [c for c in all_codes if len(c["code"]) == 3 and c["code"].isdigit()]
    two_d = [c for c in all_codes if len(c["code"]) == 2 and c["code"].isdigit()]
    alpha = [c for c in all_codes if c["code"].isalpha() and len(c["code"]) == 1]

    print(f"  Parsed: {len(alpha)} divisions, {len(two_d)} subdivisions, "
          f"{len(three_d)} groups, {len(four_d)} classes")

    enriched = build_hierarchy(all_codes)
    print(f"  Built {len(enriched)} enriched 4-digit entries")

    # Validate: every entry should have hierarchy populated
    missing_div = [e for e in enriched if not e["division"]]
    if missing_div:
        print(f"  WARNING: {len(missing_div)} entries missing division mapping:")
        for m in missing_div[:5]:
            print(f"    {m['code']}: {m['title']}")

    # Write output
    output = os.path.normpath(OUTPUT_PATH)
    with open(output, "w") as f:
        json.dump(enriched, f, indent=4, ensure_ascii=False)

    print(f"\nWrote {len(enriched)} entries to {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
