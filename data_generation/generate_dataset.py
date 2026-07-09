"""Generate a labeled dataset for the path-direction task via Replicator.

Standalone Isaac Sim script, run headless through infra/run-script-isaac.sh:

    infra/run-script-isaac.sh data_generation/generate_dataset.py \\
        --tier easy --num-frames 500

Scene: a fixed camera facing three lanes (left/center/right) over a ground
plane, with a backdrop wall past the far lane distance. Each frame, a label
is sampled uniformly from perception.labels.LABELS first, and the scene is
then constructed to match it (obstacles placed to block exactly the lanes
that label requires), so the ground truth is always exact by construction
rather than inferred after the fact. Lanes not required by the label are
randomized as distractors (see TierConfig.distractor_probability) so the
model can't shortcut by assuming untouched lanes are always clear. Ground/
backdrop color is also randomized per tier, so surroundings vary too.

RGB and depth are both captured; only RGB is used by the initial models,
depth is kept around cheaply in case a later modality comparison is worth doing
"""

import argparse
import csv
import faulthandler
import os
import random
from collections import Counter
from pathlib import Path

from perception.labels import LABELS
from tiers import TIERS, TierConfig

LANES = ("left", "center", "right")
LANE_X = {"left": -1.2, "center": 0.0, "right": 1.2}
LANE_DISTANCE = (1.5, 3.0)  # meters ahead of the camera
CAMERA_HEIGHT = 1.0
BACKDROP_DISTANCE = LANE_DISTANCE[1] + 3.0
PARK_POSITION = (0.0, -5.0, -5.0)  # behind the camera, never rendered

# Which lanes must be blocked/clear for each label; lanes absent from a
# label's entry are "don't care" and get randomized as distractors.
REQUIRED_BLOCKED = {
    "straight": {"center": False},
    "left": {"center": True, "left": False},
    "right": {"center": True, "left": True, "right": False},
    "stop": {"center": True, "left": True, "right": True},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", choices=sorted(TIERS), default="easy")
    parser.add_argument("--num-frames", type=int, default=200)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--resolution", type=int, default=224)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    if args.output_dir is None:
        # Under data_generation/data/ so .gitignore's `data/` rule covers it.
        args.output_dir = f"data_generation/data/{args.tier}"
    return args


def sample_scenario(tier: TierConfig, rng: random.Random) -> tuple[str, dict[str, bool]]:
    label = rng.choice(LABELS)
    required = REQUIRED_BLOCKED[label]
    blocked = {
        lane: required.get(lane, rng.random() < tier.distractor_probability)
        for lane in LANES
    }
    return label, blocked


def main() -> None:
    args = parse_args()
    tier = TIERS[args.tier]
    rng = random.Random(args.seed)

    # Absolute: Replicator's DiskBackend resolves relative paths against its
    # own internal root, not the process cwd.
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    from isaacsim import SimulationApp

    # Fail loudly if the lean experience isn't where expected, rather than
    # silently falling back to the full GUI+streaming+ROS2-bridge app
    exp_path = Path(os.environ["EXP_PATH"])
    experience = exp_path / "isaacsim.exp.base.python.kit"
    if not experience.is_file():
        available = "\n".join(f"  {p.name}" for p in sorted(exp_path.glob("*.kit")))
        raise FileNotFoundError(
            f"Expected experience file not found: {experience}\n"
            f".kit files actually present in {exp_path}:\n{available}"
        )
    # RaytracedLighting (RTX Real-Time legacy) instead of the default
    # RealTimePathTracing: cheaper, and still respects the dome light
    # intensity/tint that domain randomization depends on
    launch_config = {"headless": True, "renderer": "RaytracedLighting"}
    simulation_app = SimulationApp(launch_config, experience=str(experience))
    print("SimulationApp booted, building scene...", flush=True)

    # Needs Kit/USD already running, hence the delayed import. The base
    # experience doesn't enable Replicator by default, so do it explicitly.
    from isaacsim.core.utils.extensions import enable_extension

    enable_extension("omni.replicator.core")

    import carb.settings
    import omni.replicator.core as rep
    import omni.usd
    from pxr import Gf, UsdGeom, UsdLux

    def set_transform(prim, position, rotation_deg=(0.0, 0.0, 0.0), scale=1.0):
        scale_vec = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
        xformable = UsdGeom.Xformable(prim)
        xformable.ClearXformOpOrder()
        xformable.AddTranslateOp().Set(Gf.Vec3d(*position))
        xformable.AddRotateXYZOp().Set(Gf.Vec3f(*rotation_deg))
        xformable.AddScaleOp().Set(Gf.Vec3f(*scale_vec))

    def set_color(prim, rgb):
        UsdGeom.Gprim(prim).GetDisplayColorAttr().Set([Gf.Vec3f(*rgb)])

    def jitter_camera_position(camera_prim, position):
        # Only touches translation, leaving the look_at rotation set at creation time alone
        xformable = UsdGeom.Xformable(camera_prim)
        translate_op = next(
            (op for op in xformable.GetOrderedXformOps() if op.GetOpType() == UsdGeom.XformOp.TypeTranslate),
            None,
        )
        if translate_op is None:
            translate_op = xformable.AddTranslateOp()
        translate_op.Set(Gf.Vec3d(*position))

    omni.usd.get_context().new_stage()
    rep.orchestrator.set_capture_on_play(False)
    # DLSS (default AA) upscales from below its documented 300px minimum at
    # this resolution; TAA has no such floor.
    carb.settings.get_settings().set("/rtx/post/aa/op", 1)  # 1 = TAA

    # Orchestrator's first step() waits (default 30s) for a USD ASSETS_LOADED
    # event that never fires for a purely-procedural stage (no real assets to
    # load), so it always burns the full wait. Harmless, just slow -- cut it down.
    carb.settings.get_settings().set("/exts/omni.replicator.core/maxAssetLoadingTime", 0.1)

    rep.functional.create.xform(name="World")
    dome_light = rep.functional.create.dome_light(intensity=1000, parent="/World", name="DomeLight")
    camera = rep.functional.create.camera(
        position=(0, 0, CAMERA_HEIGHT), look_at=(0, 3, CAMERA_HEIGHT), parent="/World", name="Camera"
    )

    # Ground (top face at z=0, where obstacles rest) and a backdrop wall past
    # the far lane, so obstacles sit in surroundings instead of floating on
    # the dome light's flat background. Colors randomized per frame below.
    ground = rep.functional.create.cube(parent="/World", name="Ground")
    set_transform(ground, (0, BACKDROP_DISTANCE / 2, -0.01), scale=(8, BACKDROP_DISTANCE / 2 + 1, 0.01))
    backdrop = rep.functional.create.cube(parent="/World", name="Backdrop")
    set_transform(backdrop, (0, BACKDROP_DISTANCE, 3), scale=(8, 0.01, 3))

    shape_creators = {
        "cube": rep.functional.create.cube,
        "sphere": rep.functional.create.sphere,
        "cylinder": rep.functional.create.cylinder,
    }
    obstacles = {}
    for lane in LANES:
        for shape_name, creator in shape_creators.items():
            prim = creator(parent="/World", name=f"Obstacle_{lane}_{shape_name}")
            rep.functional.modify.semantics(prim, {"class": "obstacle"}, mode="add")
            set_transform(prim, PARK_POSITION)
            obstacles[(lane, shape_name)] = prim

    render_product = rep.create.render_product(camera, (args.resolution, args.resolution))
    # Only enabled around the capture step below, to skip wasted render work.
    render_product.hydra_texture.set_updates_enabled(False)
    backend = rep.backends.get("DiskBackend")
    backend.initialize(output_dir=str(output_dir))
    writer = rep.writers.get("BasicWriter")
    writer.initialize(backend=backend, rgb=True, distance_to_camera=True)
    writer.attach(render_product)

    manifest_rows = []
    label_counts = Counter()

    print(f"Scene ready, starting capture of {args.num_frames} frames...", flush=True)
    for frame_id in range(args.num_frames):
        label, blocked = sample_scenario(tier, rng)
        label_counts[label] += 1

        intensity = tier.light_intensity.sample(rng)
        tint = (tier.light_tint.sample(rng), tier.light_tint.sample(rng), tier.light_tint.sample(rng))
        light_api = UsdLux.LightAPI(dome_light)
        light_api.GetIntensityAttr().Set(intensity)
        light_api.GetColorAttr().Set(Gf.Vec3f(*tint))

        set_color(
            ground, (tier.ground_color.sample(rng), tier.ground_color.sample(rng), tier.ground_color.sample(rng))
        )
        set_color(
            backdrop,
            (tier.backdrop_color.sample(rng), tier.backdrop_color.sample(rng), tier.backdrop_color.sample(rng)),
        )

        jitter = tier.camera_position_jitter
        jitter_camera_position(
            camera,
            (rng.uniform(-jitter, jitter), 0, CAMERA_HEIGHT + rng.uniform(-jitter, jitter)),
        )

        for lane in LANES:
            active_shape = rng.choice(tier.obstacle_shapes) if blocked[lane] else None
            for shape_name in shape_creators:
                prim = obstacles[(lane, shape_name)]
                if shape_name == active_shape:
                    position = (
                        LANE_X[lane] + rng.uniform(-0.2, 0.2),
                        rng.uniform(*LANE_DISTANCE),
                        tier.obstacle_scale.sample(rng) / 2,
                    )
                    rotation = (0, 0, tier.obstacle_rotation_deg.sample(rng))
                    scale = tier.obstacle_scale.sample(rng)
                    set_transform(prim, position, rotation, scale)
                    color = (
                        tier.obstacle_color.sample(rng),
                        tier.obstacle_color.sample(rng),
                        tier.obstacle_color.sample(rng),
                    )
                    set_color(prim, color)
                else:
                    set_transform(prim, PARK_POSITION)

        render_product.hydra_texture.set_updates_enabled(True)
        # rt_subframes=8: obstacles/camera teleport between captures rather than
        # move continuously, so a few extra render passes avoid DLSS ghosting.
        rep.orchestrator.step(delta_time=0.0, rt_subframes=8)
        render_product.hydra_texture.set_updates_enabled(False)
        # Flush before the next step(): letting writes queue up behind
        # renders is what caused the mid-run deadlocks this used to hit.
        rep.orchestrator.wait_until_complete()
        print(f"frame {frame_id + 1}/{args.num_frames} captured (label={label})", flush=True)

        manifest_rows.append(
            {
                "frame_id": frame_id,
                "label": label,
                "tier": tier.name,
                "left_blocked": blocked["left"],
                "center_blocked": blocked["center"],
                "right_blocked": blocked["right"],
            }
        )

    # Dump all thread stacks if this ever hangs, instead of sitting silently.
    faulthandler.dump_traceback_later(60, exit=False)
    rep.orchestrator.wait_until_complete()
    faulthandler.cancel_dump_traceback_later()
    writer.detach()
    render_product.destroy()

    manifest_path = output_dir / "manifest.csv"
    with open(manifest_path, "w", newline="") as f:
        writer_csv = csv.DictWriter(f, fieldnames=list(manifest_rows[0].keys()))
        writer_csv.writeheader()
        writer_csv.writerows(manifest_rows)

    print(f"Wrote {len(manifest_rows)} frames to {output_dir}")
    print(f"Label counts: {dict(label_counts)}")

    simulation_app.close()


if __name__ == "__main__":
    main()
