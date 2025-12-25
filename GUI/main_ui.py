import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                             QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QFileDialog, QGroupBox, QToolBox, QComboBox,
                             QDialog, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import psycopg2
from psycopg2 import Error



class RiverArchitectWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.conditions = []
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
        for name in ["View Database", "Condition", "Lifespan", "Ecorhydraulic"]:
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

    def show_content_page(self, name):
        # Clear content area
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
        if name == "View Database":
            self.content_area.show()
            self.show_database_content()
        elif name == "Condition":
            self.content_area.show()
            self.show_condition_content()
        else:
            self.content_area.hide()

    def show_condition_content(self):
        # Left frame: select/create condition
        left_frame = QGroupBox()
        left_frame.setTitle("")
        left_layout = QVBoxLayout()
        left_frame.setLayout(left_layout)

        # Select Condition
        select_box = QGroupBox("Select Condition :")
        select_layout = QVBoxLayout()
        self.condition_selector = QComboBox()
        self.condition_selector.setMinimumWidth(200)
        self.condition_selector.setPlaceholderText("Select a condition")
        self.condition_selector.activated.connect(self.load_condition)
        select_layout.addWidget(self.condition_selector)
        left_layout.addWidget(select_box)

        # Create Condition
        create_box = QGroupBox("Create Condition :")
        create_layout = QVBoxLayout()
        create_box.setLayout(create_layout)
        left_layout.addWidget(create_box)

        self.inputs = {}
        input_fields = [
            "Condition Name",
            "Depth Rasters",
            "Velocity Rasters",
            "Digital Elevatation Model",
            "Grain size rasters",
        ]
        for field_name in input_fields:
            field_layout = QHBoxLayout()
            label = QLabel(field_name)
            label.setMinimumWidth(180)
            field_layout.addWidget(label)
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"Enter {field_name.lower()}")
            field_layout.addWidget(input_field)
            if "raster" in field_name.lower() or "model" in field_name.lower():
                browse_btn = QPushButton("Browse")
                browse_btn.setMaximumWidth(80)
                browse_btn.clicked.connect(lambda checked, f=input_field: self.browse_file(f))
                field_layout.addWidget(browse_btn)
            create_layout.addLayout(field_layout)
            self.inputs[field_name] = input_field

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        create_condition_btn = QPushButton("Create Condition")
        create_condition_btn.setMinimumWidth(150)
        create_condition_btn.clicked.connect(self.create_condition)
        button_layout.addWidget(create_condition_btn)
        proceed_btn = QPushButton("Proceed to Analysis")
        proceed_btn.setMinimumWidth(150)
        proceed_btn.clicked.connect(self.proceed_to_analysis)
        button_layout.addWidget(proceed_btn)
        create_layout.addLayout(button_layout)

        left_layout.addStretch()

        # Right frame: information
        right_frame = QGroupBox("Information regarding usage")
        right_layout = QVBoxLayout()
        right_frame.setLayout(right_layout)
        self.info_text = QTextEdit()
        self.info_text.setPlaceholderText("Usage information will appear here...")
        self.info_text.setReadOnly(False)
        default_info = """River Architect - Getting Started\n\n1. Enter a Condition Name to identify your project/scenario\n\n2. Browse and select the required input raster files:\n - Flow Rasters: Hydrodynamic flow depth data\n - Velocity Rasters: Flow velocity data\n - Digital Elevation Model: Terrain elevation data\n - Grain Size Rasters: Substrate grain size distribution\n\n3. All raster files should be in GeoTIFF format (.tif)\n\n4. Ensure all rasters have the same coordinate system and spatial extent\n\n5. After filling all inputs, proceed to the analysis modules"""
        self.info_text.setText(default_info)
        right_layout.addWidget(self.info_text)

        self.content_layout.addWidget(left_frame, 2)
        self.content_layout.addWidget(right_frame, 3)

        # Now that UI is ready, load conditions from DB
        if self.db_connection:
            self.load_conditions_from_db()

    def show_right_content(self, name):
        # Clear right frame
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
        if name == "Condition":
            self.show_condition_form()
        else:
            info = QTextEdit()
            info.setReadOnly(True)
            info.setText(f"{name} module coming soon.")
            self.right_layout.addWidget(info)

    def show_condition_form(self):
        # Main widget for condition form
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        # Select Condition
        select_box = QGroupBox("Select Condition :")
        select_layout = QVBoxLayout()
        select_box.setLayout(select_layout)
        self.condition_selector = QComboBox()
        self.condition_selector.setMinimumWidth(200)
        self.condition_selector.setPlaceholderText("Select a condition")
        self.condition_selector.activated.connect(self.load_condition)
        select_layout.addWidget(self.condition_selector)
        layout.addWidget(select_box)

        # Create Condition
        create_box = QGroupBox("Create Condition :")
        create_layout = QVBoxLayout()
        create_box.setLayout(create_layout)
        layout.addWidget(create_box)

        self.inputs = {}
        input_fields = [
            "Condition Name",
            "Flow Rasters",
            "Velocity Rasters",
            "Digital Elevatation Model",
            "Grain size rasters",
        ]
        for field_name in input_fields:
            field_layout = QHBoxLayout()
            label = QLabel(field_name)
            label.setMinimumWidth(180)
            field_layout.addWidget(label)
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"Enter {field_name.lower()}")
            field_layout.addWidget(input_field)
            if "raster" in field_name.lower() or "model" in field_name.lower():
                browse_btn = QPushButton("Browse")
                browse_btn.setMaximumWidth(80)
                browse_btn.clicked.connect(lambda checked, f=input_field: self.browse_file(f))
                field_layout.addWidget(browse_btn)
            create_layout.addLayout(field_layout)
            self.inputs[field_name] = input_field

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        create_condition_btn = QPushButton("Create Condition")
        create_condition_btn.setMinimumWidth(150)
        create_condition_btn.clicked.connect(self.create_condition)
        button_layout.addWidget(create_condition_btn)
        proceed_btn = QPushButton("Proceed to Analysis")
        proceed_btn.setMinimumWidth(150)
        proceed_btn.clicked.connect(self.proceed_to_analysis)
        button_layout.addWidget(proceed_btn)
        create_layout.addLayout(button_layout)

        # Info box
        self.info_text = QTextEdit()
        self.info_text.setPlaceholderText("Usage information will appear here...")
        self.info_text.setReadOnly(False)
        default_info = """River Architect - Getting Started\n\n1. Enter a Condition Name to identify your project/scenario\n\n2. Browse and select the required input raster files:\n - Flow Rasters: Hydrodynamic flow depth data\n - Velocity Rasters: Flow velocity data\n - Digital Elevation Model: Terrain elevation data\n - Grain Size Rasters: Substrate grain size distribution\n\n3. All raster files should be in GeoTIFF format (.tif)\n\n4. Ensure all rasters have the same coordinate system and spatial extent\n\n5. After filling all inputs, proceed to the analysis modules"""
        self.info_text.setText(default_info)
        layout.addWidget(self.info_text)

        self.right_layout.addWidget(container)

        # Now that UI is ready, load conditions from DB
        if self.db_connection:
            self.load_conditions_from_db()

    def show_database_content(self):
        """Display database conditions in the main content area as a separate tab."""
        # Left: list of conditions
        left_frame = QGroupBox("Database Conditions")
        left_layout = QVBoxLayout()
        left_frame.setLayout(left_layout)

        listw = QListWidget()
        self.db_list_widget = listw
        # populate from loaded conditions
        for name in self.conditions:
            listw.addItem(name)
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

        def refresh_list():
            self.load_conditions_from_db()
            listw.clear()
            for n in self.conditions:
                listw.addItem(n)

        def show_details(item):
            if not item:
                details.clear()
                return
            name = item.text()
            try:
                cursor = self.db_connection.cursor()
                cursor.execute(
                    "SELECT depth_rasters, velocity_rasters, digital_elevation_model, grain_size_raster FROM condition WHERE condition_name = %s;",
                    (name,)
                )
                rec = cursor.fetchone()
                cursor.close()
                if rec:
                    depth, vel, dem, grain = rec
                    details.setPlainText(f"Name: {name}\n\nDepth Rasters:\n{depth}\n\nVelocity Rasters:\n{vel}\n\nDEM:\n{dem}\n\nGrain Size:\n{grain}")
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
                self.load_conditions_from_db()
                try:
                    self.condition_selector.setCurrentText(name)
                except Exception:
                    pass
                self.populate_condition_fields(name)

        load_btn.clicked.connect(on_load)
        refresh_btn.clicked.connect(refresh_list)
        listw.currentItemChanged.connect(lambda cur, prev: show_details(cur))

        self.content_layout.addWidget(left_frame, 2)
        self.content_layout.addWidget(right_frame, 3)
    
    def browse_file(self, input_field):
        """Open file dialog to browse for raster files"""
        # Determine whether to allow multiple selection based on the
        # input field's placeholder text (detect Depth or Velocity fields).
        placeholder = input_field.placeholderText().lower()
        if "depth" in placeholder or "velocity" in placeholder:
            filenames, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Raster Files",
                "",
                "GeoTIFF Files (*.tif *.tiff);;All Files (*)"
            )
            if filenames:
                # Join multiple selected file paths with a semicolon for display/storage
                input_field.setText(";".join(filenames))
        else:
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Select Raster File",
                "",
                "GeoTIFF Files (*.tif *.tiff);;All Files (*)"
            )
            if filename:
                input_field.setText(filename)
    
    def proceed_to_analysis(self):
        """Handle proceed button click"""
        condition_name = self.inputs["Condition Name"].text()
        
        if not condition_name:
            self.info_text.append("\n⚠ Please enter a Condition Name before proceeding.")
            return
        
        self.info_text.append(f"\n✓ Condition '{condition_name}' ready for analysis.")
        self.info_text.append("Loading analysis modules...")

    def create_condition(self):
        """Handle create condition button click"""
        condition_name = self.inputs["Condition Name"].text()
        if not condition_name:
            self.info_text.append("\n⚠ Please enter a Condition Name before creating a condition.")
            return
        
        if condition_name in self.conditions:
            self.info_text.append(f"\n⚠ Condition '{condition_name}' already exists.")
            return

        depth_rasters = self.inputs["Depth Rasters"].text()
        velocity_rasters = self.inputs["Velocity Rasters"].text()
        dem = self.inputs["Digital Elevatation Model"].text()
        grain_size = self.inputs["Grain size rasters"].text()

        if not self.db_connection:
            self.info_text.append("\n⚠ Database connection not available.")
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute(
                "INSERT INTO condition (condition_name, depth_rasters, velocity_rasters, digital_elevation_model, grain_size_raster) VALUES (%s, %s, %s, %s, %s);",
                (condition_name, depth_rasters, velocity_rasters, dem, grain_size)
            )
            self.db_connection.commit()
            cursor.close()

            self.conditions.append(condition_name)
            self.condition_selector.addItem(condition_name)
            self.info_text.append(f"\n✓ Condition '{condition_name}' has been created and saved to the database.")
        except (Exception, Error) as error:
            self.info_text.append(f"\nError saving condition to database: {error}")
            self.db_connection.rollback()


    def populate_condition_fields(self, condition_name):
        """Fetch a condition record from the DB and populate the form fields."""
        if not condition_name:
            return
        if not self.db_connection:
            self.info_text.append("\n⚠ Database connection not available.")
            return
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(
                "SELECT depth_rasters, velocity_rasters, digital_elevation_model, grain_size_raster FROM condition WHERE condition_name = %s;",
                (condition_name,)
            )
            record = cursor.fetchone()
            cursor.close()
            if record:
                depth_rasters, velocity_rasters, dem, grain_size = record
                # Ensure keys exist in inputs
                self.inputs.setdefault("Condition Name", QLineEdit()).setText(condition_name)
                if "Depth Rasters" in self.inputs:
                    self.inputs["Depth Rasters"].setText(depth_rasters or "")
                if "Velocity Rasters" in self.inputs:
                    self.inputs["Velocity Rasters"].setText(velocity_rasters or "")
                if "Digital Elevatation Model" in self.inputs:
                    self.inputs["Digital Elevatation Model"].setText(dem or "")
                if "Grain size rasters" in self.inputs:
                    self.inputs["Grain size rasters"].setText(grain_size or "")
                self.info_text.append(f"\n✓ Loaded condition '{condition_name}' from database.")
            else:
                self.info_text.append(f"\n⚠ No database record found for '{condition_name}'.")
        except (Exception, Error) as error:
            self.info_text.append(f"\nError loading condition from database: {error}")

    def load_condition(self, index):
        """Handle condition selection from dropdown"""
        condition_name = self.condition_selector.itemText(index)
        self.inputs["Condition Name"].setText(condition_name)
        # Populate full fields from DB
        self.populate_condition_fields(condition_name)

    def init_db(self):
        try:
            connection = psycopg2.connect(
                port="5432",
                database="river_architect",
                user="postgres",
                password="database"
            )
            return connection
        except (Exception, Error) as error:
            self.info_text.append(f"\nError while connecting to PostgreSQL: {error}")
            return None

    def load_conditions_from_db(self):
        if not self.db_connection:
            return
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT condition_name FROM condition;")
            conditions = cursor.fetchall()
            cursor.close()
            
            self.conditions = [c[0] for c in conditions]
            # Clear selector to avoid duplicates
            try:
                self.condition_selector.clear()
            except Exception:
                pass
            self.condition_selector.addItems(self.conditions)
            self.info_text.append("\n✓ Successfully loaded conditions from the database.")
        except (Exception, Error) as error:
            self.info_text.append(f"\nError loading conditions from database: {error}")

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
                self.populate_condition_fields(name)
                dialog.accept()

        load_btn.clicked.connect(on_load)
        close_btn.clicked.connect(dialog.reject)

        listw.itemDoubleClicked.connect(lambda it: (self.condition_selector.setCurrentText(it.text()), self.populate_condition_fields(it.text()), dialog.accept()))

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