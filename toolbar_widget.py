from PySide6.QtWidgets import QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap,QCursor
from PySide6.QtCore import QSize, Qt

class FunctionWidget(QVBoxLayout):

    def __init__(self, color_picker_app, callback=None):
        super().__init__()
    

        self.color_picker_app = color_picker_app  # Store the reference to ColorPickerApp
         
        icon_size = self.color_picker_app.width()/24
        icon_bg_size = self.color_picker_app.width()/19.2
        button_names = ['mouse', 'draw', 'select', 'text', 'zoom', 'image']
        button_icons = ['icons/icons8-select-cursor-24.png', 'icons/icons8-pencil-48.png', 'icons/icons8-select-area-67.png', 'icons/icons8-text-color-64.png', 'icons/icons8-zoom-50.png', 'icons/icons8-picture-80.png']
        self.tool_tips = ['Select tool', 'Choose a color and click on the squares to draw', 'Area selection tool', 'Text tool', 'Scroll the mouse to zoom in or out of the image', 'Image tool']

        scaled_size = QSize(icon_size, icon_size)
        bg_size = QSize(icon_bg_size, icon_bg_size)
        self.icon_labels = []

        for name, icon_path, tool_tip in zip(button_names, button_icons, self.tool_tips):
            label = QLabel()
            pixmap = QPixmap(icon_path).scaled(scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(pixmap)
            label.setObjectName(name)
            label.setAlignment(Qt.AlignCenter)
            label.setFixedSize(bg_size)
            label.setStyleSheet("border: none;")
            label.setToolTip(tool_tip)  # Set the tooltip for the QLabel

            # Connect mouse press event
            label.mousePressEvent = lambda event, lbl=label: self.iconClicked(lbl)

            self.addWidget(label)
            self.icon_labels.append(label)
        self.callback = callback

    def iconClicked(self, selected_label):
        self.cursor_shape = Qt.ArrowCursor
        if selected_label.objectName() == "image":
            target_z_index = self.color_picker_app.layer_widget.get_selected_layer_z_index()
            self.color_picker_app.import_bmp(target_z_index)
            self.cursor_shape = QCursor(QPixmap('icons/icons8-image-15.png'))
        elif selected_label.objectName() == "text" :
            self.color_picker_app.start_draw_text_mode()
            self.cursor_shape = QCursor(QPixmap('icons/icons8-text-color-15.png'))
        elif selected_label.objectName() == "select":
            self.color_picker_app.start_select_area_mode()  
            self.cursor_shape = QCursor(QPixmap('icons/icons8-select-area-15.png'))
        elif selected_label.objectName() == "draw":
            self.color_picker_app.start_draw_mode()
            self.cursor_shape = QCursor(QPixmap('icons/icons8-pencil-15.png'))
        elif selected_label.objectName() == "zoom":
            self.color_picker_app.start_zoom_mode()
            self.cursor_shape = QCursor(QPixmap('icons/icons8-zoom-15.png'))
        if selected_label.objectName() == "mouse":
            self.color_picker_app.graphics_view.mouse_select_box()
            self.cursor_shape = QCursor(QPixmap('icons/icons8-select-cursor-15.png'))
        else:
            self.color_picker_app.graphics_view.release_mouse_select_box()

        self.color_picker_app.graphics_view.setCursor( self.cursor_shape)

        for label in self.icon_labels:
            if label == selected_label:
                continue  # Skip the selected one
            label.setStyleSheet("border: none;")
        else:
            for label in self.icon_labels:
                if label == selected_label and 'border: 2px solid green;' not in label.styleSheet():
                    label.setStyleSheet("background-color : gray")
                    print(f"{selected_label.objectName()} is selected.")
                    self.current_tool = selected_label.objectName()
                else:
                    label.setStyleSheet("border: none;")
            if self.callback:
                self.callback(self.current_tool)
    
    def deselect_all_tools(self):
        """
        Deselect all tool icons (remove their highlighting).
        """
        for label in self.icon_labels:
            label.setStyleSheet("border: none;")  # Or any other style indicating "not selected"
        self.current_tool = None
        self.cursor_shape = Qt.ArrowCursor
        self.color_picker_app.graphics_view.setCursor( self.cursor_shape)

    def refresh_tools(self):
        for label in self.color_picker_app.functions_widget.icon_labels:
            if label.objectName() in ["text", "image"]:
                label.setEnabled(True)
            else:
                label.setEnabled(False)
        self.cursor_shape = Qt.ArrowCursor
        self.color_picker_app.graphics_view.setCursor( self.cursor_shape)