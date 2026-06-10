_CUBE = [(-.5, -.5, -.5), (.5, -.5, -.5), (.5, .5, -.5), (-.5, .5, -.5),
         (-.5, -.5, .5), (.5, -.5, .5), (.5, .5, .5), (-.5, .5, .5)]
_FACES = [(1, 2, 3, 4), (5, 6, 7, 8), (1, 2, 6, 5),
          (2, 3, 7, 6), (3, 4, 8, 7), (4, 1, 5, 8)]


def box_obj(name, center, size, voffset):
    """OBJ text for one named box. voffset = vertices already written."""
    cx, cy, cz = center
    sx, sy, sz = size
    lines = [f"o {name}"]
    for ox, oy, oz in _CUBE:
        lines.append(f"v {cx + ox * sx:.4f} {cy + oy * sy:.4f} {cz + oz * sz:.4f}")
    for a, b, c, d in _FACES:
        lines.append(f"f {a + voffset} {b + voffset} {c + voffset} {d + voffset}")
    return "\n".join(lines) + "\n", 8


def write_obj(path, objects):
    """Write a multi-object OBJ. Each object: {name, kind:'box', center, size}."""
    chunks, voffset = [], 0
    for o in objects:
        if o["kind"] == "box":
            text, n = box_obj(o["name"], o["center"], o["size"], voffset)
            chunks.append(text)
            voffset += n
    open(path, "w").write("".join(chunks))


def cars_to_objects(car_boxes):
    objs = []
    for i, b in enumerate(car_boxes, 1):
        objs.append({"name": f"car_{i:02d}", "kind": "box",
                     "center": tuple(b["center"]),
                     "size": (b["length"], b["width"], b["height"])})
    return objs


def assets_to_objects(assets):
    objs = []
    for i, a in enumerate(assets, 1):
        h = max(a["height"], 0.3)
        objs.append({"name": f'{a["type"].lower()}_{i:02d}', "kind": "box",
                     "center": (a["x"], a["y"], a["ground_z"] + h / 2),
                     "size": (0.6, 0.6, h)})
    return objs


def write_dummy_scene(path="out/scene.obj"):
    """Two boxes so the APS round-trip can be tested before segmentation exists."""
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_obj(path, [
        {"name": "car_01", "kind": "box", "center": (0, 0, 0.75), "size": (4.5, 1.8, 1.5)},
        {"name": "car_02", "kind": "box", "center": (8, 0, 0.75), "size": (4.5, 1.8, 1.5)},
    ])
