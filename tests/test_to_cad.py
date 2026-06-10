from pipeline.to_cad import box_obj, write_obj


def test_box_obj_has_8_vertices_named_group():
    text, nverts = box_obj("car_01", center=(0, 0, 0.75), size=(4.5, 1.8, 1.5), voffset=0)
    assert text.startswith("o car_01")
    assert text.count("\nv ") == 8
    assert nverts == 8


def test_write_obj_offsets_face_indices(tmp_path):
    objs = [
        {"name": "car_01", "kind": "box", "center": (0, 0, 0.75), "size": (4.5, 1.8, 1.5)},
        {"name": "car_02", "kind": "box", "center": (10, 0, 0.75), "size": (4.5, 1.8, 1.5)},
    ]
    p = tmp_path / "scene.obj"
    write_obj(str(p), objs)
    body = p.read_text()
    assert body.count("o car_") == 2
    assert " 9 " in body  # second box references vertices 9..16
