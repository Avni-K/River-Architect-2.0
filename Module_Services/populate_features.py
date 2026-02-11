import os
from typing import List, Tuple

import arcpy
from arcpy.sa import Log10
import config
import fGl

class InputError(ValueError):
    """Raised when required rasters are missing or inconsistent."""


def _fetch_condition_inputs(conn, condition_name: str) -> Tuple[str, str, str, str]:
    """Fetch depth, velocity, grain raster paths and unit for a condition."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT depth_rasters,
               velocity_rasters,
               grain_size_raster,
               unit
        FROM condition
        WHERE condition_name = %s;
        """,
        (condition_name,),
    )
    row = cursor.fetchone()
    cursor.close()
    if not row:
        raise ValueError(f"Condition '{condition_name}' not found in database.")
    depth_rasters, velocity_rasters, grain_raster, unit = row
    return depth_rasters or "", velocity_rasters or "", grain_raster or "", (unit or "").lower()


def _get_condition_output_root(conn, condition_name: str) -> str:
    """Return the base output folder for a condition (condition_name_outputs)."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT condition_output_path FROM condition WHERE condition_name = %s;",
        (condition_name,),
    )
    row = cursor.fetchone()
    cursor.close()
    if not row or not row[0]:
        raise ValueError(
            f"No output location stored for condition '{condition_name}'. "
            "Set an output folder in the Condition tab first."
        )
    base_path = row[0]
    os.makedirs(base_path, exist_ok=True)
    return base_path


def _split_paths(raw: str) -> List[str]:
    """Split semicolon-separated paths, trimming blanks."""
    return [p for p in (raw or "").split(";") if p.strip()]


def _validate_inputs(depth_paths: List[str], vel_paths: List[str], grain_path: str):
    """Ensure required rasters exist and lists align."""
    if not depth_paths or not vel_paths:
        raise InputError("Depth and velocity rasters are required for this operation.")
    if len(depth_paths) != len(vel_paths):
        raise InputError(
            f"Depth/velocity raster count mismatch ({len(depth_paths)} vs {len(vel_paths)}). "
            "Ensure both lists align 1:1."
        )
    if not grain_path:
        raise InputError("Grain size raster is required for this operation.")
    if not os.path.exists(grain_path):
        raise InputError(f"Grain size raster not found at: {grain_path}")
    missing_depth = [p for p in depth_paths if not os.path.exists(p)]
    missing_vel = [p for p in vel_paths if not os.path.exists(p)]
    if missing_depth:
        raise InputError(f"Missing depth rasters: {', '.join(missing_depth)}")
    if missing_vel:
        raise InputError(f"Missing velocity rasters: {', '.join(missing_vel)}")


def _unit_params(unit: str):
    """Return unit-dependent constants."""
    __n__ = 0.0473934
    if "us" in unit :
        ft2m = config.ft2m
        rho_w = 1.937
        n = __n__ / 1.49
    else:
        ft2m = 1.0
        rho_w = 1000.0
        n = __n__
    g = 9.81 / ft2m
    s = 2.68
    return ft2m, rho_w, n, g, s


def _save_paths_to_db(conn, condition_name: str, column: str, paths: List[str]):
    """Update a condition row with semicolon-separated output paths."""
    cursor = conn.cursor()
    cursor.execute(
        f"ALTER TABLE IF EXISTS condition ADD COLUMN IF NOT EXISTS {column} TEXT;"
    )
    cursor.execute(
        f"UPDATE condition SET {column} = %s WHERE condition_name = %s;",
        (";".join(paths), condition_name),
    )
    conn.commit()
    cursor.close()


def _get_or_create_subfolder(conn, condition_name: str, column: str, folder_name: str) -> str:
    """
    Return a subfolder path stored in `condition.column`; create it if missing.
    """
    cur = conn.cursor()
    cur.execute(
        f"SELECT {column} FROM condition WHERE condition_name = %s;",
        (condition_name,),
    )
    row = cur.fetchone()
    cur.close()
    if row and row[0]:
        os.makedirs(row[0], exist_ok=True)
        return row[0]
    return create_output_subfolder(conn, condition_name, folder_name, column)


def create_output_subfolder(conn, condition_name: str, subfolder_name: str, column_name: str) -> str:
    """
    Create a named subfolder inside condition_output_path and save its path.

    Parameters
    ----------
    conn : psycopg2 connection
    condition_name : str
    subfolder_name : str
        Folder name to create under <condition_output_path>.
    column_name : str
        DB column in `condition` table that will store the folder path.
    """
    base_path = _get_condition_output_root(conn, condition_name)
    target = os.path.join(base_path, subfolder_name)
    os.makedirs(target, exist_ok=True)

    cur = conn.cursor()
    cur.execute(
        f"ALTER TABLE IF EXISTS condition ADD COLUMN IF NOT EXISTS {column_name} TEXT;"
    )
    cur.execute(
        f"UPDATE condition SET {column_name} = %s WHERE condition_name = %s;",
        (target, condition_name),
    )
    conn.commit()
    cur.close()
    return target


def calculate_bed_shear_stress(condition_name: str, conn):
    """
    Calculate bed shear stress rasters for a condition and store file paths in DB.
    """
    depth_raw, vel_raw, grain_path, unit = _fetch_condition_inputs(conn, condition_name)
    _, rho_w, _, _, _ = _unit_params(unit)
    shear_dir = _get_or_create_subfolder(conn, condition_name, "shear_rasters_folder", "shear rasters")

    depth_paths = _split_paths(depth_raw)
    vel_paths = _split_paths(vel_raw)
    _validate_inputs(depth_paths, vel_paths, grain_path)

    grains = arcpy.Raster(grain_path)
    outputs = []

    for depth_path, vel_path in zip(depth_paths, vel_paths):
        depth_r = arcpy.Raster(depth_path)
        vel_r = arcpy.Raster(vel_path)

        q_val = fGl.read_Q_str(os.path.basename(depth_path), prefix="h")
        tb_name = "tb" + fGl.write_Q_str(q_val) + ".tif"
        tb_path = os.path.join(shear_dir, tb_name)

        shear_vel = vel_r / (5.75 * Log10(12.2 * depth_r / (2 * 2.2 * grains)))
        tb = rho_w * (shear_vel ** 2)

        arcpy.CopyRaster_management(tb, tb_path)
        outputs.append(tb_path)

    _save_paths_to_db(conn, condition_name, "bed_shear_rasters", outputs)
    return outputs


def calculate_bed_shield_stress(condition_name: str, conn):
    """
    Calculate bed Shields stress rasters for a condition and store file paths in DB.
    Depends on bed shear outputs; computes both if needed.
    """
    depth_raw, vel_raw, grain_path, unit = _fetch_condition_inputs(conn, condition_name)
    _, rho_w, _, g, s_val = _unit_params(unit)
    shield_dir = _get_or_create_subfolder(conn, condition_name, "shield_stress_rasters_folder", "shield stress rasters")

    depth_paths = _split_paths(depth_raw)
    vel_paths = _split_paths(vel_raw)
    _validate_inputs(depth_paths, vel_paths, grain_path)

    grains = arcpy.Raster(grain_path)
    outputs = []

    for depth_path, vel_path in zip(depth_paths, vel_paths):
        depth_r = arcpy.Raster(depth_path)
        vel_r = arcpy.Raster(vel_path)

        q_val = fGl.read_Q_str(os.path.basename(depth_path), prefix="h")
        ts_name = "ts" + fGl.write_Q_str(q_val) + ".tif"
        ts_path = os.path.join(shield_dir, ts_name)

        shear_vel = vel_r / (5.75 * Log10(12.2 * depth_r / (2 * 2.2 * grains)))
        tb = rho_w * (shear_vel ** 2)
        ts = tb / (rho_w * g * (s_val - 1) * grains)

        arcpy.CopyRaster_management(ts, ts_path)
        outputs.append(ts_path)

    _save_paths_to_db(conn, condition_name, "bed_shield_rasters", outputs)
    return outputs
