import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                             QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QFileDialog, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class RiverArchitectWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("River Architect")
        self.setGeometry(100, 100, 1000, 600)
        
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
        
        # Content layout (horizontal split)
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)
        
        # Left side - Input section
        left_group = QGroupBox("Please Feed :")
        left_layout = QVBoxLayout()
        left_group.setLayout(left_layout)
        
        # Store input fields for later access
        self.inputs = {}
        
        # Create input fields
        input_fields = [
            "Condition Name",
            "Flow Rasters",
            "Velocity Rasters",
            "Digital Elevatation Model",
            "Grain size rasters"
        ]
        
        for field_name in input_fields:
            field_layout = QHBoxLayout()
            
            # Label
            label = QLabel(field_name)
            label.setMinimumWidth(180)
            field_layout.addWidget(label)
            
            # Input field
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"Enter {field_name.lower()}")
            field_layout.addWidget(input_field)
            
            # Browse button (for raster/file inputs)
            if "raster" in field_name.lower() or "model" in field_name.lower():
                browse_btn = QPushButton("Browse")
                browse_btn.setMaximumWidth(80)
                browse_btn.clicked.connect(lambda checked, f=input_field: self.browse_file(f))
                field_layout.addWidget(browse_btn)
            
            left_layout.addLayout(field_layout)
            self.inputs[field_name] = input_field
        
        left_layout.addStretch()
        content_layout.addWidget(left_group)
        
        # Right side - Information text box
        right_group = QGroupBox("Information regarding usage")
        right_layout = QVBoxLayout()
        right_group.setLayout(right_layout)
        
        self.info_text = QTextEdit()
        self.info_text.setPlaceholderText("Usage information will appear here...")
        self.info_text.setReadOnly(False)
        
        # Set default information text
        default_info = """River Architect - Getting Started

1. Enter a Condition Name to identify your project/scenario

2. Browse and select the required input raster files:
   - Flow Rasters: Hydrodynamic flow depth data
   - Velocity Rasters: Flow velocity data
   - Digital Elevation Model: Terrain elevation data
   - Grain Size Rasters: Substrate grain size distribution

3. All raster files should be in GeoTIFF format (.tif)

4. Ensure all rasters have the same coordinate system and spatial extent

5. After filling all inputs, proceed to the analysis modules"""
        
        self.info_text.setText(default_info)
        right_layout.addWidget(self.info_text)
        
        content_layout.addWidget(right_group)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        proceed_btn = QPushButton("Proceed to Analysis")
        proceed_btn.setMinimumWidth(150)
        proceed_btn.clicked.connect(self.proceed_to_analysis)
        button_layout.addWidget(proceed_btn)
        
        main_layout.addLayout(button_layout)
        
        # Apply stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
            }
        """)
    
    def browse_file(self, input_field):
        """Open file dialog to browse for raster files"""
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

def main():
    app = QApplication(sys.argv)
    window = RiverArchitectWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()