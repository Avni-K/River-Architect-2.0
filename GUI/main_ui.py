import sys
import os
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QGroupBox,
    QComboBox,
    QDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import psycopg2
from psycopg2 import Error

# Ensure project root is on sys.path so sibling packages (Module_Services, GUI) import cleanly
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from populate_ui import create_populate_condition_widget
from condition_ui import create_condition_tab
from Module_Services import condition_features, populate_features



class RiverArchitectWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.conditions = []
        self.active_condition = None
        self.db_connection = self.init_db()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("River Architect")
        self.setGeometry(100, 100, 1200, 720)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Heading
        heading = QLabel("Welcome to River Architect for Enhancing Fish Habitat")
        heading_font = QFont()
        heading_font.setPointSize(16)
        heading_font.setBold(True)
        heading.setFont(heading_font)
        heading.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(heading)

        # Vertical button bar (add 'View Database' as a separate tab above Condition)
        button_bar = QVBoxLayout()
        self.page_buttons = {}
        for name in ["View Database", "Select Condition", "Populate Condition", "Lifespan", "Ecohydraulic"]:
            btn = QPushButton(name)
            btn.setMinimumHeight(50)
            btn.setMinimumWidth(200)
            btn.setStyleSheet("font-size: 16px; font-weight: bold;")
            btn.clicked.connect(lambda checked, n=name: self.show_content_page(n))
            button_bar.addWidget(btn)
            self.page_buttons[name] = btn
        main_layout.addLayout(button_bar)


        # Content area (hidden until button is clicked)
        self.content_area = QWidget()
        self.content_layout = QHBoxLayout()
        self.content_area.setLayout(self.content_layout)
        main_layout.addWidget(self.content_area)
        self.content_area.hide()

        # Always-visible active condition status (placed below tabs/content)
        self.active_condition_label = QLabel("Active Condition: None")
        status_font = self.active_condition_label.font()
        status_font.setBold(True)
        self.active_condition_label.setFont(status_font)
        self.active_condition_label.setStyleSheet("color: #000000; padding: 4px 6px;")
        main_layout.addWidget(self.active_condition_label)

    def set_active_condition(self, name):
        """Update the status label for the currently selected condition."""
        self.active_condition = name or None
        label = getattr(self, "active_condition_label", None)
        if label:
            label.setText(f"Active Condition: {name}" if name else "Active Condition: None")

    def show_content_page(self, name):
        # Clear content area
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
        if name == "View Database":
            self.content_area.show()
            self.show_database_content()
        elif name in ("Condition", "Select Condition"):
            self.content_area.show()
            self.show_condition_content()
        elif name == "Populate Condition":
            self.content_area.show()
            self.show_populate_condition_content()
        elif name == "Lifespan":
            self.content_area.show()
            self.show_lifespan_content()
        elif name == "Ecohydraulic":
            self.content_area.show()
            self.show_ecohyraulic_content()
        else:
            self.content_area.hide()

    def show_condition_content(self):
        # Clear existing widgets in content area
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        left_frame, right_frame, refs = create_condition_tab(self)
        self.inputs = refs.get("inputs", {})
        self.condition_selector = refs.get("condition_selector")
        self.info_text = refs.get("info_text")

        self.content_layout.addWidget(left_frame, 2)
        self.content_layout.addWidget(right_frame, 3)

        if self.db_connection:
            condition_features.load_conditions_from_db(self)
        else:
            try:
                self.condition_selector.setEnabled(False)
            except Exception:
                pass

    def show_populate_condition_content(self):
        """Populate Condition tab UI with raster-prep actions."""
        # Clear content area
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        container, refs = create_populate_condition_widget(self)
        # Keep handy references for later use
        self.interpolation_method_combo = refs.get("interpolation_method_combo")
        self.populate_info_text = refs.get("info_text")
        self.populate_buttons = refs.get("buttons", {})

        # Wire up action buttons to create output folders
        btns = self.populate_buttons
        if btns:
            shear_btn = btns.get("shear")
            shield_btn = btns.get("shield")
            depth_btn = btns.get("depth")
            morph_btn = btns.get("morph")
            if shear_btn:
                shear_btn.clicked.connect(lambda _=False: self.run_bed_shear())
            if shield_btn:
                shield_btn.clicked.connect(lambda _=False: self.run_bed_shield())
            if depth_btn:
                depth_btn.clicked.connect(
                    lambda _=False: self.handle_output_folder_creation(
                        "Depth to Water table rasters", "depth_to_water_table_rasters_folder"
                    )
                )
            if morph_btn:
                morph_btn.clicked.connect(
                    lambda _=False: self.handle_output_folder_creation(
                        "Morphological unit rasters", "morphological_unit_rasters_folder"
                    )
                )

        self.content_layout.addWidget(container, 1)


    def show_database_content(self):
        """Display database conditions in the main content area as a separate tab."""
        # Left: list of conditions
        left_frame = QGroupBox("Database Conditions")
        left_layout = QVBoxLayout()
        left_frame.setLayout(left_layout)

        listw = QListWidget()
        self.db_list_widget = listw
        left_layout.addWidget(listw)

        btn_layout = QHBoxLayout()
        load_btn = QPushButton("Load Selected")
        refresh_btn = QPushButton("Refresh")
        btn_layout.addWidget(load_btn)
        btn_layout.addWidget(refresh_btn)
        left_layout.addLayout(btn_layout)

        # Right: details viewer
        right_frame = QGroupBox("Condition Details")
        right_layout = QVBoxLayout()
        right_frame.setLayout(right_layout)
        details = QTextEdit()
        details.setReadOnly(True)
        right_layout.addWidget(details)

        def delete_condition(name, item):
            """Delete a condition from the DB and update UI lists."""
            if not self.db_connection:
                info = getattr(self, "info_text", None)
                if info is not None:
                    try:
                        info.append("\n⚠ Database connection not available; cannot delete condition.")
                    except Exception:
                        pass
                QMessageBox.warning(self, "Database", "Database connection not available.")
                return
            reply = QMessageBox.question(
                self,
                "Delete Condition",
                f"Delete condition '{name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
            try:
                cursor = self.db_connection.cursor()
                cursor.execute("DELETE FROM condition WHERE condition_name = %s;", (name,))
                self.db_connection.commit()
                cursor.close()
                # refresh cached list and selectors
                condition_features.load_conditions_from_db(self)
                listw.takeItem(listw.row(item))
                details.clear()
                info = getattr(self, "info_text", None)
                if info is not None:
                    try:
                        info.append(f"\n✓ Deleted condition '{name}'.")
                    except Exception:
                        pass
                # clear active condition label if we just deleted it
                if getattr(self, "active_condition", None) == name:
                    try:
                        self.set_active_condition(None)
                    except Exception:
                        pass
            except (Exception, Error) as e:
                QMessageBox.critical(self, "Error", f"Could not delete condition:\n{e}")
                info = getattr(self, "info_text", None)
                if info is not None:
                    try:
                        info.append(f"\nError deleting condition '{name}': {e}")
                    except Exception:
                        pass

        def add_condition_item(name):
            """Add a row with a delete button before the condition name."""
            item = QListWidgetItem(name)
            row_widget = QWidget()
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(4, 2, 4, 2)
            delete_btn = QPushButton("Delete")
            delete_btn.setFixedWidth(70)
            delete_btn.clicked.connect(lambda _, n=name, it=item: delete_condition(n, it))
            name_label = QLabel(name)
            row_layout.addWidget(delete_btn)
            row_layout.addWidget(name_label)
            row_layout.addStretch()
            row_widget.setLayout(row_layout)
            item.setSizeHint(row_widget.sizeHint())
            listw.addItem(item)
            listw.setItemWidget(item, row_widget)

        def refresh_list():
            condition_features.load_conditions_from_db(self)
            listw.clear()
            for n in self.conditions:
                add_condition_item(n)
            # keep details pane clean if selection now missing
            details.clear()

        # populate directly from the database to ensure freshness
        if not self.db_connection:
            # try to reconnect
            self.db_connection = self.init_db()
        if self.db_connection:
            try:
                cur = self.db_connection.cursor()
                cur.execute("SELECT condition_name FROM condition ORDER BY condition_name;")
                rows = cur.fetchall()
                cur.close()
                for r in rows:
                    if r and r[0]:
                        add_condition_item(r[0])
                        # keep internal list in sync
                        if r[0] not in self.conditions:
                            self.conditions.append(r[0])
            except (Exception, Error):
                pass

        def show_details(item):
            if not item:
                details.clear()
                return
            name = item.text()
            try:
                cursor = self.db_connection.cursor()
                cursor.execute(
                    """
                    SELECT
                        unit,
                        depth_rasters,
                        velocity_rasters,
                        digital_elevation_model,
                        grain_size_raster,
                        condition_output_path,
                        wse_folder,
                        velocity_angle_folder,
                        scour_raster,
                        fill_raster,
                        background_raster,
                        shear_rasters_folder,
                        shield_stress_rasters_folder,
                        depth_to_water_table_rasters_folder,
                        morphological_unit_rasters_folder
                    FROM condition
                    WHERE condition_name = %s;
                    """,
                    (name,)
                )
                rec = cursor.fetchone()
                cursor.close()
                if rec:
                    (
                        unit,
                        depth,
                        vel,
                        dem,
                        grain,
                        output_path,
                        wse_folder,
                        velocity_angle_folder,
                        scour_raster,
                        fill_raster,
                        background_raster,
                        shear_rasters_folder,
                        shield_stress_rasters_folder,
                        depth_to_water_table_rasters_folder,
                        morphological_unit_rasters_folder
                    ) = rec
                    details.setPlainText(
                        f"Name: {name}"
                        f"\n\nUnit:\n{unit or ''}"
                        f"\n\nDepth Rasters:\n{depth or ''}"
                        f"\n\nVelocity Rasters:\n{vel or ''}"
                        f"\n\nDEM:\n{dem or ''}"
                        f"\n\nGrain Size:\n{grain or ''}"
                        f"\n\nOutputs Folder:\n{output_path or ''}"
                        f"\n\nWSE Folder (optional):\n{wse_folder or ''}"
                        f"\n\nVelocity Angle Folder (optional):\n{velocity_angle_folder or ''}"
                        f"\n\nScour Raster (optional):\n{scour_raster or ''}"
                        f"\n\nFill Raster (optional):\n{fill_raster or ''}"
                        f"\n\nBackground Raster (optional):\n{background_raster or ''}"
                        f"\n\nShear Rasters Folder:\n{shear_rasters_folder or ''}"
                        f"\n\nShield Stress Rasters Folder:\n{shield_stress_rasters_folder or ''}"
                        f"\n\nDepth to Water Table Rasters Folder:\n{depth_to_water_table_rasters_folder or ''}"
                        f"\n\nMorphological Unit Rasters Folder:\n{morphological_unit_rasters_folder or ''}"
                    )
                else:
                    details.setPlainText(f"No record for {name}")
            except (Exception, Error) as e:
                details.setPlainText(f"Error reading DB: {e}")

        def on_load():
            item = listw.currentItem()
            if item:
                name = item.text()
                # switch to Condition tab and populate
                self.show_content_page("Condition")
                # ensure conditions are loaded into selector
                condition_features.load_conditions_from_db(self)
                try:
                    self.condition_selector.setCurrentText(name)
                except Exception:
                    pass
                condition_features.populate_condition_fields(self, name)

        load_btn.clicked.connect(on_load)
        refresh_btn.clicked.connect(refresh_list)
        listw.currentItemChanged.connect(lambda cur, prev: show_details(cur))

        self.content_layout.addWidget(left_frame, 2)
        self.content_layout.addWidget(right_frame, 3)

    def handle_output_folder_creation(self, subfolder_name, column_name):
        """Create a specific output subfolder under condition_name_outputs and record it in DB."""
        condition_name = getattr(self, "active_condition", None)
        info_target = getattr(self, "populate_info_text", None) or getattr(self, "info_text", None)

        if not condition_name:
            if info_target:
                try:
                    info_target.append("\n⚠ Select or create a condition first.")
                except Exception:
                    pass
            return

        if not self.db_connection:
            if info_target:
                try:
                    info_target.append("\n⚠ Database connection not available.")
                except Exception:
                    pass
            return

        try:
            path = populate_features.create_output_subfolder(
                self.db_connection,
                condition_name,
                subfolder_name,
                column_name,
            )
            if info_target:
                try:
                    info_target.append(f"\n✓ Folder ready:\n{path}")
                except Exception:
                    pass
        except Exception as exc:
            if info_target:
                try:
                    info_target.append(f"\n⚠ Could not prepare folder: {exc}")
                except Exception:
                    pass

    def run_bed_shear(self):
        """Run bed shear stress calculation and save rasters to the shear folder."""
        condition_name = getattr(self, "active_condition", None)
        info_target = getattr(self, "populate_info_text", None) or getattr(self, "info_text", None)

        if not condition_name:
            if info_target:
                info_target.append("\n⚠ Select or create a condition first.")
            return
        if not self.db_connection:
            if info_target:
                info_target.append("\n⚠ Database connection not available.")
            return
        try:
            outputs = populate_features.calculate_bed_shear_stress(condition_name, self.db_connection)
            if info_target:
                info_target.append(f"\n✓ Created {len(outputs)} bed shear raster(s).\n" + "\n".join(outputs))
        except populate_features.InputError as exc:
            if info_target:
                info_target.append(f"\n⚠ Input problem: {exc}")
        except Exception as exc:
            if info_target:
                info_target.append(f"\n⚠ Error creating bed shear rasters: {exc}")

    def run_bed_shield(self):
        """Run bed Shields stress calculation and save rasters to the shield folder."""
        condition_name = getattr(self, "active_condition", None)
        info_target = getattr(self, "populate_info_text", None) or getattr(self, "info_text", None)

        if not condition_name:
            if info_target:
                info_target.append("\n⚠ Select or create a condition first.")
            return
        if not self.db_connection:
            if info_target:
                info_target.append("\n⚠ Database connection not available.")
            return
        try:
            outputs = populate_features.calculate_bed_shield_stress(condition_name, self.db_connection)
            if info_target:
                info_target.append(f"\n✓ Created {len(outputs)} bed Shields raster(s).\n" + "\n".join(outputs))
        except populate_features.InputError as exc:
            if info_target:
                info_target.append(f"\n⚠ Input problem: {exc}")
        except Exception as exc:
            if info_target:
                info_target.append(f"\n⚠ Error creating bed Shields rasters: {exc}")
     
    def init_db(self):
        try:
            connection = psycopg2.connect(
                port="5432",
                database="river_architect",
                user="postgres",
                password="database"
            )
            try:
                cursor = connection.cursor()
                cursor.execute("ALTER TABLE IF EXISTS condition ADD COLUMN IF NOT EXISTS unit TEXT;")
                cursor.execute("ALTER TABLE IF EXISTS condition ADD COLUMN IF NOT EXISTS velocity_angle_folder TEXT;")
                cursor.execute("ALTER TABLE IF EXISTS condition ADD COLUMN IF NOT EXISTS background_raster TEXT;")
                cursor.execute("ALTER TABLE IF EXISTS condition ADD COLUMN IF NOT EXISTS condition_output_path TEXT;")
                cursor.execute("ALTER TABLE IF EXISTS condition ADD COLUMN IF NOT EXISTS shear_rasters_folder TEXT;")
                cursor.execute("ALTER TABLE IF EXISTS condition ADD COLUMN IF NOT EXISTS shield_stress_rasters_folder TEXT;")
                cursor.execute("ALTER TABLE IF EXISTS condition ADD COLUMN IF NOT EXISTS depth_to_water_table_rasters_folder TEXT;")
                cursor.execute("ALTER TABLE IF EXISTS condition ADD COLUMN IF NOT EXISTS morphological_unit_rasters_folder TEXT;")
                connection.commit()
                cursor.close()
            except Exception:
                # If this fails we still return the connection; inserts will surface errors
                pass
            return connection
        except (Exception, Error) as error:
            self.info_text.append(f"\nError while connecting to PostgreSQL: {error}")
            return None

    def view_database(self):
        """Open a dialog showing all conditions from the DB and allow loading one."""
        if not self.db_connection:
            self.info_text.append("\n⚠ Database connection not available.")
            return
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT condition_name FROM condition ORDER BY condition_name;")
            records = cursor.fetchall()
            cursor.close()
        except (Exception, Error) as error:
            self.info_text.append(f"\nError querying database: {error}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Database Conditions")
        dlg_layout = QVBoxLayout()

        listw = QListWidget()
        for r in records:
            if r and r[0]:
                listw.addItem(QListWidgetItem(r[0]))
        dlg_layout.addWidget(listw)

        btn_layout = QHBoxLayout()
        load_btn = QPushButton("Load Selected")
        close_btn = QPushButton("Close")
        btn_layout.addWidget(load_btn)
        btn_layout.addWidget(close_btn)
        dlg_layout.addLayout(btn_layout)

        def on_load():
            item = listw.currentItem()
            if item:
                name = item.text()
                # Populate the main form
                self.condition_selector.setCurrentText(name)
                condition_features.populate_condition_fields(self, name)
                dialog.accept()

        load_btn.clicked.connect(on_load)
        close_btn.clicked.connect(dialog.reject)

        listw.itemDoubleClicked.connect(lambda it: (self.condition_selector.setCurrentText(it.text()), condition_features.populate_condition_fields(self, it.text()), dialog.accept()))

        dialog.setLayout(dlg_layout)
        dialog.exec_()

    def closeEvent(self, event):
        if self.db_connection:
            self.db_connection.close()
            print("PostgreSQL connection closed.")
        event.accept()



def main():
    app = QApplication(sys.argv)
    window = RiverArchitectWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
