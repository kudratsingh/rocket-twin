"""Nominal bulk densities in kg/m³; estimates, not measured printed density.

Print voids, wall count and infill need CAD-derived effective volumes in WO-03.
"""

DENSITY_KG_M3: dict[str, float] = {
    "PETG": 1270,
    "PLA": 1240,
    "nylon": 1140,
    "cardboard": 700,
    "ASA": 1070,
    "plywood": 715,
    "fiberglass": 1850,
    "phenolic": 1300,
    "G11": 1850,  # Conservative density versus cited 1820 kg/m3 stock.
    "mica": 2100,
    "aluminum": 2700,  # Nonstructural radiant foil only in model configurations.
    "epoxy": 1200,  # Estimated cured adhesive; actual mix, fillers and voids require weighing.
}
