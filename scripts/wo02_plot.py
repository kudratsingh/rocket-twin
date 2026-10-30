"""Plot recorded motor/wind trade results; no flight physics runs in this script."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="WO-02 record.json")
    parser.add_argument("--preset", choices=["tiny", "sim"], default="sim")
    parser.add_argument("--output", type=Path, default=Path("build/reports/wo02-flight-trade.png"))
    args = parser.parse_args()
    record = json.loads(args.config.read_text())
    base = [x for x in record["cases"] if "rocketpy" in x]
    labels = {
        "modular-performance-v1": "G80 fixed",
        "modular-tvc-finned-v1": "G12 TVC trainer",
        "modular-performance-g54-hypothesis": "G54 fixed",
        "modular-performance-g33-hypothesis": "G33 fixed",
        "modular-performance-g12-hypothesis": "G12 fixed / 3 m",
    }
    names = [labels[x["vehicle"]] for x in base]
    nominal = np.array([x["metrics"]["apogee_agl_m"] for x in base])
    lower = []
    upper = []
    for b in base:
        scenarios = {x.get("scenario"): x for x in record["cases"] if x["vehicle"] == b["vehicle"]}
        lower.append(scenarios["growth_low_thrust_high_drag"]["metrics"]["apogee_agl_m"])
        upper.append(scenarios["high_thrust_low_drag"]["metrics"]["apogee_agl_m"])
    fig = Figure(figsize=(10, 8), layout="constrained")
    FigureCanvasAgg(fig)
    axes = fig.subplots(2, 1)
    index = np.arange(len(base))
    axes[0].bar(index, nominal, color=["#377eb8", "#ff7f00", "#377eb8", "#377eb8", "#377eb8"])
    axes[0].errorbar(
        index,
        nominal,
        yerr=[nominal - np.array(lower), np.array(upper) - nominal],
        fmt="none",
        ecolor="black",
        capsize=5,
    )
    axes[0].set(
        ylabel="Predicted apogee AGL (m)",
        title="Calm nominal altitude and engineering sensitivity corners",
    )
    axes[0].set_xticks(index, names, rotation=10)
    axes[0].grid(axis="y", alpha=0.2)
    for label, scenario in [("Steady 1 m/s", "wind_1"), ("3 m/s + gust/profile", "wind_3_gust")]:
        values = [
            next(
                x["metrics"]["powered_max_tilt_deg"]
                for x in record["cases"]
                if x["vehicle"] == b["vehicle"] and x.get("scenario") == scenario
            )
            for b in base
        ]
        axes[1].plot(index, values, "o-", label=label)
    axes[1].set(
        ylabel="Maximum powered tilt (degrees)",
        title="Uncontrolled wind response: gimbal locked; no PID or RL",
    )
    axes[1].set_xticks(index, names, rotation=10)
    axes[1].legend()
    axes[1].grid(alpha=0.2)
    fig.suptitle(
        "WO-02 source hypotheses — estimates, not flight or launch qualification", fontsize=13
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    print(args.output)


if __name__ == "__main__":
    main()
