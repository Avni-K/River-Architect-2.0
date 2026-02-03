import os
from typing import List, Tuple

import psycopg2
from psycopg2 import Error

import arcpy
from arcpy.sa import Log10
import config
import fGl

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


def _ensure_output_dirs(condition_name: str) -> Tuple[str, str]:
    """Create (if needed) tb/ and ts/ output folders for the condition."""
    dir_tb = os.path.join(config.dir2conditions, condition_name, "tb")
    dir_ts = os.path.join(config.dir2conditions, condition_name, "ts")
    os.makedirs(dir_tb, exist_ok=True)
    os.makedirs(dir_ts, exist_ok=True)
    return dir_tb, dir_ts

def _split_paths(raw: str) -> List[str]:
    """Split semicolon-separated paths, trimming blanks."""
    return [p for p in (raw or "").split(";") if p.strip()]


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


def calculate_bed_shear_stress(condition_name: str, conn):
    """
    Calculate bed shear stress rasters for a condition and store file paths in DB.
    """
    depth_raw, vel_raw, grain_path, unit = _fetch_condition_inputs(conn, condition_name)
    ft2m, rho_w, n_val, g, s_val = _unit_params(unit)

    dir_tb, _ = _ensure_output_dirs(condition_name)

    grains = arcpy.Raster(grain_path)

    depth_paths = _split_paths(depth_raw)
    vel_paths = _split_paths(vel_raw)
    outputs = []

    for depth_path, vel_path in zip(depth_paths, vel_paths):
         depth_r = arcpy.Raster(depth_path)
         vel_r = arcpy.Raster(vel_path)

         q_val = fGl.read_Q_str(os.path.basename(depth_path), prefix="h")
         tb_name = "tb" + fGl.write_Q_str(q_val) + ".tif"
         tb_path = os.path.join(dir_tb, tb_name)

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
    ft2m, rho_w, n_val, g, s_val = _unit_params(unit)

    dir_tb, dir_ts = _ensure_output_dirs(condition_name)

    grains = arcpy.Raster(grain_path)

    depth_paths = _split_paths(depth_raw)
    vel_paths = _split_paths(vel_raw)
    outputs = []

    for depth_path, vel_path in zip(depth_paths, vel_paths):
        depth_r = arcpy.Raster(depth_path)
        vel_r = arcpy.Raster(vel_path)

        q_val = fGl.read_Q_str(os.path.basename(depth_path), prefix="h")
        tb_name = "tb" + fGl.write_Q_str(q_val) + ".tif"
        ts_name = "ts" + fGl.write_Q_str(q_val) + ".tif"
        tb_path = os.path.join(dir_tb, tb_name)
        ts_path = os.path.join(dir_ts, ts_name)

        shear_vel = vel_r / (5.75 * Log10(12.2 * depth_r / (2 * 2.2 * grains)))
        tb = rho_w * (shear_vel ** 2)
        ts = tb / (rho_w * g * (s_val - 1) * grains)

        arcpy.CopyRaster_management(tb, tb_path)
        arcpy.CopyRaster_management(ts, ts_path)
        outputs.append(ts_path)

    _save_paths_to_db(conn, condition_name, "bed_shield_rasters", outputs)
    return outputs

