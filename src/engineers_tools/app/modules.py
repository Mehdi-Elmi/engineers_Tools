"""Launcher module registry.

Only Engineering Design Tools is active in this repository stage. Other tools must be
added later as separate module folders and explicit entry points.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LauncherModule:
    key: str
    title: str
    label: str
    description: str
    accent: str
    icon_kind: str
    folder: str
    entry_point: str


MODULES: tuple[LauncherModule, ...] = (
    LauncherModule(
        key="engineering_design",
        title="Engineering Design Tools",
        label="Engineering Design Tools",
        description="Statics, dynamics, robotics and vector drawing",
        accent="#2f7df6",
        icon_kind="engineering",
        folder="modules/mechanics_dynamics_statics",
        entry_point="modules.mechanics_dynamics_statics.module_entry:create_window",
    ),
)
