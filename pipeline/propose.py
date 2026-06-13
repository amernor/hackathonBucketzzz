import os

def write_mtl(mtl_path):
    mtl_content = """
newmtl proposed_amber
Kd 0.96 0.65 0.14
Ka 0.55 0.37 0.08
Ks 0.10 0.10 0.10
illum 2

newmtl proposed_concrete
Kd 0.92 0.92 0.92
Ka 0.55 0.55 0.55
Ks 0.05 0.05 0.05
illum 2

newmtl proposed_asphalt
Kd 0.22 0.22 0.24
Ka 0.10 0.10 0.11
illum 2
"""
    with open(mtl_path, 'w') as f:
        f.write(mtl_content)


def _parse_ground(baseline_lines):
    """Return (ground_verts, scene_cx, scene_cy). ground_verts are vertices that
    belong to the ground_* meshes — used to drape the repair onto the real surface."""
    ground = []
    allx, ally = [], []
    is_ground = False
    for line in baseline_lines:
        if line.startswith('o ') or line.startswith('g '):
            is_ground = line[2:].strip().lower().startswith('ground')
        elif line.startswith('v '):
            p = line.split()
            try:
                x, y, z = float(p[1]), float(p[2]), float(p[3])
            except (ValueError, IndexError):
                continue
            allx.append(x); ally.append(y)
            if is_ground:
                ground.append((x, y, z))
    if not allx:
        return [], 40.0, 40.0
    cx = (min(allx) + max(allx)) / 2.0
    cy = (min(ally) + max(ally)) / 2.0
    return ground, cx, cy


def _ground_z(ground, x, y):
    """Z of the nearest ground-mesh vertex to (x,y) — the real surface height there."""
    if not ground:
        return 0.0
    best, bz = 1e18, 0.0
    for gx, gy, gz in ground:
        d = (gx - x) ** 2 + (gy - y) ** 2
        if d < best:
            best, bz = d, gz
    return bz


def generate_proposed(location_id, repair_option_id, baseline_obj_path, output_path):
    if not os.path.exists(baseline_obj_path):
        print(f"Warning: {baseline_obj_path} not found. Creating blank baseline for demo.")
        with open(baseline_obj_path, 'w') as f:
            f.write("o Baseline\nv 0 0 0\n")

    with open(baseline_obj_path, 'r') as f:
        baseline_lines = f.readlines()

    out_dir = os.path.dirname(output_path)
    os.makedirs(out_dir, exist_ok=True)
    mtl_path = output_path.replace('.obj', '.mtl')
    write_mtl(mtl_path)
    mtl_filename = os.path.basename(mtl_path)

    ground, cx, cy = _parse_ground(baseline_lines)
    v_count = sum(1 for line in baseline_lines if line.startswith('v '))
    new_lines = [f"mtllib {mtl_filename}\n"]

    def slab(bx, by, sx, sy, thick, group, mat, lift=0.03):
        """Emit a thin slab that DRAPES onto the ground surface (each corner sits at
        the real ground height there), so it lies flush on the ramp instead of floating."""
        nonlocal v_count
        new_lines.append(f"g {group}\n")
        new_lines.append(f"usemtl {mat}\n")
        corners = [(bx-sx/2, by-sy/2), (bx+sx/2, by-sy/2), (bx+sx/2, by+sy/2), (bx-sx/2, by+sy/2)]
        zb = [_ground_z(ground, x, y) + lift for x, y in corners]      # bottom follows terrain
        for (x, y), z in zip(corners, zb):                            # 4 bottom verts
            new_lines.append(f"v {x:.3f} {y:.3f} {z:.3f}\n")
        for (x, y), z in zip(corners, zb):                            # 4 top verts
            new_lines.append(f"v {x:.3f} {y:.3f} {z+thick:.3f}\n")
        b = v_count
        for a, c, d, e in [(1,2,3,4),(5,6,7,8),(1,2,6,5),(2,3,7,6),(3,4,8,7),(4,1,5,8)]:
            new_lines.append(f"f {b+a} {b+c} {b+d} {b+e}\n")
        v_count += 8

    rid = repair_option_id
    has_ramp = any(k in rid for k in ('ramp', 'bumpout', 'upgrade', 'replacement'))
    has_strip = ('domes' in rid) or ('replacement' in rid)
    has_pave = any(k in rid for k in ('pavement', 'regrade', 'patch', 'relocate'))

    if has_pave:   # new asphalt patch draped over the corner
        slab(cx, cy, 6.0, 6.0, 0.06, "proposed_repaving", "proposed_asphalt")
    if has_ramp:   # reconstructed concrete ramp pad
        slab(cx, cy, 2.6, 2.6, 0.14, "proposed_ramp", "proposed_concrete")
        strip_y = cy - 1.4                       # warning strip at the ramp's road edge
    else:
        strip_y = cy
    if has_strip:  # amber detectable-warning (truncated dome) strip
        slab(cx, strip_y, 2.4, 0.7, 0.12, "proposed_warning_strip", "proposed_amber", lift=0.04)

    gz0 = _ground_z(ground, cx, cy)
    with open(output_path, 'w') as f:
        f.writelines(baseline_lines)
        f.write("\n")
        f.writelines(new_lines)
    print(f"Generated proposed model: {output_path} (draped at {cx:.1f},{cy:.1f}, ground z≈{gz0:.1f})")
