import os

def write_mtl(mtl_path):
    mtl_content = """
newmtl proposed_amber
Kd 0.96 0.65 0.14
illum 1

newmtl proposed_concrete
Kd 0.91 0.91 0.91
illum 1

newmtl proposed_asphalt
Kd 0.20 0.20 0.20
illum 1
"""
    with open(mtl_path, 'w') as f:
        f.write(mtl_content)

def generate_proposed(location_id, repair_option_id, baseline_obj_path, output_path):
    if not os.path.exists(baseline_obj_path):
        print(f"Warning: {baseline_obj_path} not found. Creating blank baseline for demo.")
        with open(baseline_obj_path, 'w') as f:
            f.write("o Baseline\n")

    with open(baseline_obj_path, 'r') as f:
        baseline_lines = f.readlines()

    out_dir = os.path.dirname(output_path)
    os.makedirs(out_dir, exist_ok=True)

    mtl_path = output_path.replace('.obj', '.mtl')
    write_mtl(mtl_path)
    mtl_filename = os.path.basename(mtl_path)

    v_count = sum(1 for line in baseline_lines if line.startswith('v '))

    new_lines = []
    new_lines.append(f"mtllib {mtl_filename}\n")

    if 'domes' in repair_option_id or 'replacement' in repair_option_id:
        new_lines.extend([
            "g proposed_warning_strip\n", "usemtl proposed_amber\n",
            "v 0.0 0.0 0.1\n", "v 1.2 0.0 0.1\n", "v 1.2 0.6 0.1\n", "v 0.0 0.6 0.1\n",
            f"f {v_count+1} {v_count+2} {v_count+3} {v_count+4}\n"
        ])
        v_count += 4

    if 'ramp' in repair_option_id or 'bumpout' in repair_option_id or 'upgrade' in repair_option_id:
        new_lines.extend([
            "g proposed_ramp_or_bumpout\n", "usemtl proposed_concrete\n",
            "v -1.0 -1.0 0.0\n", "v 2.0 -1.0 0.0\n", "v 2.0 1.0 0.2\n", "v -1.0 1.0 0.2\n",
            f"f {v_count+1} {v_count+2} {v_count+3} {v_count+4}\n"
        ])
        v_count += 4

    if 'pavement' in repair_option_id or 'regrade' in repair_option_id or 'patch' in repair_option_id or 'relocate' in repair_option_id:
        new_lines.extend([
            "g proposed_repaving\n", "usemtl proposed_asphalt\n",
            "v -2.0 -2.0 0.05\n", "v 3.0 -2.0 0.05\n", "v 3.0 2.0 0.05\n", "v -2.0 2.0 0.05\n",
            f"f {v_count+1} {v_count+2} {v_count+3} {v_count+4}\n"
        ])
        v_count += 4

    with open(output_path, 'w') as f:
        f.writelines(baseline_lines)
        f.write("\n")
        f.writelines(new_lines)
    print(f"Generated proposed model: {output_path}")
