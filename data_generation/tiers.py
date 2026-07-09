"""Difficulty tier definitions for dataset generation.

Each tier scales the same set of domain randomization axes (lighting,
obstacle appearance, obstacle geometry, camera jitter). "hard" also
introduces a shape held out of "easy"/"medium" entirely, so it tests
generalization rather than just adding noise to familiar conditions.

This module has no Isaac Sim / Replicator dependencies, so it can be
imported standalone (e.g. from training/benchmark code) to inspect what a
tier means without needing the sim running.
"""

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class Range:
    low: float
    high: float

    def sample(self, rng: random.Random) -> float:
        return rng.uniform(self.low, self.high)


@dataclass(frozen=True)
class TierConfig:
    name: str

    # Single dome light, resampled every frame.
    light_intensity: Range
    light_tint: Range  # per-channel RGB multiplier, sampled independently

    # Obstacle appearance/geometry, resampled per obstacle per frame.
    obstacle_shapes: tuple[str, ...]
    obstacle_color: Range  # per-channel RGB, sampled independently
    obstacle_scale: Range  # meters
    obstacle_rotation_deg: Range

    # Ground plane / backdrop wall color, resampled per frame. Gives the
    # model varied surroundings to generalize across, same as the axes above.
    ground_color: Range  # per-channel RGB, sampled independently
    backdrop_color: Range  # per-channel RGB, sampled independently

    # +/- meters, applied independently to camera x (lateral) and z (height).
    camera_position_jitter: float

    # Chance a "don't care" lane gets an obstacle anyway, so the model can't
    # shortcut by assuming untouched lanes are always empty.
    distractor_probability: float


TIERS: dict[str, TierConfig] = {
    "easy": TierConfig(
        name="easy",
        light_intensity=Range(800, 1200),
        light_tint=Range(0.9, 1.0),
        obstacle_shapes=("cube",),
        obstacle_color=Range(0.2, 0.8),
        obstacle_scale=Range(0.4, 0.6),
        obstacle_rotation_deg=Range(0, 30),
        ground_color=Range(0.4, 0.6),
        backdrop_color=Range(0.7, 0.9),
        camera_position_jitter=0.05,
        distractor_probability=0.2,
    ),
    "medium": TierConfig(
        name="medium",
        light_intensity=Range(400, 2000),
        light_tint=Range(0.6, 1.0),
        obstacle_shapes=("cube", "sphere"),
        obstacle_color=Range(0.05, 0.95),
        obstacle_scale=Range(0.3, 0.8),
        obstacle_rotation_deg=Range(0, 90),
        ground_color=Range(0.15, 0.85),
        backdrop_color=Range(0.4, 1.0),
        camera_position_jitter=0.15,
        distractor_probability=0.4,
    ),
    "hard": TierConfig(
        name="hard",
        light_intensity=Range(150, 4000),
        light_tint=Range(0.3, 1.0),
        # cylinder is never seen in easy/medium: hard tests generalization
        # to an unseen shape, not just noisier versions of familiar ones.
        obstacle_shapes=("cube", "sphere", "cylinder"),
        obstacle_color=Range(0.0, 1.0),
        obstacle_scale=Range(0.2, 1.1),
        obstacle_rotation_deg=Range(0, 180),
        ground_color=Range(0.0, 1.0),
        backdrop_color=Range(0.0, 1.0),
        camera_position_jitter=0.3,
        distractor_probability=0.6,
    ),
}
