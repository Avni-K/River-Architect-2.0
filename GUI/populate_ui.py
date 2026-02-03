from PyQt5.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTextEdit,
)


def create_populate_condition_widget(parent=None):
    """
    Build the Populate Condition UI section.

    Returns
    -------
    container : QGroupBox
        The populated widget ready to add to layouts.
    refs : dict
        References to useful child widgets (buttons, info text, combo).
    """
    container = QGroupBox("Populate Condition", parent)
    main_layout = QHBoxLayout()
    container.setLayout(main_layout)

    # Left: action buttons
    actions_box = QGroupBox("Actions")
    actions_layout = QVBoxLayout()
    actions_box.setLayout(actions_layout)

    intro = QLabel("Run raster preparation tasks for the selected condition.")
    intro.setWordWrap(True)
    actions_layout.addWidget(intro)

    shear_btn = QPushButton("Create Shear stress Rasters")
    shear_btn.setMinimumHeight(40)
    actions_layout.addWidget(shear_btn)

    shield_btn = QPushButton("Create Sheild Stress Rasters")
    shield_btn.setMinimumHeight(40)
    actions_layout.addWidget(shield_btn)

    interp_box = QGroupBox("Interpolation")
    interp_layout = QHBoxLayout()
    interp_box.setLayout(interp_layout)
    interp_label = QLabel("Choose Interpolation Method:")
    interpolation_method_combo = QComboBox()
    interpolation_method_combo.addItems(["Kriging", "IDW", "Nearest Neighbour"])
    interp_layout.addWidget(interp_label)
    interp_layout.addWidget(interpolation_method_combo, 1)
    interp_layout.addStretch()
    actions_layout.addWidget(interp_box)

    depth_btn = QPushButton("Create Depth to Water table Rasters")
    depth_btn.setMinimumHeight(40)
    actions_layout.addWidget(depth_btn)

    morph_btn = QPushButton("Create Morphological Unit Rasters")
    morph_btn.setMinimumHeight(40)
    actions_layout.addWidget(morph_btn)

    actions_layout.addStretch()

    # Right: info placeholder
    info_box = QGroupBox("Information")
    info_layout = QVBoxLayout()
    info_box.setLayout(info_layout)
    info_text = QTextEdit()
    info_text.setReadOnly(True)
    info_text.setPlaceholderText("Information will appear here.")
    info_layout.addWidget(info_text)

    main_layout.addWidget(actions_box, 2)
    main_layout.addWidget(info_box, 3)

    refs = {
        "interpolation_method_combo": interpolation_method_combo,
        "info_text": info_text,
        "buttons": {
            "shear": shear_btn,
            "shield": shield_btn,
            "depth": depth_btn,
            "morph": morph_btn,
        },
    }

    return container, refs
