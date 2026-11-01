"""Staged parametric keeper-service geometry; dimensions come from owning part spec."""

import math

import cadquery as cq


def build(part, base_factory):
    p = part.cad.parameters
    r = p["service_recipe_mm"]
    kind = p["service_kind"]
    index = int(p.get("service_index", 0))

    def cyl(rad, z, h, x=0.0, y=0.0):
        return cq.Solid.makeCylinder(rad, h, cq.Vector(x, y, z))

    def box(x, y, z, z0):
        return (
            cq.Workplane("XY")
            .box(x, y, z, centered=(True, True, False))
            .val()
            .translate((0, 0, z0))
        )

    def rot(shape, angle):
        return shape.rotate((0, 0, 0), (0, 0, 1), angle)

    def ann(ro, ri, z, h, eps):
        return cyl(ro, z, h).cut(cyl(ri, z - eps, h + 2 * eps))

    def point(radius, angle):
        return radius * math.cos(math.radians(angle)), radius * math.sin(math.radians(angle))

    def hexagon(af, z, h, x, y):
        return (
            cq.Workplane("XY")
            .polygon(6, af / math.cos(math.pi / 6))
            .extrude(h)
            .val()
            .translate((x, y, z))
        )

    ro, ri = r["outer_radius"], r["inner_radius"]
    railangles = r["rail_angles_deg"]
    bolts = r["bolt_angles_deg"]
    m2angles = r["m2_angles_deg"]
    ext = r["boolean_extension_mm"]
    kext = r["keeper_boolean_extension_mm"]
    if kind == "mount":
        q = part.model_copy(deep=True)
        q.cad.generator = "mount"
        shape = base_factory(q)
        x, y, z, z0, rad = r["old_block_cutter"]
        for a in bolts:
            shape = shape.cut(rot(box(x, y, z, z0).translate((rad, 0, 0)), a))
        inner, outer, width, height, z0 = r["relief"]
        for a in bolts:
            shape = shape.cut(
                rot(box(outer - inner, width, height, z0).translate(((inner + outer) / 2, 0, 0)), a)
            )
        band = ann(ro, ri, r["ring_band_z"], r["ring_band_height"], kext)
        removal = shape.intersect(band)
        for a in railangles:
            removal = removal.cut(
                rot(box(*r["rail_envelope"], 0).translate((r["rail_radius"], 0, 0)), a)
            )
        return shape.cut(removal)
    if kind == "guide":
        x, y, z, z0, rad, bore, bz, bh, cz, ch = r["guide"]
        shape = box(x, y, z, z0).translate((rad, 0, 0)).cut(cyl(bore, bz, bh, rad, 0))
        return rot(shape.intersect(cyl(ro, cz, ch)), bolts[index])
    if kind == "bridge":
        z, h, nrad, nx, ny, nz, nz0, bore, brad, tx, ty, tz, tz0, trad, tside, cz, ch = r["bridge"]
        shape = ann(ro, ri, z, h, ext)
        for a in railangles:
            shape = shape.cut(rot(box(nx, ny, nz, nz0).translate((nrad, 0, 0)), a))
        for a in bolts:
            x, y = point(brad, a)
            shape = shape.cut(cyl(bore, nz0, nz, x, y))
        for a in railangles:
            for side in (-1, 1):
                shape = shape.fuse(
                    rot(
                        box(tx, ty, tz, tz0)
                        .translate((trad, side * tside, 0))
                        .intersect(cyl(ro, cz, ch)),
                        a,
                    )
                )
        cr, cb, cz0, ch0, bz, bh, *_ = r["closure"]
        for a in m2angles:
            x, y = point(cr, a)
            shape = shape.cut(cyl(cb, bz, bh, x, y))
        return shape.clean()
    if kind == "keeper":
        z, h, nrad, nx, ny, nz, nz0, brad, wr, wz, wh, af, hz, hh, borer, bz, bh, corner = r[
            "keeper"
        ]
        shape = ann(ro, ri, z, h, kext)
        for a in railangles:
            shape = shape.cut(rot(box(nx, ny, nz, nz0).translate((nrad, 0, 0)), a))
        for a in bolts:
            x, y = point(brad, a)
            shape = (
                shape.cut(cyl(wr, wz, wh, x, y))
                .cut(hexagon(af, hz, hh, x, y))
                .cut(cyl(borer, bz, bh, x, y))
            )
            dist = af / math.sqrt(3)
            for angle in range(0, 360, 60):
                dx, dy = point(dist, angle)
                shape = shape.cut(cyl(corner, hz, hh, x + dx, y + dy))
        cr, cb, cz0, ch0, bz, bh, pro, pri, pz, ph = r["closure"]
        for a in m2angles:
            x, y = point(cr, a)
            shape = shape.cut(cyl(cb, cz0, ch0, x, y))
            shape = shape.fuse(ann(pro, pri, pz, ph, kext).translate((x, y, 0)))
        return shape.clean()
    if kind.startswith("m3_"):
        x, y = point(r["bridge"][8], bolts[index])
        if kind == "m3_washer":
            a, b, z, h = r[kind]
            return ann(a, b, z, h, ext).translate((x, y, 0))
        if kind == "m3_nut":
            af, z, h, br, bz, bh = r[kind]
            return hexagon(af, z, h, x, y).cut(cyl(br, bz, bh, x, y))
        if kind == "m3_screw":
            rad, z, h, hr, hz, hh = r[kind]
            return cyl(rad, z, h, x, y).fuse(cyl(hr, hz, hh, x, y))
    if kind.startswith("m2_"):
        x, y = point(r["closure"][0], m2angles[index])
        if kind == "m2_nut":
            af, z, h, br, bz, bh = r[kind]
            return hexagon(af, z, h, x, y).cut(cyl(br, bz, bh, x, y))
        if kind == "m2_screw":
            rad, z, h, hr, hz, hh = r[kind]
            return cyl(rad, z, h, x, y).fuse(cyl(hr, hz, hh, x, y))
    raise ValueError(f"Unknown service kind {kind}")
