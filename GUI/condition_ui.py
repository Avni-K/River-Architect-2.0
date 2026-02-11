from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTextEdit,
    QFileDialog,
)

from Module_Services import condition_features


def create_condition_tab(window):
    """
    Build the Condition (create condition) UI.

    Parameters
    ----------
    window : QMainWindow
        Main window hosting the tab; expected to provide `browse_file`.

    Returns
    -------
    left_frame : QGroupBox
    right_frame : QGroupBox
    refs : dict
        Contains handy references: inputs, condition_selector, info_text.
    """
    # Left frame: select/create condition
    left_frame = QGroupBox()
    left_frame.setTitle("")
    left_layout = QVBoxLayout()
    left_frame.setLayout(left_layout)

    # Select Condition
    select_box = QGroupBox()
    select_layout = QHBoxLayout()
    select_box.setLayout(select_layout)

    select_label = QLabel("Select Condition :")
    select_label.setMinimumWidth(180)
    select_layout.addWidget(select_label)

    condition_selector = QComboBox()
    condition_selector.setMinimumWidth(200)
    condition_selector.setPlaceholderText("Select a condition")
    condition_selector.activated.connect(lambda idx: condition_features.load_condition(window, idx))
    select_layout.addWidget(condition_selector)
    select_layout.addStretch()
    left_layout.addWidget(select_box)

    # Visual separator
    or_label = QLabel("OR")
    or_label.setAlignment(Qt.AlignCenter)
    or_font = or_label.font()
    or_font.setBold(True)
    or_label.setFont(or_font)
    left_layout.addWidget(or_label)

    # Create Condition
    create_box = QGroupBox("Create Condition :")
    create_layout = QVBoxLayout()
    create_box.setLayout(create_layout)
    left_layout.addWidget(create_box)

    inputs = {}
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
            browse_btn.clicked.connect(lambda checked, f=input_field: browse_file(window, f))
            field_layout.addWidget(browse_btn)
        create_layout.addLayout(field_layout)
        inputs[field_name] = input_field
        if field_name == "Condition Name":
            # Unit selector directly under the condition name
            unit_layout = QHBoxLayout()
            unit_label = QLabel("Unit")
            unit_label.setMinimumWidth(180)
            unit_layout.addWidget(unit_label)
            unit_selector = QComboBox()
            unit_selector.addItems(["US Customary Unit", "SI Units"])
            unit_layout.addWidget(unit_selector)
            create_layout.addLayout(unit_layout)
            inputs["Unit"] = unit_selector

    optional_label = QLabel("Optional Inputs")
    optional_font = optional_label.font()
    optional_font.setBold(True)
    optional_label.setFont(optional_font)
    create_layout.addWidget(optional_label)

    optional_fields = ["WSE Folder", "Velocity Angle Folder", "Scour Raster", "Fill Raster", "Background Raster"]
    for field_name in optional_fields:
        field_layout = QHBoxLayout()
        label = QLabel(field_name)
        label.setMinimumWidth(180)
        field_layout.addWidget(label)
        input_field = QLineEdit()
        input_field.setPlaceholderText(f"Enter {field_name.lower()}")
        field_layout.addWidget(input_field)
        browse_btn = QPushButton("Browse")
        browse_btn.setMaximumWidth(80)
        if "folder" in field_name.lower():
            browse_btn.clicked.connect(lambda checked, f=input_field: browse_file(window, f, select_folder=True))
        elif "background raster" in field_name.lower():
            browse_btn.clicked.connect(
                lambda checked, f=input_field: browse_file(
                    window,
                    f,
                    file_filter="Raster Files (*.tif *.tiff *.asc *.pgw *.jgw);;All Files (*)",
                )
            )
        else:
            browse_btn.clicked.connect(
                lambda checked, f=input_field: browse_file(
                    window, f, file_filter="GeoTIFF Files (*.tif *.tiff);;All Files (*)"
                )
            )
        field_layout.addWidget(browse_btn)
        create_layout.addLayout(field_layout)
        inputs[field_name] = input_field

    # Bottom buttons
    button_layout = QHBoxLayout()
    button_layout.addStretch()
    create_condition_btn = QPushButton("Create Condition")
    create_condition_btn.setMinimumWidth(150)
    create_condition_btn.clicked.connect(lambda checked=False: condition_features.create_condition(window))
    button_layout.addWidget(create_condition_btn)
    # Proceed button placed below the create box
    proceed_btn = QPushButton("Proceed to Analysis")
    proceed_btn.setMinimumWidth(150)
    proceed_btn.clicked.connect(lambda checked=False: condition_features.proceed_to_analysis(window))
    left_layout.addWidget(proceed_btn)
    create_layout.addLayout(button_layout)

    left_layout.addStretch()

    # Right frame: information
    right_frame = QGroupBox("Information regarding usage")
    right_layout = QVBoxLayout()
    right_frame.setLayout(right_layout)
    info_text = QTextEdit()
    info_text.setPlaceholderText("Usage information will appear here...")
    info_text.setReadOnly(False)
    default_info = """River Architect - Getting Started\n\n1. Enter a Condition Name to identify your project/scenario\n\n2. Browse and select the required input raster files:\n - Flow Rasters: Hydrodynamic flow depth data\n - Velocity Rasters: Flow velocity data\n - Digital Elevation Model: Terrain elevation data\n - Grain Size Rasters: Substrate grain size distribution\n\n3. All raster files should be in GeoTIFF format (.tif)\n\n4. Ensure all rasters have the same coordinate system and spatial extent\n\n5. After filling all inputs, proceed to the analysis modules"""
    info_text.setText(default_info)
    right_layout.addWidget(info_text)

    refs = {
        "inputs": inputs,
        "condition_selector": condition_selector,
        "info_text": info_text,
    }

    return left_frame, right_frame, refs


def browse_file(window, input_field, select_folder=False, file_filter="GeoTIFF Files (*.tif *.tiff);;All Files (*)"):
    """Open file dialog to browse for raster files or folders."""
    if select_folder:
        folder = QFileDialog.getExistingDirectory(window, "Select Folder", "")
        if folder:
            input_field.setText(folder)
        return

    placeholder = input_field.placeholderText().lower()
    if "depth" in placeholder or "velocity" in placeholder:
        filenames, _ = QFileDialog.getOpenFileNames(window, "Select Raster Files", "", file_filter)
        if filenames:
            input_field.setText(";".join(filenames))
    else:
        filename, _ = QFileDialog.getOpenFileName(window, "Select Raster File", "", file_filter)
        if filename:
            input_field.setText(filename)
   
