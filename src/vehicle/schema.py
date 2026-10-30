"""SI vehicle contract; axial stations increase aft from the nose tip.

This station coordinate is opposite body +x (noseward); see sim.frames.
Part positions are absolute, while parent identifies assembly membership only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.vehicle.geometry import shape_properties


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, allow_inf_nan=False)


class Evidence(Model):
    cite: str | None = None
    estimate: bool = False

    @model_validator(mode="after")
    def provenance(self) -> Self:
        if not self.cite and not self.estimate:
            raise ValueError("provide a citation or mark estimate: true")
        return self


class Tank(Evidence):
    volume_m3: float = Field(gt=0)
    propellant: str
    fill_fraction: float = Field(ge=0, le=1)
    ullage_pressure_pa: float = Field(gt=0)
    wall_material: str
    wall_m: float = Field(gt=0)


Positive = Annotated[float, Field(gt=0)]
Nonnegative = Annotated[float, Field(ge=0)]


class Geometry(Model):
    bbox_m: tuple[Positive, Positive, Positive] | None = None
    length_m: Positive | None = None
    radius_m: Positive | None = None
    inner_radius_m: Nonnegative = 0
    fore_radius_m: Nonnegative | None = None
    wall_m: Positive | None = None
    shape: Literal["ogive", "conical", "elliptical"] | None = None
    shoulder_length_m: Nonnegative = 0
    od_m: Positive | None = None
    id_m: Positive | None = None
    diameter_m: Positive | None = None
    outer_ring_od_m: Positive | None = None
    inner_ring_id_m: Positive | None = None
    max_deflection_rad: Positive | None = None
    retention: str | None = None
    sled: bool | None = None
    type: str | None = None
    count: int | None = Field(default=None, gt=0)
    span_m: Positive | None = None
    root_chord_m: Positive | None = None
    tip_chord_m: Positive | None = None
    sweep_m: Nonnegative | None = None
    thickness_m: Positive | None = None

    @model_validator(mode="after")
    def dimensions(self) -> Self:
        if self.span_m is not None:
            if (
                self.bbox_m is not None
                or self.count is None
                or self.count < 3
                or self.root_chord_m is None
                or self.tip_chord_m is None
                or self.sweep_m is None
                or self.thickness_m is None
                or self.radius_m is None
                or self.length_m is None
            ):
                raise ValueError(
                    "fin set requires count, chords, span, sweep, thickness and body radius"
                )
            if abs(self.length_m - max(self.root_chord_m, self.sweep_m + self.tip_chord_m)) > 1e-9:
                raise ValueError("fin length must bound both root and swept tip")
            return self
        if self.bbox_m is not None:
            if self.length_m is not None or self.radius_m is not None:
                raise ValueError("choose box or axisymmetric geometry, not both")
            return self
        if self.length_m is None or self.radius_m is None:
            raise ValueError("axisymmetric geometry needs length_m and radius_m")
        if self.inner_radius_m >= self.radius_m:
            raise ValueError("inner radius must be below outer radius")
        if self.wall_m is not None and self.wall_m >= self.radius_m:
            raise ValueError("wall thickness exceeds radius")
        if self.od_m is not None and abs(self.od_m - 2 * self.radius_m) > 1e-9:
            raise ValueError("od_m disagrees with radius_m")
        if self.diameter_m is not None and abs(self.diameter_m - 2 * self.radius_m) > 1e-9:
            raise ValueError("diameter_m disagrees with radius_m")
        if self.id_m is not None and self.id_m >= 2 * self.radius_m:
            raise ValueError("inner diameter exceeds outer diameter")
        return self


class Electrical(Model):
    supply_v: Positive | None = None
    current_a: Positive | None = None
    nominal_v: Positive | None = None
    capacity_mah: Positive | None = None
    max_discharge_a: Positive | None = None
    bus: Literal["SPI", "I2C"] | None = None
    stall_torque_nm: Positive | None = None
    speed_s_per_60deg: Positive | None = None
    deadband_us: Nonnegative | None = None
    stall_current_a: Positive | None = None


class PrintSettings(Model):
    line_width_mm: Positive | None = None
    orientation: str
    layer_mm: Positive
    infill_pct: float = Field(ge=0, le=100)
    walls: int = Field(gt=0)
    supports: bool


class NoseDescription(Model):
    shape: Literal["ogive", "conical", "elliptical"]
    length_m: Positive


class Airframe(Model):
    body_diameter_m: Positive
    length_m: Positive
    nose: NoseDescription
    material_default: str


class PassiveStubs(Model):
    enabled: bool
    span_m: Positive
    count: int = Field(ge=3, le=8)
    root_chord_m: Positive
    tip_chord_m: Positive
    sweep_m: Nonnegative
    position_m: Nonnegative


class DragTable(Evidence):
    type: Literal["empirical_mach_table"]
    reference: str
    mach: list[Nonnegative] = Field(min_length=2)
    cd: list[Positive] = Field(min_length=2)
    base_drag_cd: Nonnegative

    @model_validator(mode="after")
    def table(self) -> Self:
        if len(self.mach) != len(self.cd) or any(a >= b for a, b in zip(self.mach, self.mach[1:])):
            raise ValueError("drag table requires equal lengths and strictly increasing Mach")
        if self.mach[0] != 0 or self.mach[-1] < 0.8:
            raise ValueError("drag table must cover Mach 0 through 0.8")
        return self


class Aero(Model):
    passive_stubs: PassiveStubs
    cd_model: DragTable


class TVC(Model):
    axes: Literal[2]
    max_deflection_rad: float = Field(gt=0, lt=1.5708)
    pivot_position_m: Nonnegative
    servo_ids: tuple[str, str]
    linkage_ratio: Positive

    @model_validator(mode="after")
    def independent_servos(self) -> Self:
        if self.servo_ids[0] == self.servo_ids[1]:
            raise ValueError("gimbal axes require distinct servos")
        return self


class Sensor(Model):
    part: str
    rate_hz: Positive
    accel_range_g: Positive | None = None
    gyro_range_dps: Positive | None = None


class AbortAction(Model):
    gimbal: Literal["centre"]
    recovery: Literal["arm"]


class Abort(Model):
    max_tilt_rad: float = Field(gt=0, lt=3.1416)
    max_rate_rad_s: Positive
    sensor_dropout_ms: Positive
    servo_fault_ms: Positive
    action_on_abort: AbortAction


class Avionics(Model):
    loop_rate_hz: Positive
    physics_rate_hz: Positive
    estimator: Literal["madgwick", "complementary"]
    sensors: dict[str, Sensor]
    abort: Abort

    @model_validator(mode="after")
    def timing(self) -> Self:
        ratio = self.physics_rate_hz / self.loop_rate_hz
        if ratio < 1 or abs(ratio - round(ratio)) > 1e-9:
            raise ValueError("physics rate must be an integer multiple of control rate")
        return self


class Build(Model):
    method: Literal["purchased", "printed", "cut", "bonded", "assembled"]
    cost_usd: Nonnegative
    generator: str
    notes: str


class DesignRequirements(Model):
    mode: Literal["performance", "tvc_finned", "tvc_finless"]
    mass_allowance_kg: Nonnegative
    rail_length_m: Positive
    minimum_rail_exit_mps: Positive
    screening_wind_mps: Nonnegative
    rail_friction_n: Nonnegative
    drag_coefficient_upper: Positive
    thrust_scale_lower: float = Field(gt=0, le=1)
    minimum_static_margin_cal: Nonnegative | None = None
    minimum_control_time_s: Nonnegative = 0
    target_control_time_s: Nonnegative = 0
    control_thrust_to_weight: float = Field(default=1.2, gt=1)
    provenance: str


class MotorQualification(Model):
    certified_impulse_ns: float = Field(gt=0, le=160)
    certified_average_thrust_n: float = Field(gt=0, le=80)
    motor_type: Literal["commercial_solid_nonsparky"]
    source: str
    exact_hardware_verified: bool = False
    california_verified: bool = False


class Part(Evidence):
    id: str
    type: Literal[
        "nose_cone",
        "body_tube",
        "avionics_bay",
        "commercial",
        "recovery",
        "tvc_gimbal",
        "servo",
        "motor_mount",
        "motor",
        "rail_guide",
        "transition",
        "fin_set",
    ]
    parent: str | None
    position_m: float = Field(ge=0)
    lateral_offset_m: tuple[float, float] = (0.0, 0.0)
    geometry: dict[str, Any]
    material: str = "commercial"
    mass_kg: Positive | None = None
    density_kg_m3: Positive | None = None
    cg_offset_m: Nonnegative | None = None
    electrical: Electrical | None = None
    print_settings: PrintSettings | None = Field(default=None, alias="print")
    explode_offset: float = 0
    learn: str = Field(min_length=30)
    tank: Tank | None = None
    engine: str | None = None
    build: Build | None = None

    @model_validator(mode="after")
    def geometry_check(self) -> Self:
        g = Geometry.model_validate(self.geometry)
        self.geometry = g.model_dump(exclude_none=True, exclude_defaults=True)
        if (self.type == "fin_set") != (g.span_m is not None):
            raise ValueError("fin geometry must belong to a fin_set part")
        if (self.mass_kg is None) == (self.density_kg_m3 is None):
            raise ValueError("provide exactly one of mass_kg or density_kg_m3")
        if self.type == "nose_cone" and (g.shape is None or g.length_m is None):
            raise ValueError("nose requires axisymmetric geometry and supported shape")
        if self.type == "transition" and g.fore_radius_m is None:
            raise ValueError("transition requires fore_radius_m")
        if self.type == "body_tube" and g.wall_m is not None:
            assert g.radius_m is not None
            if abs(g.inner_radius_m - (g.radius_m - g.wall_m)) > 1e-9:
                raise ValueError("tube wall disagrees with inner radius")
        length = g.bbox_m[0] if g.bbox_m else g.length_m
        assert length is not None
        if self.cg_offset_m is not None and self.cg_offset_m > length:
            raise ValueError("CG offset exceeds part length")
        # Shape integration provides volume/centroid only when the spec requests it.
        if self.density_kg_m3 is not None:
            shape_properties(self.type, self.geometry)
        if self.cg_offset_m is None:
            self.cg_offset_m = shape_properties(self.type, self.geometry).cg_offset_m
        return self

    @property
    def resolved_mass_kg(self) -> float:
        if self.mass_kg is not None:
            return self.mass_kg
        assert self.density_kg_m3 is not None
        return shape_properties(self.type, self.geometry).volume_m3 * self.density_kg_m3

    @property
    def cg_station_m(self) -> float:
        assert self.cg_offset_m is not None
        return self.position_m + self.cg_offset_m


class Limits(Model):
    max_liftoff_mass_kg: float = Field(default=1.5, gt=0, le=1.5)
    max_propellant_kg: float = Field(default=0.125, gt=0, le=0.125)
    max_total_impulse_ns: float = Field(default=320, gt=0, le=320)
    metal_structure_allowed: Literal[False] = False


class Motor(Evidence):
    id: str
    curve: str | None = None
    propellant_mass_kg: float = Field(gt=0)
    casing_mass_kg: float = Field(gt=0)
    mount_position_m: float = Field(ge=0)
    burn_time_s: float = Field(gt=0)
    total_impulse_ns: float = Field(gt=0)
    average_thrust_n: float = Field(gt=0)
    ignition_delay_s: float = Field(default=0, ge=0)
    thrust_scale_range: tuple[float, float] = (0.85, 1.15)
    qualification: MotorQualification | None = None

    @model_validator(mode="after")
    def thrust_range(self) -> Self:
        if not 0 < self.thrust_scale_range[0] <= self.thrust_scale_range[1]:
            raise ValueError("invalid thrust scale interval")
        return self


class Stage(Model):
    id: str
    name: str
    parts: list[str] = Field(default_factory=list)
    engine: str | None = None
    tanks: list[Tank] = Field(default_factory=list)
    reusable: bool = False


class Event(Model):
    name: str
    trigger: dict[str, Any]
    params: dict[str, Any] = Field(default_factory=dict)


class Net(Model):
    net: str
    source: str = Field(alias="from")
    to: str | list[str]
    gauge_awg: int | None = Field(default=None, gt=0)
    pin: str | int | None = None


class Recovery(Evidence):
    canopy_diameter_m: Positive
    drag_coefficient: float = Field(gt=0, le=2.0)
    trigger: Literal["independent_electronic_apogee"]
    trigger_lag_s: Nonnegative
    inflation_s: Positive
    independent_recovery_part: str


class Vehicle(Model):
    id: str
    name: str
    vehicle_class: Literal["model_rocket", "digital_only"] = Field(alias="class")
    scale: Literal["model", "full"]
    axis: dict[str, str]
    limits: Limits | None = None
    airframe: dict[str, Any]
    aero: Aero
    motor: Motor | None = None
    tvc: TVC | None = None
    avionics: Avionics | None = None
    parts: list[Part] = Field(min_length=1)
    stages: list[Stage] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    netlist: list[Net] = Field(default_factory=list)
    design: DesignRequirements | None = None
    recovery: Recovery | None = None

    @field_validator("airframe")
    @classmethod
    def airframe_dimensions(cls, value: dict[str, Any]) -> dict[str, Any]:
        return Airframe.model_validate(value).model_dump()

    @model_validator(mode="after")
    def assembly(self) -> Self:
        if (self.scale == "model") != (self.vehicle_class == "model_rocket"):
            raise ValueError("model scale requires model_rocket class")
        if self.airframe.get("length_m", 0) <= 0 or self.airframe.get("body_diameter_m", 0) <= 0:
            raise ValueError("airframe length and diameter must be positive")
        ids = {p.id for p in self.parts}
        if len(ids) != len(self.parts):
            raise ValueError("duplicate part IDs")
        parents = {p.id: p.parent for p in self.parts}
        for part in self.parts:
            visited: set[str] = set()
            node: str | None = part.id
            while node is not None:
                if node not in parents or node in visited:
                    raise ValueError("missing parent or cycle in parts tree")
                visited.add(node)
                node = parents[node]
            length = part.geometry.get("length_m", part.geometry.get("bbox_m", [0])[0])
            if part.position_m + length > self.airframe["length_m"] + 1e-9:
                raise ValueError(f"part {part.id} extends beyond vehicle")
        if sum(p.parent is None for p in self.parts) != 1:
            raise ValueError("parts tree must have one root")
        if self.recovery and self.recovery.independent_recovery_part not in ids:
            raise ValueError("unknown independent recovery hardware")
        for net in self.netlist:
            targets = [net.to] if isinstance(net.to, str) else net.to
            if not {net.source, *targets} <= ids:
                raise ValueError(f"unknown part in net {net.net}")
        for stage in self.stages:
            if not set(stage.parts) <= ids:
                raise ValueError("unknown stage part")
        if self.tvc and not set(self.tvc.servo_ids) <= ids:
            raise ValueError("unknown TVC servo")
        if self.tvc:
            if self.tvc.pivot_position_m > self.airframe["length_m"]:
                raise ValueError("TVC pivot outside vehicle")
            by_id = {p.id: p for p in self.parts}
            if any(by_id[pid].type != "servo" for pid in self.tvc.servo_ids):
                raise ValueError("TVC references must identify servo parts")
        if self.avionics and any(
            sensor.part not in ids for sensor in self.avionics.sensors.values()
        ):
            raise ValueError("unknown sensor part")
        noses = [p for p in self.parts if p.type == "nose_cone"]
        if len(noses) != 1:
            raise ValueError("vehicle requires exactly one nose cone")
        nose = noses[0]
        if (
            nose.geometry["shape"] != self.airframe["nose"]["shape"]
            or abs(nose.geometry["length_m"] - self.airframe["nose"]["length_m"]) > 1e-9
        ):
            raise ValueError("airframe nose description disagrees with nose part")
        stubs = self.aero.passive_stubs
        fin_sets = [p for p in self.parts if p.type == "fin_set"]
        if fin_sets and stubs.enabled:
            raise ValueError("physical fins and legacy aerodynamic stubs cannot both be enabled")
        if any(
            abs(p.geometry["radius_m"] * 2 - self.airframe["body_diameter_m"]) > 1e-9
            for p in fin_sets
        ):
            raise ValueError("fin root radius disagrees with body")
        if self.design:
            if self.scale != "model" or self.limits is None:
                raise ValueError("physical design profile requires model scale and limits")
            if self.motor is None or self.motor.qualification is None:
                raise ValueError("rebaselined model requires explicit motor qualification evidence")
            if self.motor.total_impulse_ns > 160:
                raise ValueError("single motor exceeds G impulse ceiling")
            if self.design.mode == "performance" and (self.tvc is not None or not fin_sets):
                raise ValueError("performance mode requires physical fins and a fixed motor")
            if self.design.mode.startswith("tvc") and self.tvc is None:
                raise ValueError("TVC mode requires a TVC assembly")
            if self.design.mode == "tvc_finned" and not fin_sets:
                raise ValueError("finned TVC mode requires physical fins")
            if self.design.mode == "tvc_finless" and (fin_sets or stubs.enabled):
                raise ValueError("finless mode cannot contain aerodynamic fins")
            if self.design.mode != "performance" and self.design.minimum_control_time_s <= 0:
                raise ValueError("TVC requires a positive useful-control-time requirement")
            if (
                sum(p.resolved_mass_kg for p in self.parts) + self.design.mass_allowance_kg
                >= self.limits.max_liftoff_mass_kg
            ):
                raise ValueError("design with allowance must remain below the loaded-mass cap")
        if stubs.position_m + stubs.root_chord_m > self.airframe["length_m"]:
            raise ValueError("stub geometry extends beyond vehicle")
        if self.axis != {
            "body_x": "nose",
            "body_z": "down",
            "world": "NED" if self.scale == "model" else "ECI",
        }:
            raise ValueError("axis conventions disagree with vehicle scale")
        if self.scale == "model":
            if self.limits is None or self.motor is None:
                raise ValueError("model vehicle requires limits and motor")
            if sum(p.resolved_mass_kg for p in self.parts) > self.limits.max_liftoff_mass_kg:
                raise ValueError("liftoff mass exceeds model limit")
            if self.motor.propellant_mass_kg > self.limits.max_propellant_kg:
                raise ValueError("propellant mass exceeds model limit")
            if self.motor.total_impulse_ns > self.limits.max_total_impulse_ns:
                raise ValueError("impulse exceeds model limit")
            structural = {
                "nose_cone",
                "body_tube",
                "tvc_gimbal",
                "motor_mount",
                "transition",
                "fin_set",
            }
            if any(
                p.material
                not in {
                    "PETG",
                    "PLA",
                    "nylon",
                    "cardboard",
                    "ASA",
                    "plywood",
                    "fiberglass",
                    "phenolic",
                }
                for p in self.parts
                if p.type in structural
            ):
                raise ValueError("model structural material must be nonmetallic")
            motors = [p for p in self.parts if p.type == "motor"]
            if len(motors) != 1:
                raise ValueError("model requires exactly one motor part")
            expected = self.motor.propellant_mass_kg + self.motor.casing_mass_kg
            if abs(motors[0].resolved_mass_kg - expected) > 1e-9:
                raise ValueError("motor part mass must equal casing plus propellant")
            if abs(motors[0].position_m - self.motor.mount_position_m) > 1e-9:
                raise ValueError("motor station disagrees with mount")
        return self


def load_vehicle(path: str | Path) -> Vehicle:
    return Vehicle.model_validate(load_vehicle_data(path))


def load_vehicle_data(path: str | Path) -> dict[str, Any]:
    """Resolve one shared upper assembly and explicit mode-specific aft parts.

    No hidden geometry switches: each resolved vehicle contains every actual part.
    Shared files cannot inherit recursively or override mode parts by ID.
    """
    path = Path(path)
    data: dict[str, Any] = yaml.safe_load(path.read_text())
    shared = data.pop("shared", None)
    if shared:
        common = yaml.safe_load((path.parent / shared).read_text())
        if "shared" in common:
            raise ValueError("recursive shared assemblies are not supported")
        common_parts = common.pop("parts")
        data["parts"] = common_parts + data.get("parts", [])
        data = {**common, **data}
    return data


def vehicle_input_paths(path: str | Path) -> list[Path]:
    path = Path(path)
    raw = yaml.safe_load(path.read_text())
    return [path, *([path.parent / raw["shared"]] if raw.get("shared") else [])]
