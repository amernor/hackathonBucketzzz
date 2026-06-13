import os, sys, re, json, subprocess, zipfile
from pipeline.propose import generate_proposed

# Use the existing, working aps/ modules (do not modify them). APS only runs
# when credentials are present; otherwise we emit mock URNs so the UI still demos.
try:
    from aps.auth import get_token
    from aps.upload import ensure_bucket, upload_object
    from aps.translate import start_translation, wait_until_done
    APS_AVAILABLE = bool(os.environ.get("APS_CLIENT_ID") and os.environ.get("APS_CLIENT_SECRET"))
except ImportError:
    APS_AVAILABLE = False

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, 'data')
OUT_DIR = os.path.join(ROOT, 'out')
os.makedirs(DATA_DIR, exist_ok=True); os.makedirs(OUT_DIR, exist_ok=True)
URNS_FILE = os.path.join(DATA_DIR, 'urns.json')
SCENE_OBJ = os.path.join(OUT_DIR, 'scene.obj')   # produced by the real run.py pipeline
SCENE_MTL = os.path.join(OUT_DIR, 'scene.mtl')

APS_BUCKET = os.environ.get("APS_BUCKET", "cyvl-hack-xavier")

# Locations whose baseline is the real Cyvl scene from run.py (the rest are mock).
# morrison_ave is the dense tile-center of the downloaded tile (ROI override unset).
REAL_BASELINE_IDS = {"morrison_ave"}


def load_urns():
    if os.path.exists(URNS_FILE):
        with open(URNS_FILE, 'r') as f: return json.load(f)
    return {}

def save_urn(key, urn):
    urns = load_urns(); urns[key] = urn
    with open(URNS_FILE, 'w') as f: json.dump(urns, f, indent=2)


def aps_upload_translate(file_path):
    """Upload an OBJ (zipped with its .mtl if present) and translate to SVF2. Returns URN."""
    token = get_token()
    ensure_bucket(token, APS_BUCKET)
    mtl_path = file_path[:-4] + ".mtl"
    obj_name = os.path.basename(file_path)
    if file_path.endswith(".obj") and os.path.exists(mtl_path):
        zip_path = file_path[:-4] + ".zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(file_path, obj_name)
            z.write(mtl_path, os.path.basename(mtl_path))
        key = os.path.basename(zip_path)
        urn = upload_object(token, APS_BUCKET, key, zip_path)
        start_translation(token, urn, root_filename=obj_name)
    else:
        key = obj_name
        urn = upload_object(token, APS_BUCKET, key, file_path)
        start_translation(token, urn)
    wait_until_done(token, urn)
    return urn


def build_real_baseline(loc_id):
    """Build (or reuse) the real Cyvl scene as this location's baseline. Returns URN or None.

    run.py is used only to GENERATE out/scene.obj; its own APS upload targets a
    hardcoded bucket the user may not own (403), so we ignore its exit/URN and
    upload the OBJ ourselves to APS_BUCKET.
    """
    if not APS_AVAILABLE:
        print(f"[{loc_id}] APS creds not set -> using mock baseline.")
        return None
    if not os.path.exists(SCENE_OBJ):
        if not os.environ.get("LAZ_DIR"):
            print(f"[{loc_id}] LAZ_DIR not set and out/scene.obj missing -> mock baseline.")
            return None
        print(f"[{loc_id}] Generating real Cyvl scene via run.py (a few minutes)...")
        proc = subprocess.run([sys.executable, "run.py"], cwd=ROOT,
                              capture_output=True, text=True)
        sys.stdout.write(proc.stdout[-3000:])
        if not os.path.exists(SCENE_OBJ):  # run.py's upload may 403, but scene.obj is what we need
            print(f"[{loc_id}] run.py did not produce scene.obj:\n{proc.stderr[-3000:]}")
            return None
    print(f"[{loc_id}] uploading out/scene.obj to bucket '{APS_BUCKET}'...")
    return aps_upload_translate(SCENE_OBJ)


def _merge_scene_materials(proposed_mtl_path):
    """Append the real scene's materials so the baseline geometry renders textured
    alongside the amber/concrete proposed surfaces (scene.mtl isn't in the zip)."""
    if os.path.exists(SCENE_MTL):
        with open(SCENE_MTL) as f:
            extra = f.read()
        with open(proposed_mtl_path, "a") as f:
            f.write("\n# --- baseline scene materials ---\n" + extra)


def generate_and_upload_all():
    locs_path = os.path.join(DATA_DIR, 'locations.json')
    if not os.path.exists(locs_path):
        return
    with open(locs_path, 'r') as f:
        locs = json.load(f)

    for loc in locs:
        loc_id = loc['id']
        is_real = loc_id in REAL_BASELINE_IDS
        urns = load_urns()
        b_key = f"{loc_id}_baseline"

        # --- baseline ---
        baseline_obj = os.path.join(OUT_DIR, f"{loc_id}_baseline.obj")
        if b_key not in urns:
            urn = build_real_baseline(loc_id) if is_real else None
            if urn is None:
                if not os.path.exists(baseline_obj):
                    with open(baseline_obj, 'w') as f:
                        f.write(f"o Baseline_{loc_id}\nv 0 0 0\n")
                urn = f"mock_base_urn_for_{loc_id}"
            save_urn(b_key, urn)

        # The OBJ proposed repairs build on: the real scene for Davis, else the stub.
        base_for_proposed = SCENE_OBJ if (is_real and os.path.exists(SCENE_OBJ)) else baseline_obj
        if not os.path.exists(base_for_proposed):
            with open(base_for_proposed, 'w') as f:
                f.write(f"o Baseline_{loc_id}\nv 0 0 0\n")
        real_scene = base_for_proposed == SCENE_OBJ

        # --- proposed repair variants ---
        for opt in loc.get('repair_options', []):
            o_id = opt['id']
            p_key = f"{loc_id}_{o_id}"
            urns = load_urns()
            if p_key in urns:
                continue
            p_path = os.path.join(OUT_DIR, f"{p_key}_proposed.obj")
            generate_proposed(loc_id, o_id, base_for_proposed, p_path)
            if real_scene:
                _merge_scene_materials(p_path[:-4] + ".mtl")
            if is_real and APS_AVAILABLE and real_scene:
                p_urn = aps_upload_translate(p_path)
            else:
                p_urn = f"mock_prop_urn_{loc_id}_{o_id}"
            save_urn(p_key, p_urn)


if __name__ == "__main__":
    generate_and_upload_all()
    print("Pre-generation complete. Booting Flask app...")
    server_path = os.path.join(ROOT, 'api', 'server.py')
    subprocess.run([sys.executable, server_path])
    print("CurbCheck is running at http://localhost:5000")
