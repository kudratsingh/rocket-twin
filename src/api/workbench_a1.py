"""Separately versioned A1 connection drawings; copies recorded data, no solves."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

from src.api.workbench import ROOT, WorkbenchUnavailable

MAPPING = "configs/engineering/workbench-a1.yaml"


def build_workbench_a1(root: Path = ROOT) -> dict[str, Any]:
    mapping = yaml.safe_load((root / MAPPING).read_text())
    sources: list[dict[str, Any]] = []
    content: dict[str, Any] = {}
    for item in mapping["sources"]:
        path = (root / item["path"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise WorkbenchUnavailable("A1 source path escapes repository")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise WorkbenchUnavailable("A1 source revision mismatch: " + item["path"])
        sources.append(item)
        if path.suffix in (".json", ".yaml", ".yml"):
            content[item["id"]] = yaml.safe_load(raw)
    cfg, r, historical = (content[k] for k in ("a1_config", "a1_record", "historical_fit"))
    if r["id"] != cfg["id"] or not r["status"].startswith("not_admitted"):
        raise WorkbenchUnavailable("A1 result is not the selected held concept")
    for source in sources:
        if (
            source["id"] in ("a1_config", "a1_research", "published_a")
            and r["input_sha256"].get(source["path"]) != source["sha256"]
        ):
            raise WorkbenchUnavailable("A1 record/config source mismatch: " + source["path"])
        if (
            source["id"] == "a1_script"
            and r["input_sha256"].get("scripts/wo03_a1_connections.py") != source["sha256"]
        ):
            raise WorkbenchUnavailable("A1 executed-script mismatch")
    mapping_raw = (root / MAPPING).read_bytes()
    sources.append(
        {
            "id": "a1_mapping",
            "path": MAPPING,
            "sha256": hashlib.sha256(mapping_raw).hexdigest(),
            "description": "A1 display source mapping; no physics",
        }
    )
    src = ["a1_config", "a1_record"]

    def value(
        number: float | None, unit: str, note: str, state: str = "estimated"
    ) -> dict[str, Any]:
        return {"value": number, "unit": unit, "note": note, "state": state}

    def finding(fid: str, label: str, note: str, state: str = "unavailable") -> dict[str, Any]:
        return {"id": fid, "label": label, "note": note, "state": state, "source_ids": src}

    def feature(
        fid: str,
        label: str,
        role: str,
        z: list[float],
        ri: float | None,
        ro: float | None,
        note: str,
        axes: list[float] | None = None,
        widths: list[float] | None = None,
    ) -> dict[str, Any]:
        return {
            "id": fid,
            "label": label,
            "role": role,
            "start_mm": z[0],
            "end_mm": z[1],
            "inner_radius_mm": ri,
            "outer_radius_mm": ro,
            "axes_deg": axes or [],
            "widths_mm": widths or [],
            "note": note,
            "source_ids": src,
        }

    i, h = cfg["interface"], cfg["harness"]
    features = []
    for key, label, role in (
        ("sleeve", "New G11 sleeve", "sleeve"),
        ("stop", "Integral axial stop", "stop"),
        ("upper_body", "Retained paper upper body", "body"),
        ("aft_can", "Structural aft can", "body"),
        ("collar", "External load-spreading collar", "collar"),
    ):
        p = i[key]
        features.append(
            feature(
                key,
                label,
                role,
                p["z_mm"],
                p["ri_mm"],
                p["ro_mm"],
                "Source-defined concept dimensions; not actual CAD or manufactured tolerance.",
            )
        )
    p = i["index"]
    features.append(
        feature(
            "keys",
            "Unequal indexing keys",
            "index",
            p["z_mm"],
            p["ri_mm"],
            p["ro_mm"],
            "6/4/4mm keys;6.6/4.6/4.6mm slots. Per-flank clearance; not axial retention.",
            p["axes_deg"],
            p["widths_mm"],
        )
    )
    features.append(
        feature(
            "bolts",
            "Three M5x16 retention sets",
            "retention",
            [952, 952],
            20.2,
            41.2,
            "External head envelope and inner thread-tip are reservations; actual SKU/lock/preload unqualified.",
            i["bolts"]["axes_deg"],
            [5, 5, 5],
        )
    )
    features.append(
        feature(
            "harness_sleeve",
            "Six inward-routed harness legs",
            "harness",
            [900, 962],
            None,
            21,
            "21mm centre radius,12.7mm radial width, offsets±6mm; fan toR24 atz1004. Width is not this centre radius.",
            h["axes_deg"],
            [12.7],
        )
    )
    for key, role in (
        ("fixed_body_reservation", "motor"),
        ("retainer_reservation", "motor_service"),
    ):
        p = cfg["motor"][key]
        features.append(
            feature(
                key,
                key.replace("_", " "),
                role,
                p["z_mm"],
                0,
                p["radius_mm"],
                "Protected envelope, not exact current purchased geometry.",
            )
        )
    fits = [
        {
            "id": "historical",
            "label": "Published A/B old coupler — preserved failure",
            "result": value(
                historical["minimum_radial_gap_mm"],
                "mm",
                "64.0mm old coupler/64.4mm bore; nominal0.2, minimum0, maximum0.4mm cold.",
                "failed",
            ),
            "criterion": "At least0.1mm minimum radial clearance",
            "source_ids": ["historical_fit"],
        }
    ]
    fit = r["interface_fit"]
    fits.append(
        {
            "id": "aft_fit",
            "label": "A1 sleeve/can radial clearance",
            "result": value(
                fit["minimum_bounded_mm"],
                "mm",
                f"Cold minimum/nominal/maximum {fit['minimum_cold_mm']:.3f}/{fit['nominal_mm']:.3f}/{fit['maximum_cold_mm']:.3f}mm. Bounded hot/wet maximum {fit['maximum_bounded_mm']:.4f}mm. Calculated bound only; manufacture and properties unqualified.",
                "calculated",
            ),
            "criterion": "At least0.1mm; calculated bounded screen passes, actual acceptance unknown",
            "source_ids": src,
        }
    )
    for n, key in enumerate(r["key_flanks"]):
        fits.append(
            {
                "id": f"key{n}",
                "label": f"Key{n+1} per-flank clearance",
                "result": value(
                    key["minimum_per_flank_mm"],
                    "mm",
                    f"Nominal {key['nominal_per_flank_mm']:.3f}mm per flank; cold max {key['maximum_cold_per_flank_mm']:.3f}mm. Total is twice per-flank.",
                    "calculated",
                ),
                "criterion": "At least0.1mm per flank under declared bounds; not measured",
                "source_ids": src,
            }
        )
    definitions = [
        (
            "fin",
            "Fin forces and turning effect",
            [
                "Carbon skins / dense plywood root",
                "Two real898mm² root edge bonds + fillets",
                "Structural motor tube and slotted can",
                "Cuff / upper sleeve / actual paper body",
            ],
            "8.830Nm and220.759N already include DF3. Outer/inner reactions821.222/-600.464N; peeling, installed movement and flutter unavailable. Toe/heel stops locate axially; no proven radial capture.",
        ),
        (
            "recovery",
            "Parachute-opening pull",
            [
                "Retained primary connector + routed bridles",
                "R6 saddles / finite6mm cap",
                "Windowed integral cuff and can lap",
                "Bolted sleeve / upper paper bond + retained branches",
            ],
            "Full severe demand at one endpoint. No equal strap/bolt sharing or rigid support. Finished eyes, finite cap spreading and upper paper/peel capacity unqualified.",
        ),
        (
            "motor_forward",
            "Motor forward thrust —450N case",
            [
                "Current G80 ring/nozzle geometry UNKNOWN",
                "Proposed2mm seat overlaps liner/foil",
                "Continuous root-web bonds / outer can",
                "Finite can / actual upper connection",
            ],
            "450N forward case. The source-layout audit finds a2mm axial seat overlap with retained mica/foil, so the seat is not geometrically admissible. Original16.318MPa strip arithmetic cannot close that conflict. Reverse retention is a separate path.",
        ),
        (
            "motor_reverse",
            "Motor reverse retention —450N case",
            [
                "Motor rear contact / exact nozzle UNKNOWN",
                "Independent threaded retainer body and cap",
                "5g adapter/bond allocation / structural tube",
                "Continuous root webs / finite can",
            ],
            "Separate reverse450N case. Not serial with forward thrust or parachute loads. Exact retainer mating, installed dimensions, bond and hot capacity remain unavailable.",
        ),
        (
            "upper",
            "Aft structure to upper assembly",
            [
                "Finite outer can / collar",
                "ThreeM5 sets, crush spacers and curved doublers",
                "120mm G11 sleeve /76mm upper bonded overlap",
                "Real0.5mm paper wall and retained-body connections",
            ],
            "One-bolt whole-force/torque bound gives463.661MPa combined proxy versus estimated200MPa: failed admission screen, not measured yielding. Bearing/tear-out and paper capacity unavailable.",
        ),
    ]
    paths = [
        {
            "id": pid,
            "label": label,
            "sequence": sequence,
            "state": "failed" if pid in ("upper", "motor_forward") else "unavailable",
            "note": note,
            "source_ids": src,
        }
        for pid, label, sequence, note in definitions
    ]
    cases = []
    for c in r["complete_cases"]:
        cases.append(
            {
                "id": c["id"],
                "label": (
                    "Nominal +50g"
                    if c["extra_aft_g"] == 0
                    else "+50g and additional20g / motor-CG probe"
                ),
                "state": "failed",
                "total_mass_g": c["total_g"],
                "loaded_cg_mm": c["cg_mm"],
                "burnout_cg_mm": c["burnout_cg_mm"],
                "reference_cp_mm": c["reference_cp_mm"],
                "loaded_margin_cal": c["reference_loaded_static_cal"],
                "burnout_margin_cal": c["reference_burnout_static_cal"],
                "recovery_force_n": c["severe_recovery_DF3_N"],
                "guide_results": c["guides"],
                "baseline_formal_headroom_g": c["baseline_formal_headroom_g"],
                "baseline_planning_headroom_g": c["baseline_planning_headroom_g"],
                "note": "Full separate50g unchanged. CP and drag reuse C1/reference hypotheses; collar and bolt heads change actual aerodynamics. No stability/flight acceptance; full inertia unavailable.",
                "source_ids": src,
            }
        )
    return {
        "schema_version": "1.0.0",
        "id": cfg["id"],
        "label": "A1 connections — separate preliminary concept",
        "status": "NOT ADMITTED: full baseline mass and connection screens fail; thermal and installed evidence open",
        "identity": {
            "candidate_id": "A1",
            "source_identity": sources[0]["sha256"],
            "cad_revision": None,
            "frame": "z=0 nose; z increases aft; radius from centreline; diagram not to scale",
            "units": "mm, g, N, N m, MPa, m/s; calibre uses66mm reference diameter",
        },
        "generated_from": sources,
        "geometry": {
            "sleeve_length": value(
                120, "mm", "Explicit104-to120mm sleeve change; G80 candidate only"
            ),
            "sleeve_outer_diameter": value(
                63.4, "mm", "Explicit64-to63.4mm change, mass/strength counted"
            ),
            "sleeve_inner_diameter": value(61.4, "mm", "1mm G11 wall; original cardboard ID61mm"),
            "upper_stop_station": value(918, "mm", "4mm stop from918to922"),
            "axial_overlap": value(40, "mm", "Removable aft engagement; upper bonded overlap76mm"),
            "index_feature_count": value(3, "", "Unequal widths define unique orientation"),
            "retention_feature_count": value(
                3, "", "M5 bolts are independent of recovery connector and motor retainer"
            ),
            "features": features,
            "note": "Local source-defined concept geometry. No complete CAD/mesh or sharedG54/G12 adoption.",
        },
        "fit_rows": fits,
        "paths": paths,
        "protected_volumes": [
            finding(
                "route",
                "Harness route",
                f"Old R24 route in A1 sleeve gives {r['space']['old_R24_harness_min_in_new_sleeve_mm']:.3f}mm clearance: fail. R21 route gives {r['space']['routed_R21_harness_min_in_sleeve_mm']:.3f}mm after0.7mm losses; sector bound {r['space']['angular_gap_between_legs_and_inner_doublers_deg']:.3f}deg. Connector/chafe access remains unknown.",
                "calculated",
            ),
            finding(
                "removal",
                "Motor and module removal",
                "Motor+liner R15.8,z1069–1195; retainer R23,z1195–1227. Upper bolts end102mm ahead. Module needs40.5mm translation;100mm extra harness slack mass counted. Storyboard only.",
                "estimated",
            ),
        ],
        "mass": {
            "net_delta": value(
                r["net_delta_from_A_g"],
                "g",
                "All changes versus frozen A, not C1; separate50g retained",
                "calculated",
            ),
            "ledger_rows": [
                finding(
                    row["id"],
                    row["id"],
                    f"{row['mass_delta_g']:+.6f}g atz{row['station_mm']:.3f}mm. {row['function']}. {row['basis']}",
                    "estimated",
                )
                for row in r["replacement_ledger"]
            ],
            "note": "Signed removals/additions use one ledger for mass and balance; source service/finish/thermal/guide allocations remain unless named removed.",
        },
        "joint_detail": {
            "radial_stack": [
                {"label": label, "thickness_mm": thickness, "source_ids": src}
                for label, thickness in [
                    ("Outer washer", 1),
                    ("G11 collar", 2),
                    ("Collar adhesive", 0.2),
                    ("Can wall", 0.8),
                    ("Fitted gap spacer", 0.5),
                    ("G11 sleeve", 1),
                    ("Inner G11 doubler", 2),
                    ("Inner washer", 1),
                    ("Full nut", 4),
                ]
            ],
            "total_to_nut_end_mm": r["hardware_stack"]["nominal_grip_plus_nut_mm"],
            "maximum_to_nut_end_mm": r["hardware_stack"]["declared_max_mm"],
            "bolt_length_mm": 16,
            "minimum_protrusion_mm": r["hardware_stack"]["minimum_thread_protrusion_mm"],
            "hole_diameter_mm": 5.4,
            "upper_bond": {"length_mm": 76, "radial_gap_mm": 0.8, "paper_wall_mm": 0.5},
            "root": {
                "edge_patch_mm": [100, 8.98],
                "fillet_leg_mm": 3,
                "normal_outer_n": r["section_demands"]["root_outer_reaction_N"],
                "normal_inner_n": r["section_demands"]["root_inner_reaction_N"],
                "normal_peel_mpa": r["section_demands"]["root_outer_normal_demand_pa"] / 1e6,
                "toe_z_mm": [1073.5, 1090],
                "heel_z_mm": [1190, 1190.5],
                "stop_radial_tangential_mm": [15, 8.98],
            },
            "note": "Concept stack/demands. Source-config nominal dimensions, not selected bolt SKU, installed capacity or qualified preload. No rigid ground or equal sharing.",
            "source_ids": src,
        },
        "cases": cases,
        "findings": [
            {
                "id": "seat_liner_overlap",
                "label": "Thrust seat intersects retained thermal barrier",
                "state": "failed",
                "note": "Declared coaxial annuli overlap atz1193–1195: micaR14.7–15.1 and foilR15.1–15.12 both intersect proposed seatR14.6–17.2. Liner/foil endz1200. No trimming, motor shift, mass or thermal correction was adopted.",
                "source_ids": ["a1_occupancy"],
            },
            finding(
                "bolt",
                "Combined radial-bolt screen failed",
                "463.661MPa conservative single-lap bending/shear proxy exceeds200MPa hot-steel estimate. Changing load sharing or using shear-only is not a pass.",
                "failed",
            ),
            finding(
                "mass",
                "Baseline guide mass failed",
                "Nominal/adverse full totals1074.762/1094.762g. Formal deficits116.364/136.364g; planning170.908/190.908g under saved reference assumptions.",
                "failed",
            ),
            finding(
                "materials",
                "Unqualified finished joints",
                "G11 bearing, shear-out, bond peeling and paper wall capacity unavailable; typical laminate properties do not establish them.",
            ),
            finding(
                "thermal",
                "Required heat cases remain open",
                "No new temperature solve.45C substrate screen;300C case+contaminated foil+35C ambient burn/soak preserved. Current polymer motor material needs matching boundary evidence.",
            ),
            finding(
                "next",
                "Next bounded decision",
                "No detailed CAD/FEA or next automatic bracket. Decide a recovery-force path bypassing the service bolts, keeping the full required recovery load in defined harness/anchors; resolve mass/actual guide evidence separately.",
                "estimated",
            ),
        ],
    }
