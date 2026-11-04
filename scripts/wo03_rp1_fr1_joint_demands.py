"""Complete face-area/aft-route accounting from the frozen FR1 preflight only."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path


def main():
    start = time.process_time()
    root = Path(__file__).resolve().parents[1]
    source = root / "runs/wo03-rp1-fin-root-20261104-v1/record.json"
    target = source.parent / "joint-supplement.json"
    if target.exists():
        raise ValueError("Preserve one completed supplement")
    r = json.loads(source.read_text())
    rows = [case for prop in r["structural_sensitivity"] for case in prop["finite_roots"]]
    body = max(abs(c["body_reaction_N"]) for c in rows)
    mount = max(abs(c["mount_reaction_N"]) for c in rows)
    body_area, mount_area = (0.13 - 0.0001) * 0.0058, (0.1094 - 0.0001) * 0.0058
    radial = 0.017451 - 0.0001
    thickness = 0.002921
    area = thickness * radial
    tau = 1e6
    # A rectangular bond in elastic pure rotation has tau proportional to radius.
    elastic_moment = tau * thickness * radial**2 / 6
    # A separate maximum same-direction shear traction gives this inner-edge moment.
    full_traction_moment = tau * thickness * radial**2 / 2
    result = {
        "identity": r["identity"],
        "source": str(source.relative_to(root)),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "decision": "No admission; complete route strength/stiffness not established",
        "corrected_area_scope": "Record used109.4mm overlap area for bodyface as conservative subregion; actual bodyroot length130mm shown separately here. No beam/guide cases repeated.",
        "body_one_face_area_mm2": body_area * 1e6,
        "body_single_face_mean_shear_Pa": body / body_area,
        "body_70percent_face_mean_Pa": 0.7 * body / body_area,
        "body_equal_share_mean_Pa_diagnostic_only": 0.5 * body / body_area,
        "body_single_face_screen_pass": body / body_area <= tau,
        "required_body_leg_mm_for_mean1MPa": body / (0.1299 * tau) * 1000,
        "mount_single_face_mean_shear_Pa": mount / mount_area,
        "aft_tab_end": {
            "area_mm2": area * 1e6,
            "filled_gap_nominal_mm": 0.4,
            "provisional_gap_bounds_mm": [0.25, 0.55],
            "direct_butt_contact": False,
            "mean_shear_force_screen_N": tau * area,
            "elastic_pure_moment_screen_Nm": elastic_moment,
            "one_direction_traction_inner_edge_moment_bound_Nm": full_traction_moment,
            "illustrative_G_Pa_not_sourced": 1e8,
            "illustrative_rigid_ring_K_Nm_rad": 1e8 * thickness * radial**3 / (12 * 0.0004),
            "qualified_capacity_or_stiffness": None,
            "scope": "Shear-area and elastic-section demands only; actual annular ring/peel/wood stiffness and load partition unknown. No rigid aft-ring support credited.",
        },
        "complete_installed_movement": None,
        "finite_sensitivity_scope": "Short-tab model has no credited extra aft-end rotational restraint; unqualified missing route could change movement. Failed sensitivities do not establish physical impossibility or a complete installed displacement prediction.",
        "strength_qualification": None,
        "resources": {
            "cpu_seconds": time.process_time() - start,
            "new_beam_or_guide_runs": 0,
            "new_CAD_or_FEA": 0,
        },
    }
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
