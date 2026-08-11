"""Fast, non-redistributive structure checks for local candidate workbooks."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

import pandas as pd

from tourism_forecasting.data import sha256_file
from tourism_forecasting.paths import resolve_from_root

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
EXPECTED_INSTAGRAM_SHA256 = "d6230b265bd4a058c636a0a2c0b8a7b36343cb96cdb03333440669f96b1c0f5e"
EXPECTED_GTD_SHA256 = "4f372d996ba31365f69a13b15a1e72507c7d8b65faad430e9343b44a538c2b07"


def _shared_strings(archive: zipfile.ZipFile, needed: set[int]) -> dict[int, str]:
    if not needed or "xl/sharedStrings.xml" not in archive.namelist():
        return {}
    values: dict[int, str] = {}
    with archive.open("xl/sharedStrings.xml") as stream:
        index = -1
        for _event, element in ET.iterparse(stream, events=("end",)):
            if element.tag == f"{{{MAIN_NS}}}si":
                index += 1
                if index in needed:
                    values[index] = "".join(
                        node.text or "" for node in element.iter(f"{{{MAIN_NS}}}t")
                    )
                element.clear()
                if needed.issubset(values):
                    break
    return values


def _sheet_paths(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        relationship.attrib["Id"]: relationship.attrib["Target"]
        for relationship in relationships.findall(f"{{{PKG_REL_NS}}}Relationship")
    }
    sheets: list[tuple[str, str]] = []
    for sheet in workbook.findall(f".//{{{MAIN_NS}}}sheet"):
        relationship_id = sheet.attrib[f"{{{DOC_REL_NS}}}id"]
        target = PurePosixPath(targets[relationship_id].lstrip("/"))
        if not str(target).startswith("xl/"):
            target = PurePosixPath("xl") / target
        sheets.append((sheet.attrib["name"], str(target)))
    return sheets


def _sheet_header_and_dimension(archive: zipfile.ZipFile, sheet_path: str) -> tuple[str, list[str]]:
    dimension = "unknown"
    cells: list[tuple[str, str, int | str | None]] = []
    with archive.open(sheet_path) as stream:
        for event, element in ET.iterparse(stream, events=("start", "end")):
            if event == "start" and element.tag == f"{{{MAIN_NS}}}dimension":
                dimension = element.attrib.get("ref", "unknown")
            if event == "end" and element.tag == f"{{{MAIN_NS}}}row":
                if element.attrib.get("r") != "1":
                    element.clear()
                    continue
                for cell in element.findall(f"{{{MAIN_NS}}}c"):
                    kind = cell.attrib.get("t", "n")
                    value_node = cell.find(f"{{{MAIN_NS}}}v")
                    inline_node = cell.find(f".//{{{MAIN_NS}}}t")
                    raw: int | str | None
                    if kind == "s" and value_node is not None:
                        raw = int(value_node.text or "0")
                    elif inline_node is not None:
                        raw = inline_node.text or ""
                    else:
                        raw = value_node.text if value_node is not None else None
                    cells.append((cell.attrib.get("r", ""), kind, raw))
                element.clear()
                break
    needed = {int(raw) for _, kind, raw in cells if kind == "s" and isinstance(raw, int)}
    strings = _shared_strings(archive, needed)
    header = [strings.get(raw, "") if kind == "s" else str(raw or "") for _, kind, raw in cells]
    return dimension, header


def inspect_xlsx_structure(path: str | Path) -> dict[str, object]:
    source = resolve_from_root(path)
    with zipfile.ZipFile(source) as archive:
        corrupt_member = archive.testzip()
        sheets = []
        for name, sheet_path in _sheet_paths(archive):
            dimension, header = _sheet_header_and_dimension(archive, sheet_path)
            sheets.append({"name": name, "dimension": dimension, "header": header})
        core_properties: dict[str, str] = {}
        if "docProps/core.xml" in archive.namelist():
            core = ET.fromstring(archive.read("docProps/core.xml"))
            for element in core:
                key = element.tag.rsplit("}", 1)[-1]
                if key in {"created", "modified"}:
                    core_properties[key] = element.text or ""
    return {
        "filename": source.name,
        "bytes": source.stat().st_size,
        "sha256": sha256_file(source),
        "zip_crc_ok": corrupt_member is None,
        "sheets": sheets,
        "core_properties": core_properties,
    }


def assess_external_data_files(
    *,
    tables_dir: str | Path = "reports/tables",
    diagnostics_dir: str | Path = "results/diagnostics",
) -> tuple[Path, Path]:
    instagram = inspect_xlsx_structure("data/kaggle/trending_hashtags.xlsx")
    gtd = inspect_xlsx_structure("data/kaggle/global_terrorism.xlsx")
    records = [
        {
            "candidate": "local_instagram_trending_hashtags",
            "sha256": instagram["sha256"],
            "size_bytes": instagram["bytes"],
            "sheets": len(instagram["sheets"]),
            "dimensions": ";".join(sheet["dimension"] for sheet in instagram["sheets"]),
            "coverage": "2024-05-28..2025-05-27 (deep forensic audit)",
            "decision": "reject",
            "reason": (
                "triplicated one-year data; unverified provenance/geography; "
                "no Turkey travel intent"
            ),
            "redistribution": "no",
        },
        {
            "candidate": "global_terrorism_database",
            "sha256": gtd["sha256"],
            "size_bytes": gtd["bytes"],
            "sheets": len(gtd["sheets"]),
            "dimensions": ";".join(sheet["dimension"] for sheet in gtd["sheets"]),
            "coverage": "1970..2020; 1993 absent",
            "decision": "conditional_accept_common_sample",
            "reason": (
                "licensed security analysis through 2020 only; methodology breaks and missing codes"
            ),
            "redistribution": "raw/codebook prohibited",
        },
    ]
    expected = {
        "local_instagram_trending_hashtags": EXPECTED_INSTAGRAM_SHA256,
        "global_terrorism_database": EXPECTED_GTD_SHA256,
    }
    for record in records:
        if record["sha256"] != expected[record["candidate"]]:
            record["coverage"] = "not assessed: checksum differs from forensically audited file"
            record["decision"] = "quarantine_checksum_mismatch"
            record["reason"] = "deep-audit conclusions are checksum-bound and cannot be transferred"
            record["redistribution"] = "no"
    table_path = resolve_from_root(tables_dir) / "external_data_inventory.csv"
    table_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(table_path, index=False)
    diagnostics_path = resolve_from_root(diagnostics_dir) / "external_data_structure.json"
    diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics_path.write_text(
        json.dumps({"instagram": instagram, "gtd": gtd}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return table_path, diagnostics_path
