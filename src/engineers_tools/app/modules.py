"""Launcher module registry.

The launcher must keep all planned design workspaces visible. Current active work
is Engineering Design Tools, but the other cards remain as routed placeholders.
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
    LauncherModule(
        key="circuit_design",
        title="Circuit Design",
        label="Circuit Design",
        description="Electronic circuits and RLC symbols",
        accent="#20a86b",
        icon_kind="circuits",
        folder="modules/electronic_circuits",
        entry_point="modules.electronic_circuits.module_entry:create_window",
    ),
    LauncherModule(
        key="flowcharts",
        title="Engineering Flowcharts",
        label="Flowcharts",
        description="Process and decision diagrams",
        accent="#f0a12b",
        icon_kind="flowcharts",
        folder="modules/engineering_flowcharts",
        entry_point="modules.engineering_flowcharts.module_entry:create_window",
    ),
    LauncherModule(
        key="barcode",
        title="Barcode Designer",
        label="Barcode",
        description="Barcode generation and print setup",
        accent="#d5579d",
        icon_kind="barcode",
        folder="modules/barcode_designer",
        entry_point="modules.barcode_designer.module_entry:create_window",
    ),
    LauncherModule(
        key="background",
        title="White Background Remover",
        label="Background",
        description="Clean white image backgrounds",
        accent="#6f63d9",
        icon_kind="background",
        folder="modules/white_background_remover",
        entry_point="modules.white_background_remover.module_entry:create_window",
    ),
)
