"""
Simple script to visualize a token's scene using navsim.visualization.
Usage examples in README/Docstrings below.
"""
import argparse
from pathlib import Path
import numpy as np

from navsim.common.dataclasses import SceneFilter, SensorConfig
from navsim.common.dataloader import SceneLoader
from navsim.common.dataclasses import Trajectory as TrajDC
from navsim.visualization import plots


def load_scene(data_path: Path, sensor_blobs_path: Path, token: str, num_history: int = 4, num_future: int = 10):
    scene_filter = SceneFilter(num_history_frames=num_history, num_future_frames=num_future, frame_interval=1, has_route=True, tokens=[token])
    sensor_config = SensorConfig.build_no_sensors()
    loader = SceneLoader(data_path=data_path, sensor_blobs_path=sensor_blobs_path, scene_filter=scene_filter, sensor_config=sensor_config)
    assert token in loader.tokens, f"Token {token} not found under data_path={data_path}"
    scene = loader.get_scene_from_token(token)
    return scene


def load_prediction(trajs_dir: Path, token: str):
    traj_path = trajs_dir / f"{token}.npy"
    if not traj_path.exists():
        return None
    poses = np.load(traj_path)
    return TrajDC(poses)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--data-path", required=True, help="Path to dataset/ maps pickles (folder of log pickle files)")
    parser.add_argument("--sensor-blobs", required=True, help="Path to sensor_blobs directory (dataset/sensor_blobs")
    parser.add_argument("--trajs-dir", default=None, help="Optional path to directory with <token>.npy predicted trajectories (GoalFlow)")
    parser.add_argument("--trajs-dir2", default=None, help="Optional path to second directory with <token>.npy predicted trajectories (SafeGoalFlow)")
    parser.add_argument("--frame-idx", type=int, default=None, help="Frame index to visualize (defaults to history last frame)")
    parser.add_argument("--out", default=None, help="Optional output image path (png). If omitted, image will be displayed using plt.show().")
    args = parser.parse_args()

    data_path = Path(args.data_path)
    sensor_blobs_path = Path(args.sensor_blobs)
    token = args.token

    scene = load_scene(data_path, sensor_blobs_path, token)

    # choose frame
    if args.frame_idx is None:
        frame_idx = scene.scene_metadata.num_history_frames - 1
    else:
        frame_idx = args.frame_idx

    # If prediction provided, overlay on BEV
    if args.trajs_dir is not None:
        print(f"Loading prediction from {args.trajs_dir} for token {token}")
        pred = load_prediction(Path(args.trajs_dir), token)
    else:
        pred = None

    # If second prediction provided
    if args.trajs_dir2 is not None:
        print(f"Loading second prediction from {args.trajs_dir2} for token {token}")
        pred2 = load_prediction(Path(args.trajs_dir2), token)
    else:
        pred2 = None

    fig, ax = plots.plot_bev_frame(scene, frame_idx)

    # Determine if we have two trajectories for custom coloring
    has_two_trajectories = pred is not None and pred2 is not None

    if pred is not None:
        print(f"Overlaying prediction from {args.trajs_dir} for token {token}")
        from navsim.visualization.bev import add_trajectory_to_bev_ax
        from navsim.visualization.config import TRAJECTORY_CONFIG
        # Use red color and add label when two trajectories are present
        if has_two_trajectories:
            config = TRAJECTORY_CONFIG["agent"].copy()
            config["line_color"] = "#d62728"  # red
            config["fill_color"] = "#d62728"
            add_trajectory_to_bev_ax(ax, pred, config)
            ax.plot([], [], color="#d62728", linewidth=2.0, marker="o", markersize=5, label="GoalFlow")
        else:
            add_trajectory_to_bev_ax(ax, pred, TRAJECTORY_CONFIG["agent"])

    if pred2 is not None:
        print(f"Overlaying second prediction from {args.trajs_dir2} for token {token}")
        from navsim.visualization.bev import add_trajectory_to_bev_ax
        from navsim.visualization.config import TRAJECTORY_CONFIG
        # Use green color for second trajectory
        config = TRAJECTORY_CONFIG["agent"].copy()
        config["line_color"] = "#2ca02c"  # green
        config["fill_color"] = "#2ca02c"
        add_trajectory_to_bev_ax(ax, pred2, config)
        ax.plot([], [], color="#2ca02c", linewidth=2.0, marker="o", markersize=5, label="SafeGoalFlow (Ours)")

    # Add legend if we have two trajectories
    if has_two_trajectories:
        ax.legend(loc="lower left")

    if args.out is None:
        import matplotlib.pyplot as plt
        plt.show()
    else:
        fig.savefig(args.out, bbox_inches="tight")


if __name__ == "__main__":
    main()
