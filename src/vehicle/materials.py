"""Nominal bulk densities in kg/m³; estimates, not measured printed density.

Print voids, wall count and infill need CAD-derived effective volumes in WO-03.
"""

DENSITY_KG_M3: dict[str, float] = {
    "PETG": 1270,
    "PLA": 1240,
    "nylon": 1140,
    "cardboard": 700,
    "ASA": 1070,
    "plywood": 550,
    "fiberglass": 1850,
    "phenolic": 1300,
}
