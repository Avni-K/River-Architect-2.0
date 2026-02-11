import os

from PyQt5.QtWidgets import QLineEdit, QComboBox
try:
    import sip
except ImportError:  # fallback if sip not available
    sip = None
from psycopg2 import Error


def proceed_to_analysis(window):
    """Handle proceed button click."""
    condition_name = window.inputs["Condition Name"].text()

    if not condition_name:
        window.info_text.append("\n⚠ Please enter a Condition Name before proceeding.")
        return

    base_output = window.inputs.get("Select Output Location", QLineEdit()).text().strip()
    if not base_output:
        window.info_text.append("\n⚠ Please select an output location before proceeding.")
        return

    output_path = os.path.join(base_output, f"{condition_name}_outputs")

    try:
        os.makedirs(output_path, exist_ok=True)
    except Exception as exc:  # keep UI responsive on failure
        window.info_text.append(f"\n⚠ Could not create output folder:\n{exc}")
        return

    if window.db_connection:
        try:
            cursor = window.db_connection.cursor()
            cursor.execute("ALTER TABLE IF EXISTS condition ADD COLUMN IF NOT EXISTS condition_output_path TEXT;")
            cursor.execute(
                "UPDATE condition SET condition_output_path = %s WHERE condition_name = %s;",
                (output_path, condition_name),
            )
            window.db_connection.commit()
            cursor.close()
            window.info_text.append(f"\n✓ Output folder set to:\n{output_path}")
        except (Exception, Error) as error:
            window.info_text.append(f"\n⚠ Could not save output folder to database: {error}")
            try:
                window.db_connection.rollback()
            except Exception:
                pass

    window.info_text.append(f"\n✓ Condition '{condition_name}' ready for analysis.")
    window.info_text.append("Loading analysis modules...")


def create_condition(window):
    """Handle create condition button click."""
    condition_name = window.inputs["Condition Name"].text()
    if not condition_name:
        window.info_text.append("\n⚠ Please enter a Condition Name before creating a condition.")
        return

    if condition_name in window.conditions:
        window.info_text.append(f"\n⚠ Condition '{condition_name}' already exists.")
        return

    depth_rasters = window.inputs["Depth Rasters"].text()
    velocity_rasters = window.inputs["Velocity Rasters"].text()
    dem = window.inputs["Digital Elevatation Model"].text()
    grain_size = window.inputs["Grain size rasters"].text()
    wse_folder = window.inputs.get("WSE Folder", QLineEdit()).text()
    velocity_angle_folder = window.inputs.get("Velocity Angle Folder", QLineEdit()).text()
    scour_raster = window.inputs.get("Scour Raster", QLineEdit()).text()
    fill_raster = window.inputs.get("Fill Raster", QLineEdit()).text()
    background_raster = window.inputs.get("Background Raster", QLineEdit()).text()
    base_output = window.inputs.get("Select Output Location", QLineEdit()).text().strip()
    condition_output_path = os.path.join(base_output, f"{condition_name}_outputs") if base_output else None
    unit = None
    if "Unit" in window.inputs and isinstance(window.inputs["Unit"], QComboBox):
        unit = window.inputs["Unit"].currentText()

    if not window.db_connection:
        window.info_text.append("\n⚠ Database connection not available.")
        return

    try:
        cursor = window.db_connection.cursor()
        cursor.execute(
            """
            INSERT INTO condition (
                condition_name,
                unit,
                depth_rasters,
                velocity_rasters,
                digital_elevation_model,
                grain_size_raster,
                wse_folder,
                velocity_angle_folder,
                scour_raster,
                fill_raster,
                background_raster,
                condition_output_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                condition_name,
                unit,
                depth_rasters,
                velocity_rasters,
                dem,
                grain_size,
                wse_folder,
                velocity_angle_folder,
                scour_raster,
                fill_raster,
                background_raster,
                condition_output_path
            )
        )
        window.db_connection.commit()
        cursor.close()

        window.conditions.append(condition_name)
        window.condition_selector.addItem(condition_name)
        # Refresh condition lists from DB to ensure all views show the latest data
        try:
            load_conditions_from_db(window)
        except Exception:
            pass
        window.info_text.append(f"\n✓ Condition '{condition_name}' has been created and saved to the database.")
        try:
            window.set_active_condition(condition_name)
        except Exception:
            pass
    except (Exception, Error) as error:
        window.info_text.append(f"\nError saving condition to database: {error}")
        window.db_connection.rollback()


def populate_condition_fields(window, condition_name):
    """Fetch a condition record from the DB and populate the form fields."""
    if not condition_name:
        return
    if not window.db_connection:
        window.info_text.append("\n⚠ Database connection not available.")
        return
    try:
        cursor = window.db_connection.cursor()
        cursor.execute(
            """
            SELECT
                unit,
                depth_rasters,
                velocity_rasters,
                digital_elevation_model,
                grain_size_raster,
                wse_folder,
                velocity_angle_folder,
                scour_raster,
                fill_raster,
                background_raster,
                condition_output_path
            FROM condition
            WHERE condition_name = %s;
            """,
            (condition_name,)
        )
        record = cursor.fetchone()
        cursor.close()
        if record:
            (
                unit,
                depth_rasters,
                velocity_rasters,
                dem,
                grain_size,
                wse_folder,
                velocity_angle_folder,
                scour_raster,
                fill_raster,
                background_raster,
                condition_output_path,
            ) = record
            # Ensure keys exist in inputs
            window.inputs.setdefault("Condition Name", QLineEdit()).setText(condition_name)
            if "Unit" in window.inputs and isinstance(window.inputs["Unit"], QComboBox):
                window.inputs["Unit"].setCurrentText(unit or window.inputs["Unit"].itemText(0))
            if "Depth Rasters" in window.inputs:
                window.inputs["Depth Rasters"].setText(depth_rasters or "")
            if "Velocity Rasters" in window.inputs:
                window.inputs["Velocity Rasters"].setText(velocity_rasters or "")
            if "Digital Elevatation Model" in window.inputs:
                window.inputs["Digital Elevatation Model"].setText(dem or "")
            if "Grain size rasters" in window.inputs:
                window.inputs["Grain size rasters"].setText(grain_size or "")
            if "WSE Folder" in window.inputs:
                window.inputs["WSE Folder"].setText(wse_folder or "")
            if "Velocity Angle Folder" in window.inputs:
                window.inputs["Velocity Angle Folder"].setText(velocity_angle_folder or "")
            if "Scour Raster" in window.inputs:
                window.inputs["Scour Raster"].setText(scour_raster or "")
            if "Fill Raster" in window.inputs:
                window.inputs["Fill Raster"].setText(fill_raster or "")
            if "Background Raster" in window.inputs:
                window.inputs["Background Raster"].setText(background_raster or "")
            if "Select Output Location" in window.inputs:
                # Store the parent folder so user sees the location they picked
                base_output = ""
                if condition_output_path:
                    # If we stored the path with the suffix, show the parent directory
                    expected_suffix = f"{condition_name}_outputs"
                    if condition_output_path.endswith(expected_suffix):
                        base_output = os.path.dirname(condition_output_path)
                    else:
                        base_output = condition_output_path
                window.inputs["Select Output Location"].setText(base_output)
            window.info_text.append(f"\n✓ Loaded condition '{condition_name}' from database.")
            try:
                window.set_active_condition(condition_name)
            except Exception:
                pass
        else:
            window.info_text.append(f"\n⚠ No database record found for '{condition_name}'.")
    except (Exception, Error) as error:
        window.info_text.append(f"\nError loading condition from database: {error}")


def load_condition(window, index):
    """Handle condition selection from dropdown."""
    condition_name = window.condition_selector.itemText(index)
    window.inputs["Condition Name"].setText(condition_name)
    populate_condition_fields(window, condition_name)


def load_conditions_from_db(window):
    """Load condition names into the selector and local cache."""
    if not window.db_connection:
        return

    try:
        cursor = window.db_connection.cursor()
        cursor.execute("SELECT condition_name FROM condition;")
        conditions = cursor.fetchall()
        cursor.close()

        window.conditions = [c[0] for c in conditions]

        selector = getattr(window, "condition_selector", None)
        if selector is not None:
            try:
                if sip and sip.isdeleted(selector):
                    selector = None
            except Exception:
                pass
        if selector is not None:
            try:
                selector.clear()
                selector.addItems(window.conditions)
            except Exception:
                pass

        info = getattr(window, "info_text", None)
        if info is not None:
            try:
                if sip and sip.isdeleted(info):
                    info = None
            except Exception:
                pass
        if info is not None:
            try:
                info.append("\n✓ Successfully loaded conditions from the database.")
            except Exception:
                pass
        try:
            if window.active_condition and window.active_condition in window.conditions:
                window.set_active_condition(window.active_condition)
            elif window.conditions:
                window.set_active_condition(window.conditions[0])
            else:
                window.set_active_condition(None)
        except Exception:
            pass
    except (Exception, Error) as error:
        info = getattr(window, "info_text", None)
        if info is not None:
            try:
                if sip and sip.isdeleted(info):
                    info = None
            except Exception:
                pass
        if info is not None:
            try:
                info.append(f"\nError loading conditions from database: {error}")
            except Exception:
                pass
