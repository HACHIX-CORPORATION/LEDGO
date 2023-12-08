from PySide6.QtWidgets import  QApplication, QSizePolicy, QDialog, QSpinBox, QGraphicsRectItem, QProgressDialog, QComboBox, QHBoxLayout, QDoubleSpinBox, QDialogButtonBox, QFormLayout, QVBoxLayout, QLabel, QPushButton, QSlider, QCheckBox, QWidget, QColorDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import qGray, QColor, QPixmap
import numpy as np
from utils import get_std_threshold

class InputWidgetSizeDialogue(QDialog):
    def __init__(self, parent=None,default_scale_v=480, default_scale_h=384):
        super(InputWidgetSizeDialogue, self).__init__(parent)
        self.parents = parent
        self.initUI(default_scale_v, default_scale_h)
        if self.parents.parent().language_code == "eng":
            self.setWindowTitle("Change widget size")
        else:
            self.setWindowTitle("ウィジェットのサイズを変更する")

    def initUI(self, default_scale_v, default_scale_h):
        # Set up layout
        vbox = QVBoxLayout()

        # Create form layout to add fields
        formLayout = QFormLayout()

        # Scale input field
        self.scaleVSpinBox = QSpinBox()
        self.scaleVSpinBox.setRange(1, 480)  
        self.scaleVSpinBox.setValue(self.parents.parent().num_col)
        formLayout.addRow(self.parents.parent().data["input"]["width"].get(self.parents.parent().language_code), self.scaleVSpinBox)
        
        self.scaleHSpinBox = QSpinBox()
        self.scaleHSpinBox.setRange(1, 384)  
        self.scaleHSpinBox.setValue(self.parents.parent().num_row)
        formLayout.addRow(self.parents.parent().data["input"]["height"].get(self.parents.parent().language_code), self.scaleHSpinBox)    

        vbox.addLayout(formLayout)

        # OK and Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        
        # Kết nối sự kiện rejected của QDialogButtonBox với phương thức reject của QDialog
        # buttons.rejected.connect(self.reject)

        # Thêm QDialogButtonBox vào layout
        vbox.addWidget(buttons)

        # Truy cập nút "Ok" và "Cancel" và đặt văn bản cho chúng
        ok_button = buttons.button(QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        ok_button.setText(self.parents.parent().data["message"]["Yes"].get(self.parents.parent().language_code))
        cancel_button.setText(self.parents.parent().data["message"]["Cancel"].get(self.parents.parent().language_code))
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        # buttons.rejected.connect(self.reject)
        # vbox.addWidget(buttons)

        self.setLayout(vbox)

    def getInputs(self):
        return self.scaleVSpinBox.value(), self.scaleHSpinBox.value()


class TopBarWidget(QWidget):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        # Initialize top layout components
        self.select_color_label = QLabel("Select Color", self)
        
        # Set up the color layout with basic color labels
        self.basic_color_labels = []
        for color in colors:
            label = QLabel()
            label.setStyleSheet(f"background-color: {color}; border: 1px solid black; border-radius: 5px;")
            label.setProperty("selected", False)
            self.basic_color_labels.append(label)

        self.custom_color_button = QPushButton("Custom Color")
        self.custom_color_button.clicked.connect(self.pick_custom_color)
        self.custom_color_button.setEnabled(True)
        self.custom_color_button.setObjectName("CustomColorButton")

        self.color_layout = QHBoxLayout()
        for label in self.basic_color_labels:
            self.color_layout.addWidget(label)
        # Add the custom color button to the color layout
        self.color_layout.addWidget(self.custom_color_button)
        # Create slider for gray scale
        self.gray_slider = QSlider(Qt.Horizontal)
        self.gray_slider.setObjectName("GraySlider")
        self.gray_slider.setMinimum(10)
        self.gray_slider.setMaximum(160)
        self.gray_slider.setValue(80)  # Default value
        self.gray_slider.setMinimumWidth(100)

        # Create the white and black squares for the grid color slider
        self.white_square = QLabel()
        self.white_square.setObjectName("WhiteSquare")
        self.white_square.setFixedSize(20, 20)

        self.black_square = QLabel()
        self.black_square.setObjectName("BlackSquare")
        self.black_square.setFixedSize(20, 20)
        self.grid_color_text = QLabel("Grid Color")
        # Set up layouts for sliders and checkboxes
        self.slider_layout = QHBoxLayout()
        self.slider_layout.addWidget(self.grid_color_text)
        self.slider_layout.addWidget(self.white_square)
        self.slider_layout.addWidget(self.gray_slider)
        self.slider_layout.addWidget(self.black_square)
        self.slider_layout.addStretch()

        # Create checkbox for grid border
        self.grid_border_checkbox = QCheckBox()
        self.grid_border_checkbox.setObjectName("GridBorderCheckbox")
        self.grid_border_text = QLabel("Grid Border")
        self.grid_border_text.setObjectName("GridBorderTitle")
        self.border_layout = QHBoxLayout()
        self.border_layout.addWidget(self.grid_border_text)
        self.border_layout.addWidget(self.grid_border_checkbox)
        self.border_layout.addStretch()

        self.select_color_layout = QHBoxLayout()
        self.select_color_layout.addWidget(self.select_color_label)
        self.select_color_layout.addLayout(self.color_layout)
        self.select_color_layout.addStretch()

        self.sizeLayout = QHBoxLayout()
        self.currentSizeLabel = QLabel("Current canvas size (WxH): 96 x 128")
        self.currentSizeLabel.setObjectName("CurrentSizeLabel")

        self.widgetSizeButton = QPushButton("Change size", self)
        self.widgetSizeButton.setObjectName("WidgetSizeButton")
        self.widgetSizeButton.clicked.connect(self.showWidgetSizeDialogue)
        # current mouse and zoom
        mouse_icon = QLabel()
        mouse_icon_pixmap = QPixmap("./icons/icons8-select-cursor-24.png")
        mouse_icon.setPixmap(mouse_icon_pixmap)
        self.mouse_position = QLabel()
        self.mouse_position.setFixedWidth(80)
        zoom_icon = QLabel()
        zoom_icon_pixmap = QPixmap("./icons/icons8-zoom-50.png")
        zoom_icon_pixmap = zoom_icon_pixmap.scaled(24,24)
        zoom_icon.setPixmap(zoom_icon_pixmap)
        self.curent_zoom_factor = QLabel()
        self.sizeLayout.addWidget(self.currentSizeLabel)
        self.sizeLayout.addWidget(self.widgetSizeButton)
        self.sizeLayout.addWidget(mouse_icon)
        self.sizeLayout.addWidget(self.mouse_position)
        self.sizeLayout.addWidget(zoom_icon)
        self.sizeLayout.addWidget(self.curent_zoom_factor)
        self.sizeLayout.addStretch()




        # Create a combo box for selecting border styles
        self.border_style_combo = QComboBox()
        self.border_style_combo.setObjectName("BorderStyleCombo")
        # self.border_style_combo.setEnabled(False)
        self.border_style_combo.addItem("filter")
        self.border_style_combo.addItem("Change cover dots to text color")
        self.border_style_combo.addItem("Change cover dots to background")
        self.border_style_combo.setFixedWidth(400)
        self.border_style_combo.currentIndexChanged.connect(self.handle_filter_text)


        self.top_layout = QVBoxLayout()
        self.top_layout.addLayout(self.select_color_layout)
        # self.top_layout.addLayout(self.color_layout)
        self.grid_layout = QHBoxLayout()
        self.grid_layout.addLayout(self.slider_layout)
        self.grid_layout.addLayout(self.border_layout)
        self.top_layout.addLayout(self.grid_layout)

        # self.top_layout.addWidget(self.widgetSizeButton)
        self.top_layout.addLayout(self.sizeLayout)
        self.top_layout.addWidget(self.border_style_combo)

        # Maintain aspect ratio relative to the app when scaling
        self.label_ratio = 24
        self.custom_color_button_ratio = 11
        self.select_color_label_w_ratio = 10
        self.select_color_label_h_ratio = 30

        self.setLayout(self.top_layout)

    def get_widget(self):
        # Method to get the actual top bar widget
        return self

    def updateSize(self, col, row):
        """
        Update the widget's col and row values, and the label text.
        :param col: New column value.
        :param row: New row value.
        """
        # Update the label text with the new values
        if self.parent().language_code == "eng":
            text = "Current canvas size (WxH)"
        else:
            text = "現在のサイズ (WxH)"
        self.currentSizeLabel.setText(f"{text}: {col} x {row}")

    def showWidgetSizeDialogue(self):
        # Tạo và hiển thị InputWidgetSizeDialogue
        dialog = InputWidgetSizeDialogue(self)
        if dialog.exec_():
            self.parent().graphics_view.release_mouse_select_box()
            view_rect = self.parent().graphics_view.sceneRect()
            print("Preview view:",view_rect)
            scene_rect = self.parent().graphics_scene.sceneRect()
            print("Preview scene:",scene_rect)
            # Xử lý dữ liệu sau khi đối thoại được đóng
            new_width, new_height = dialog.getInputs()

            self.parent().reset_global()
            self.parent().num_col = int(new_width)
            self.parent().num_row = int(new_height)
  
            self.parent().reset_grid(int(new_width), int(new_height))
            self.updateSize(int(new_width),int(new_height))
            self.parent().graphics_view.zoom_factor = 1
            self.curent_zoom_factor.setText(f"x{1}")

    def update_selected_color(self):
        app_width = self.parent().width()
        app_height = self.parent().height()

        # Adjust the sizing calculations based on app height
        label_size = app_height / self.label_ratio
        button_width = app_height / self.custom_color_button_ratio

        self.select_color_label.setFixedWidth(app_width/self.select_color_label_w_ratio)
        self.select_color_label.setFixedHeight(app_height/self.select_color_label_h_ratio)
        self.grid_color_text.setFixedWidth(self.select_color_label.width())
        self.grid_color_text.setFixedHeight(self.select_color_label.height())
        self.grid_border_text.setFixedWidth(self.select_color_label.width())
        self.grid_border_text.setFixedHeight(self.select_color_label.height())

        for label in self.basic_color_labels:
            label.setFixedSize(label_size, label_size)

        self.custom_color_button.setFixedSize(button_width, label_size)
        font1 = self.custom_color_button.font()
        font1.setPointSize(int(label_size * 0.25))
        self.custom_color_button.setFont(font1)
        font = self.select_color_label.font()
        font.setPointSize(int(button_width * 0.2))
        self.select_color_label.setFont(font)

        self.grid_color_text.setFont(font)
        self.grid_border_text.setFont(font)
        self.currentSizeLabel.setFont(font)

        self.gray_slider.setFixedWidth(app_width*1/3)
    
    def pick_custom_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.custom_color_button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black; border-radius: 5px;")  # Add rounded corners
            self.parent().selected_color = color


    def handle_filter_text(self, index):
        list_selected_layer = self.parent().layer_widget.get_list_selected_layer_name()
        len_list_selected_layer = len(list_selected_layer)
        if len_list_selected_layer == 0:
            return

        progress_dialog = QProgressDialog(self.parent().data["progress"]["Processing_layers"].get(self.parent().language_code), 
                                        self.parent().data["progress"]["Abort"].get(self.parent().language_code), 
                                        0, len_list_selected_layer, self)
        progress_dialog.setWindowTitle("Processing")
        progress_dialog.setWindowModality(Qt.WindowModal)

        for i, layer_name in enumerate(list_selected_layer):
            progress_dialog.setValue(i+1)
            target_items = [item for item in self.parent().graphics_scene.items() if item.zValue() == 1 and isinstance(item, QGraphicsRectItem)]
            colors = [item.brush().color() for item in target_items if item.brush().color() != self.parent().transparent]
            if "Text" in layer_name:
                text_color = self.parent().layer_widget.layers[layer_name]["color"]
                if colors:
                    threshold = get_std_threshold(colors)
                    
                    for item in target_items:
                        x, y = self.parent().convert_rect_to_grid(item.rect(), self.parent().dot_size)
                        color = item.brush().color()
                        if color != self.parent().transparent:
                            current_color_value = np.array(color.getRgb()[:3])
                            if index == 1:
                                if np.any(current_color_value > threshold):
                                    color = None
                                else:
                                    color = text_color
                            elif index == 2:
                                if color != text_color:
                                    color = None
                                # else:
                                #     color = None
                            self.parent().layer_widget.set_color_at_pos(layer_name, x, y, color)
            else: # Nếu layer image
                 for item in target_items:
                    x, y = self.parent().convert_rect_to_grid(item.rect(), self.parent().dot_size)
                    color = item.brush().color()
                    if color != self.parent().transparent:
                        # Convert color to grayscale
                        gray_value = qGray(color.rgb())
                        if index == 1:
                            if gray_value < 200:
                                color = QColor(0, 0, 0)  
                            else:
                                color = self.parent().transparent #or (255,255,255) if you want to change bg to white
                        elif index == 2:
                            if gray_value < 100:
                                color = QColor(0, 0, 0)  
                            else:
                                color = self.parent().transparent 
                        self.parent().layer_widget.set_color_at_pos(layer_name, x, y, color)


            QApplication.processEvents()

        self.parent().layer_widget.handle_view_layer_visibility()  # update view eyes         
        self.parent().set_layer_visibility()   
        self.border_style_combo.setCurrentIndex(0)
        progress_dialog.close()