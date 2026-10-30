"""Tropospheric ISA and deterministic continuous wind uncertainty.

T=T0-Lh, p=p0*(T/T0)^(g/(R*L)); rho=p/(R*T), a=sqrt(gamma*R*T).
Altitude is MSL while trajectory positions are NED relative to the pad.
Scope is the troposphere and subsonic model rockets; excursions are flagged.
Wind combines a height power law with smooth bounded sinusoidal gusts. It is an
engineering disturbance, not a measured sounding or Dryden turbulence model.
References: US Standard Atmosphere 1976; Sutton & Biblarz, ch. 4.
Extension contracts: Atmosphere, Gravity, Wind from docs/EXTENSIONS.md.
"""

import jax.numpy as jnp
from jax import Array

from src.sim.frames import STANDARD_GRAVITY_M_S2 as G
from src.sim.types import Params


def atmosphere(height_msl: Array) -> tuple[Array, Array, Array]:
    temp = 288.15 - 0.0065 * jnp.clip(height_msl, -500, 11000)
    pressure = 101325 * (temp / 288.15) ** (G / (287.05287 * 0.0065))
    return pressure / (287.05287 * temp), jnp.sqrt(1.4 * 287.05287 * temp), pressure


def wind(t: Array, height_agl: Array, p: Params) -> Array:
    north, east, sigma, period, exponent = p.wind
    factor = (jnp.maximum(height_agl, 1) / 10) ** exponent
    phase = 2 * jnp.pi * t / jnp.maximum(period, 0.1)
    return jnp.array(
        [
            north * factor + sigma * jnp.sin(phase),
            east * factor + sigma * jnp.sin(phase * 1.37 + 0.7),
            0,
        ]
    )
