import sys
import os
import numpy as np
import json
from io import BytesIO
import zipfile

import time 
import tempfile

from websocket import WebSocketClient

start = time.time()

from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene,\
 QGraphicsRectItem, QWidget,QProgressDialog, QComboBox, QFileDialog, QMessageBox, QGraphicsProxyWidget, \
 QSplashScreen, QGraphicsLineItem
from PySide6.QtGui import QPen, QBrush, QColor, QImage, QPixmap, QMovie
from PySide6.QtCore import Qt, QTranslator, QEvent, QByteArray, Signal, QBuffer, QIODevice ,QThread, QObject, Signal, QRect

print(f"Finish importing PySide6 after: {time.time() - start}s")


DEFAULT_VALUE_OF_ITEM = None # Default value item GraphicsScene for layer >0
# NUM_ROW = 384
# NUM_COL = 480
DOT_SIZE = 2

# image = QImage(NUM_COL, NUM_ROW, QImage.Format_RGB32)
# image.fill(Qt.white)
os.makedirs(tempfile.gettempdir(), exist_ok=True) # create temp folder
TEMP_DIR = tempfile.TemporaryDirectory() # temp dir auto clean 

temp_graphs_scene = []

class ColorPickerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.num_col = 96   
        self.num_row = 128
        self.dot_size = 2
        self.pen_size = 0.1

        self.current_tool = None
        self.sceneChanged = Signal()
        self.setWindowTitle("LEDGO")

        screen = QApplication.primaryScreen().geometry()
        print( "screen resolution:", screen.width(),screen.height())
        
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        self.setMinimumWidth(self.screen_width*0.6)
        self.setMinimumHeight(self.screen_height*0.8)

        self.colors = ['#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF']
        self.topbar_widget = TopBarWidget(self.colors)
        self.topbar_widget.setObjectName("TopBarWidget")
        ## Handlers for topbar_widget
        self.topbar_widget.gray_slider.valueChanged.connect(self.handle_slider_change)
        self.topbar_widget.grid_border_checkbox.stateChanged.connect(self.handle_grid_border_change)
        
        self.layout_language = QHBoxLayout()
        self.language_dropdown = QComboBox()
        self.language_dropdown.addItem("日本語", "jap")
        self.language_dropdown.addItem("English", "eng")
        # self.topbar_widget.addLayer(self.language_dropdown)
        self.layout_language.addStretch(1)
        self.layout_language.addWidget(self.language_dropdown)

        # Connect the dropdown to the function
        self.language_dropdown.currentIndexChanged.connect(self.change_language)

        self.translator = QTranslator(app)
        self.graphics_scene = QGraphicsScene(self)
        self.graphics_view = ZoomableGraphicsView(self.graphics_scene, self)
        self.graphics_view.setMinimumSize(self.screen_width*0.3,self.screen_height*0.3)

        self.functions_widget = FunctionWidget(self,self.update_current_tool)
        functions_widget = QWidget()
        functions_widget.setLayout(self.functions_widget)
        functions_widget.setObjectName("FunctionsWidget")

        self.layer_preview_layout = QVBoxLayout()
        self.layer_widget = LayersWidget(self)
        self.layers_widget = QWidget()
        self.layers_widget.setLayout(self.layer_widget)
        self.layers_widget.setObjectName("LayersWidget")
        self.layers_widget.setFixedWidth(self.screen_width*0.155)
        self.layer_preview_layout.addWidget(self.layers_widget)

        self.graphics_view_layout = QHBoxLayout()
        self.graphics_view_layout.addWidget(functions_widget)
        self.graphics_view_layout.addWidget(self.graphics_view)
        self.graphics_view_layout.addLayout(self.layer_preview_layout)


        # Create a QLabel to display additional instructions
        self.instructions_label = QLabel(self.tr("*Click on the dot again to turn it OFF"))
        self.instructions_label.setObjectName("InstructionsLabel")
        self.instructions_label.setAlignment(Qt.AlignLeft)

        # Create a QLabel to display additional instructions
        self.version_label = QLabel(self.tr("Version 3.0.0"))
        self.version_label.setObjectName("VersionLabel")
        self.version_label.setAlignment(Qt.AlignLeft)

        self.footbar_widget = FootBarWidget()

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.topbar_widget)
        main_layout.addLayout(self.graphics_view_layout)

        main_control_layout = QHBoxLayout()
        main_control_layout.addWidget(self.instructions_label)
        main_control_layout.addWidget(self.footbar_widget)
        main_layout.addLayout(main_control_layout)

        main_bottom_layout = QHBoxLayout()
        main_bottom_layout.addWidget(self.version_label)
        main_bottom_layout.addLayout(self.layout_language)
        main_layout.addLayout(main_bottom_layout)
        self.setLayout(main_layout)

        self.graphics_view.viewport().installEventFilter(self)
        for label in self.topbar_widget.basic_color_labels:
            label.installEventFilter(self)

        self.selected_color = QColor("#000000")
        self.last_selected_square = None
       
        self.transparent = QColor.fromRgbF(0.000000, 0.000000, 0.000000, 0.000000)
        self.transparent_red = QColor(0, 0, 0, 0)
        self.text_threshold = [30,160]
        self.thread_init_layer = self.create_thread_init_item()
        self.draw_grid()
        self.list_item_layer_view = []
        self.list_item_layer_view_eyes = []
        self.current_processed_matrix = np.full((self.num_col, self.num_row), DEFAULT_VALUE_OF_ITEM)
        self.drawing = False
        self.thread_view = self.create_thread_view()

        self.thread_handle_layer = self.create_thread_handle()
        self.pen = QPen(Qt.white, 0.1)
        with open("translate.json", "r", encoding='utf-8') as file:
            self.data = json.load(file)
        self.language_code = "jp"
        self.change_language(0) # Set default language
        self.dict_rect_items_text = {}
        self.topbar_widget.curent_zoom_factor.setText(f"x{self.graphics_view.zoom_factor}")

    def create_thread_view(self):
        thread_view = QThread()
        worker_view = ViewLayer()
        worker_view.moveToThread(thread_view)
        thread_view.started.connect(lambda: worker_view.update_view(self.list_item_layer_view_eyes,
                                                                    self.layer_widget.get_combine_matrix_view_layer(),
                                                                    self.transparent_red, 
                                                                    self.convert_rect_to_grid, 
                                                                    self.pen,
                                                                    self.layer_widget.find_diff))
        worker_view.finished.connect(thread_view.quit)

        return thread_view

    def create_thread_handle(self):
        thread_handle_layer = QThread()
        worker = WorkerThread()
        worker.moveToThread(thread_handle_layer)
        thread_handle_layer.started.connect(lambda: worker.run_thread(self.set_layer_visibility))
        worker.finished.connect(thread_handle_layer.quit)
        return thread_handle_layer

    def create_thread_init_item(self):
        print("Start thread init item: OK")
        self.thread_init_item = QThread()
        self.worker_init_item = InitLayer(self.num_col,self.num_row)
        self.worker_init_item.moveToThread(self.thread_init_item)
        self.thread_init_item.started.connect(lambda: self.worker_init_item.generate(temp_graphs_scene))
        self.worker_init_item.updateScene.connect(self.update_scene_from_thread)
        self.worker_init_item.finished.connect(self.thread_init_item.quit)
        self.worker_init_item.finished.connect(self.on_worker_finished)
        
        return self.thread_init_item

    def on_worker_finished(self):
        self.set_layer_visibility()
        self.layer_widget.handle_view_layer_visibility()
        self.update_items_text_from_dict_rect(self.dict_rect_items_text)
        view_layers = [row_layout.itemAt(3).widget().text().split(" :")[0]
                for checkbox, row_layout in self.layer_widget.checkbox_to_row.items()
                if row_layout.itemAt(1).widget().isChecked()]
        if self.current_tool == "mouse":
            self.graphics_view.mouse_select_box()


    def update_items_text_from_dict_rect(self, list_rect):
        """update items text for each layer from dictionary rect 

        Args:
            list_rect (dict): dictionary rect
        """
        for layer, rect in list_rect.items():
            # rect is array [x, y ,w ,h]
            new_rect = QRect(rect[0], rect[1], rect[2], rect[3])
            selected_items = self.graphics_view.scene().items(new_rect, Qt.IntersectsItemShape)
            text_layer_items = [item for item in selected_items if item.zValue() == 1]
            self.layer_widget.layers[layer]["items_text"] = text_layer_items

    def createThread(self):
        """This function is not used.
           Keep for reference.
        Returns:
            QThread: a separated thread from main thread
        """
        print("Start thread: OK")
        global image
        
        thread = QThread()
        worker = PreviewManager()
        worker.moveToThread(thread)
        thread.started.connect(lambda: worker.draw(self.get_matrix_layer(), image))
        worker.updateImage.connect(self.update_preview_from_thread)
        worker.finished.connect(thread.quit)
        return thread
    
    def trigger_preview_update(self):
        """This function is not used.
           Keep for reference.
        """
        print("Start trigger")
        self.thread.start()
    
    def update_preview_from_thread(self):
        """This function is not used.
           Keep for reference.
        """
        start = time.time()
        global image
        image = QImage(self.num_col, self.num_row, QImage.Format_RGB32)
        image.fill(Qt.white)

        print(f"Finished draw: {time.time() - start} s")
        self.preview_widget.update_preview_by_image(image)
        print(f"Finish update preview: {time.time() - start} s")
    
    def reset_global(self):
        global temp_graphs_scene 
        temp_graphs_scene = []

    def update_scene_from_thread(self):
        start = time.time()
        global temp_graphs_scene
        for item in temp_graphs_scene:
            self.graphics_scene.addItem(item)

            # because items create from this thread -> update to list
            if item.zValue() == 1:
                self.list_item_layer_view.append(item)
                continue

            if item.zValue() == 2:
                self.list_item_layer_view_eyes.append(item)
        print(f"Finish update scene: {time.time() - start} s")


    def update_preview(self):
        # Create a QImage with the size 480x384 and fill it with white color
        start = time.time()
        global image
        image = QImage(self.num_col, self.num_row, QImage.Format_RGB32)
        image.fill(Qt.white)
        print(f"Finished draw: {time.time() - start} s")
        self.preview_widget.update_preview(self.get_matrix_layer())
        print(f"Finish update preview: {time.time() - start} s")

    def start_select_area_mode(self):
        self.graphics_view.setDragMode(QGraphicsView.RubberBandDrag)

    def start_draw_text_mode(self):
        self.topbar_widget.border_style_combo.setEnabled(True)
        # self.layer_widget.add_text_layer()
        self.graphics_view.setDragMode(QGraphicsView.RubberBandDrag)
    
    def start_draw_mode(self):
        self.graphics_view.setDragMode(QGraphicsView.NoDrag)
    
    def start_zoom_mode(self):
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)
    
    def get_matrix_layer(self):
        """Combine the matrix from selected boxes

        Returns:
            original_matrix_layer (numpy.ndarray): combined matrix from selected layers
        """
        # init default matrix
        original_matrix_layer =  np.full((self.num_col, self.num_row), DEFAULT_VALUE_OF_ITEM)
        # get selected boxes
        checked_boxes = [cb for cb in self.layer_widget.checkbox_to_row.keys() if cb.isChecked()]
        view_layers = [row_layout.itemAt(3).widget().text().split(" :")[0]
                        for checkbox, row_layout in self.layer_widget.checkbox_to_row.items()
                        if row_layout.itemAt(1).widget().isChecked()]

        self.previous_processed_matrix = np.copy(self.current_processed_matrix)
        # get selected layers name
        layer_selected_arr = []
        for cb in checked_boxes:
            row_layout = self.layer_widget.checkbox_to_row[cb]
            layer_name = row_layout.itemAt(3).widget().text().split(" :")[0]
            if layer_name in view_layers:
                layer_selected_arr.append(layer_name)
        # find value of layers in all layers
        layer_selected_dict =  {key: value for key, value in self.layer_widget.layers.items() if key in layer_selected_arr}
        sorted_layers = dict(sorted(layer_selected_dict.items(), key=lambda x: x[1]['z_index'] ))
        # if layer have "z_index" larger and a different color than the default value, matrix will pick its color
        for layer in sorted_layers.values():
            colors = layer["graphic_scene"]
            diff_default_color_idx = np.where(colors != DEFAULT_VALUE_OF_ITEM)
            original_matrix_layer[diff_default_color_idx] = colors[diff_default_color_idx]
        self.current_processed_matrix = original_matrix_layer
        return original_matrix_layer

    def set_layer_visibility(self, z_value=0, visible=False):
        """ Update view when checked layer or delete layer

        Args:
            z_value (int): z_index of layer.
            visible (bool): visible or invisible item.
        """
        matrix_color_layer = self.get_matrix_layer()
        col, row = self.current_processed_matrix.shape
        diff_idx = []
        for i in range(col):
            for j in range(row):
                if (self.previous_processed_matrix[i,j] != self.current_processed_matrix[i,j]):
                    diff_idx.append(j*col + i)

        print(f"Current view size: {len(self.list_item_layer_view)}")
        print("Index Change processed layer:", len(diff_idx))
        for idx in diff_idx:
            item = self.list_item_layer_view[idx]
            if item.zValue() == 0:
                continue
            transparent_brush = self.transparent_red
            if matrix_color_layer is None:
                # when no layer is selected
                item.setBrush(transparent_brush) 
                continue
            
            x_pos, y_pos = self.convert_rect_to_grid(item.rect())
            cell_color = matrix_color_layer[x_pos][y_pos]

            if cell_color != DEFAULT_VALUE_OF_ITEM:
                # set color for item
                transparent_brush = QColor(cell_color)
            transparent_brush = QBrush(QColor(transparent_brush))
            
            item.setBrush(transparent_brush)

    
    def reset_grid(self, col, row):
        # keep content
        self.list_item_layer_view = []
        self.list_item_layer_view_eyes = []
        self.current_processed_matrix = np.full((int(col), int(row)), DEFAULT_VALUE_OF_ITEM)
        self.layer_widget.current_view =  np.full((int(col), int(row)), DEFAULT_VALUE_OF_ITEM)
        old_layer = self.layer_widget.layers
        new_layer = {"Layer 0": {"z_index": 0, "graphic_scene": []}}
        self.dict_rect_items_text = {}
        for layer_name, value in old_layer.items():
            if layer_name != "Layer 0":
                new_layer[layer_name] = {}
                for key_value_layer, value_of_key in value.items():
                    if key_value_layer == "graphic_scene":
                        old_matrix = value_of_key
                        new_layer[layer_name][key_value_layer] = np.full((col, row), DEFAULT_VALUE_OF_ITEM)
                        new_matrix = new_layer[layer_name][key_value_layer]
                        min_x = min(old_matrix.shape[0], new_matrix.shape[0])
                        min_y = min(old_matrix.shape[1], new_matrix.shape[1])
                        new_matrix[:min_x, :min_y] = old_matrix[:min_x, :min_y]
                    elif key_value_layer == "items_text":
                        rect = [0, 0, 0, 0]
                        if len(value_of_key) == 1:
                            first_items = value_of_key[-1]
                            rect = [first_items.x(), first_items.y(), self.dot_size, self.dot_size]
                        elif len(value_of_key) > 1:
                            first_items = value_of_key[-1].rect()
                            last_items = value_of_key[0].rect()
                            rect = [first_items.x(), first_items.y(),
                                     abs(last_items.x() - first_items.x()), abs(last_items.y() - first_items.y()) ]
                        self.dict_rect_items_text[layer_name] = rect
                    else:
                        new_layer[layer_name][key_value_layer] = value_of_key
        self.layer_widget.layers = new_layer
        # self.layer_widget.delete_all_layers()
        self.graphics_scene.clear()
        x,y,w,h = self.graphics_scene.sceneRect().getRect()
        # Update display area
        self.graphics_scene.setSceneRect(x, 
                                         y, 
                                        (x + col)*self.dot_size,
                                        (y + row)*self.dot_size)

        self.worker_init_item.updateScene.disconnect()
        self.thread_view = self.create_thread_view()
        self.thread_init_layer = self.create_thread_init_item()
        self.draw_grid()

        self.drawing = False

        self.thread_handle_layer = self.create_thread_handle()



        # self.thread_init_layer.wait()

    def thread_finished(self):
        print("Thread init layer done.")
        self.set_layer_visibility()
        self.layer_widget.update_function_icons_state()

    def resizeEvent(self, event):
        self.footbar_widget.update_button_sizes(self.width(),self.height())
        self.layer_widget.update_scroll_area_size(self.layers_widget.height())
        self.topbar_widget.update_selected_color()
        # Automatically adjust the zoom level when the window is resized
        super().resizeEvent(event)

    def setGeometry(self, x, y, w, h):
        if self.locked_width and self.locked_height:
            # only allow resize both dimensions together
            if w != self.locked_width or h != self.locked_height:
                return
        super().setGeometry(x, y, w, h)
        self.locked_width = w
        self.locked_height = h
        self.geometryChanged.emit(x, y, w, h)

    def handle_grid_border_change(self,state):
        print("Grid checkbox state:", state)
        # State take value of 1 or 2 not Qt.Checked
        if state == 2:
            self.pen = QPen(Qt.black, 0.1)
            self.on_action()
        else:
            self.pen = QPen(Qt.white, 0.1)
            self.off_action()
        layer0_idx = self.num_col+self.num_row+1
        for item in self.list_item_layer_view_eyes:
            if isinstance(item, QGraphicsRectItem):
                item.setPen(self.pen)
                item.update()

    def handle_slider_change(self):
        gray_value = 255 - self.topbar_widget.gray_slider.value()
        pen_color = QColor(gray_value, gray_value, gray_value)

        ## Change only first layer
        for item in self.graphics_scene.items()[-1:]:
            if isinstance(item, QGraphicsRectItem):
                item.setBrush(QBrush(pen_color))
                item.update()

    def add_items_to_layer(self, layer_name):
        # Create items for new layer
        self.layer_widget.layers[layer_name]["graphic_scene"] = np.full((self.num_col, self.num_row), DEFAULT_VALUE_OF_ITEM)

    def draw_grid(self):
        # Clear scene
        self.graphics_scene.clear()
        # Get the current value of the slider
        gray_value = 255 - self.topbar_widget.gray_slider.value()
        pen_color = QColor(gray_value, gray_value, gray_value)
        if self.topbar_widget.grid_border_checkbox.isChecked():
            pen = QPen(Qt.black, 0.1)  # Set the border color to white and the width to 2 pixels
        else:
            pen = QPen(Qt.white, 0.1)  # Set the border color to white and the width to 2 pixels

        ## Init background
        rect_item = QGraphicsRectItem(0, 0, self.num_col * self.dot_size, self.num_row * self.dot_size)
        rect_item.setZValue(0)
        rect_item.setPen(pen)
        brush = QBrush(pen_color)
        rect_item.setBrush(brush)
        self.graphics_scene.addItem(rect_item)

        for row in range(self.num_row):
            y = row * self.dot_size
            x1 = 0
            x2 = x1 + self.num_col * self.dot_size
            item = QGraphicsLineItem(x1, y, x2, y)
            item.setZValue(0) # set 0 because if it's 3, drawing will get LineItem and can not draw
            item.setPen(pen)
            self.graphics_scene.addItem(item)

        for col in range(self.num_col):
            x = col * self.dot_size
            y1 = 0
            y2 = x1 + self.num_row * self.dot_size
            item = QGraphicsLineItem(x, y1, x, y2)
            item.setZValue(0) # set 0 because if it's 3, drawing will get LineItem and can not draw
            item.setPen(pen)
            self.graphics_scene.addItem(item) 

        print("Start generating")
        self.thread_init_layer.start()
        print("Current graph scene items: ", len(self.graphics_scene.items()))
        view_rect = self.graphics_view.sceneRect()
        self.graphics_view.fitInView(view_rect, Qt.KeepAspectRatio)


    def update_current_tool(self, tool_name):
        self.current_tool = tool_name
        print(f"Updated current_tool in ColorPickerApp: {self.current_tool}")

    @staticmethod
    def convert_rect_to_grid(rect, cell_size=2):
        x_item = int(rect.x() // cell_size)
        y_item = int(rect.y() // cell_size)
        return x_item, y_item
    
    def add_item_into_graphics_scene(self, x_pos, y_pos, z_index, cell_color, visible=False):
        # create item for graphics scene
        transparent_red = QColor(cell_color)
        transparent_brush = QBrush(transparent_red)
        x = x_pos * self.dot_size
        y = y_pos * self.dot_size
        rect_item = QGraphicsRectItem(x, y, self.dot_size, self.dot_size)
        # Use the border and fill color logic you have in draw_grid() if needed.
        pen = QPen(Qt.gray, 0.1)
        rect_item.setPen(QPen(self.transparent_red))
        rect_item.setBrush(transparent_brush)
        rect_item.setZValue(z_index)
        rect_item.setVisible(visible)
        self.graphics_scene.addItem(rect_item)
        return rect_item
    
    def draw_item(self, item, pen_color, transparent_brush, is_holding=False):
        x_pos, y_pos = self.convert_rect_to_grid(item.rect(), self.dot_size)
        z_value = item.zValue()
        print("drawing")
        # get list selected layer.
        # If empty list -> layer 0
        list_selected_layer = self.layer_widget.get_list_selected_layer_name()
        len_list_selected_layer = len(list_selected_layer)
        if len_list_selected_layer == 0:
            layer_name = "Layer 0"
            return
        

        elif len_list_selected_layer == 1:
            layer_name = list_selected_layer[0]
            # check color at position in layer is exist. turn off if exist
            if self.layer_widget.layers[layer_name]["graphic_scene"][x_pos][y_pos] != DEFAULT_VALUE_OF_ITEM and not is_holding:
                new_color = transparent_brush.color()
                self.layer_widget.set_color_at_pos(layer_name, x_pos, y_pos, DEFAULT_VALUE_OF_ITEM)
                self.layer_widget.current_view[x_pos][y_pos] = DEFAULT_VALUE_OF_ITEM
                self.current_processed_matrix[x_pos][y_pos] = DEFAULT_VALUE_OF_ITEM
            else:
                new_color = self.selected_color
                self.layer_widget.set_color_at_pos(layer_name, x_pos, y_pos, new_color.name())
                self.layer_widget.current_view[x_pos][y_pos] = new_color.name()
                self.current_processed_matrix[x_pos][y_pos] = new_color.name()
        else:
            # If multiple layers, can not draw
            return

        # set color in layer eye view
        for item_at_pos in self.graphics_view.scene().items(item.rect().center()):
            # TODO: update to (1,2) when fix view layer
            if item_at_pos.zValue() in (1,2):
                item_at_pos.setBrush(QBrush(new_color))
        item.setPen(self.pen)

        # Store the last selected square
        self.last_selected_square = item
        del x_pos
        del y_pos
        del item

    def eventFilter(self, obj, event):
        gray_value = 255 - self.topbar_widget.gray_slider.value()
        pen_color = QColor(gray_value, gray_value, gray_value)
        transparent_brush = QBrush(self.transparent_red)
        if obj == self.graphics_view.viewport() and event.type() == QEvent.MouseMove:
            pos = event.pos()
            item = self.graphics_view.itemAt(pos)
            if isinstance(item, QGraphicsRectItem):
                x_pos, y_pos = self.convert_rect_to_grid(item.rect(), self.dot_size)
                self.topbar_widget.mouse_position.setText(f"{int(y_pos + 1)} x {int(x_pos + 1)}")
            elif item is None:
                self.topbar_widget.mouse_position.setText('')

        # Handle mouse press event on the graphics view and basic color squares
        if obj == self.graphics_view.viewport() and event.type() == QEvent.MouseButtonPress and self.current_tool == "draw"  :

            self.drawing = True
            # Get the position of the mouse click
            pos = event.pos()
            item = self.graphics_view.itemAt(pos)
        
            # Check if the item is a QGraphicsRectItem
            if isinstance(item, QGraphicsRectItem):
                current_color = item.brush().color()

                self.draw_item(item, pen_color, transparent_brush, False)

        # Handle mouse press event on basic color squares
        elif obj in self.topbar_widget.basic_color_labels and event.type() == QEvent.MouseButtonPress:
            color = obj.palette().color(obj.backgroundRole())

            # Toggle the border for the clicked square
            if not obj.property("selected"):
                obj.setStyleSheet(
                    f"background-color: {color.name()}; border: 4px solid green; border-radius: 5px;")  # Add rounded corners and border
                obj.setProperty("selected", True)
                self.on_action()
            else:
                obj.setStyleSheet(
                    f"background-color: {color.name()}; border: 1px solid black; border-radius: 5px;")  # Add rounded corners
                obj.setProperty("selected", False)
                self.off_action()
 

            # Restore the border of the previously clicked square to black if applicable
            for label in self.topbar_widget.basic_color_labels:
                if label != obj and label.property("selected"):
                    label.setStyleSheet(
                        f"background-color: {label.palette().color(label.backgroundRole()).name()}; border: 1px solid black; border-radius: 5px;")  # Add rounded corners
                    label.setProperty("selected", False)

            # Set the selected color
            self.selected_color = color
        if obj == self.graphics_view.viewport() and event.type() == QEvent.MouseMove and self.drawing:
            pos = event.pos()
            item = self.graphics_view.itemAt(pos)
            if isinstance(item, QGraphicsRectItem):
                current_color = item.brush().color()
                self.draw_item(item, pen_color, transparent_brush, True)

        return super().eventFilter(obj, event)
    def import_gif(self, gif_path, target_layer="Layer 0"):
        """Create gif from path


        Args:
            gif_path (str): gif path
        """
        # read buffer from path
        with open(gif_path, 'rb') as file:
            gif_data = file.read()
        gif_layer = self.layer_widget.layers[target_layer]
        gif_layer["gif"] = QMovie()
        # create buffer
        buffer = QBuffer(self)
        buffer.open(QIODevice.ReadWrite)
        buffer.write(gif_data)
        buffer.seek(0)
        gif = gif_layer["gif"]
        gif.setDevice(buffer)

        gif_animation = QLabel()
        frame_gif = QPixmap(gif_path)

        frame_size = frame_gif.size()
        if frame_size.height() > self.num_row or frame_size.width() > self.num_col:
            QMessageBox.critical(self, self, self.data["message"]["Error"].get(self.language_code), self, self.data["message"]["Import_BMP_error"].get(self.language_code).replace("{0}", f"{self.num_col}x{self.num_row}" ))
            return
        gif.setScaledSize(frame_size*self.dot_size)

        gif.finished.connect(lambda:  gif.stop())
        gif.finished.connect(lambda: gif.jumpToFrame(0))


        self.gif = gif # set to self to write # TODO: remove after fix generate gif
        
        gif.jumpToFrame(0) # display first frame

        gif_animation.setMovie(gif)
        gif_animation.setFixedSize(frame_size*self.dot_size)
        proxy = QGraphicsProxyWidget()
        proxy.setWidget(gif_animation)
        # don't set 0 because conflict different process
        proxy.setZValue(2)
        self.graphics_scene.addItem(proxy)
        gif_layer["proxy"] = proxy

    def import_bmp(self, target_z_index=0):
        gray_value = 255 - self.topbar_widget.gray_slider.value()
        pen_color = QColor(gray_value, gray_value, gray_value)

        # Open a dialog box to select the BMP file
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        if self.language_code == "eng":
            file_dialog.setWindowTitle("Import BMP File")
        else:
            file_dialog.setWindowTitle("BMPファイルをインポートする")
        file_dialog.setNameFilter("BMP Files (*.bmp);; GIF File (*.gif)")

        if file_dialog.exec_() == QFileDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            self.layer_widget.add_layer(file_path.split(".")[-1].lower(), True)
            self.layer_widget.update_function_icons_state()
            list_selected_layer = self.layer_widget.get_list_selected_layer_name()
            layer_name = list_selected_layer[0]
            if file_path.split(".")[-1].lower() == "gif":
                self.import_gif(file_path, layer_name)
            else:
                image = QImage(file_path)
                # Check if the image was loaded successfully or not
                if image.isNull():
                    QMessageBox.critical(self, self.data["message"]["Error"].get(self.language_code), self.data["message"]["Import_BMP_fail"].get(self.language_code))
                    return
                
                # Check the size of the image
                len_list_selected_layer = len(list_selected_layer)
                if len_list_selected_layer == 0:
                        layer_name = "Layer 0"
                elif len_list_selected_layer == 1:
                    if image.height() > self.num_row or image.width() > self.num_col:
                        width_ratio = image.width() / self.num_col
                        height_ratio = image.height() / self.num_row
                        ratio = max(width_ratio, height_ratio)
                        image = image.scaled(image.width()//ratio, image.height()//ratio)

                    image_size = image.height()*image.width()
                    progress_dialog = QProgressDialog(self.data["progress"]["Importing_image"].get(self.language_code), self.data["progress"]["Cancel"].get(self.language_code), 0, image_size,
                                                    self)
                    progress_dialog.setWindowTitle("Processing")
                    progress_dialog.setWindowModality(Qt.WindowModal)

                    current_progress = 0
                    for y in range(image.height()):
                        for x in range(image.width()):
                            color = QColor(image.pixel(x, y)).name()
                            self.layer_widget.set_color_at_pos(layer_name,x,y,color)
                            current_progress  += 1
                            progress_dialog.setValue(current_progress)
                            QApplication.processEvents()
                    self.layer_widget.handle_view_layer_visibility() # update view eyes
                    self.set_layer_visibility() 
                    progress_dialog.close()

    def closeEvent(self, event):
        
        # if self.language_dropdown.currentIndex() == 0:
        message_box = QMessageBox()
        message_box.setWindowTitle(self.data["message"]["Close"].get(self.language_code))
        message_box.setText(self.data["message"]["save_project_question"].get(self.language_code))
        message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        message_box.setDefaultButton(QMessageBox.Cancel)
        message_box.button(QMessageBox.Yes).setText(self.data["message"]["Yes"].get(self.language_code))
        message_box.button(QMessageBox.No).setText(self.data["message"]["No"].get(self.language_code))
        message_box.button(QMessageBox.Cancel).setText(self.data["message"]["Cancel"].get(self.language_code))
        result = message_box.exec_()     
        if result == QMessageBox.Yes:
            current_dir = os.getcwd()
            temp_dir = os.path.join(current_dir, "temp")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            temp_file_path = os.path.join(temp_dir, "temp.proj")
            self.footbar_widget.save_project(temp_file_path)  
            event.accept()
        elif result == QMessageBox.No:
            event.accept()
            temp_file_path = os.path.join('temp', 'temp.proj')
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            event.accept()
        else:
            event.ignore()

    
    def on_action(self):
        # Change the window title when an action occurs
        if not self.windowTitle().endswith("(edited)"):
            self.setWindowTitle("LEDGO (edited)")
    
    def off_action(self):
        # Change the window title when an action off
        if len(list(self.layer_widget.layers.keys())) == 1:
            self.setWindowTitle("LEDGO")
    
    def change_language(self, language_code):
        self.language_code = self.language_dropdown.itemData(self.language_dropdown.currentIndex())
        if language_code == 0:
            self.retranslateUi("jap")
            self.tool_tips = ['ツールを選択', '色を選んで四角にクリックして描く', '領域選択ツール', 'テキストツール', 'マウスをスクロールして画像を拡大または縮小する', '画像ツールをインポートする']
            for label, tool_tip in zip(self.functions_widget.icon_labels, self.tool_tips):
                label.setToolTip(tool_tip)
            self.topbar_widget.border_style_combo.setItemText(0,"フィルター")
            self.topbar_widget.border_style_combo.setItemText(1,"カバードットをテキストの色に変更する")
            self.topbar_widget.border_style_combo.setItemText(2,"カバードットを背景に変更する")

        else:
            self.retranslateUi("eng")
            self.tool_tips = ['Select tool', 'Choose a color and click on the squares to draw', 'Area selection tool', 'Text tool', 'Scroll the mouse to zoom in or out of the image', 'Image tool']
            for label, tool_tip in zip(self.functions_widget.icon_labels, self.tool_tips):
                label.setToolTip(tool_tip)
            self.topbar_widget.border_style_combo.setItemText(0,"Filter")
            self.topbar_widget.border_style_combo.setItemText(1,"Change cover dots to text color")
            self.topbar_widget.border_style_combo.setItemText(2,"Change cover dots to background")
        self.topbar_widget.updateSize(self.num_col, self.num_row)

    def retranslateUi(self,language_code):
        for key, value in self.data.items():
            if key == "label":
                 for label, text in value.items():
                    value_text = text.get(language_code)
                    eval(f"self.{label}.setText('{value_text}')")

if __name__ == "__main__":
    start = time.time()
    # Create the application
    app = QApplication(sys.argv)
    print(f"Finish init application after: {time.time() - start}s")
    pixmap = QPixmap("./icons/loading-icon.png")
    splash = QSplashScreen(pixmap)
    splash.show()

    ws_client = WebSocketClient("ws://your-websocket-server-url")
    ws_client.connect()

    start = time.time()
    from zoomable_graphics_view import ZoomableGraphicsView
    from toolbar_widget import FunctionWidget
    from layer import LayersWidget
    from layer_thread import ViewLayer, WorkerThread
    from preview_thread import PreviewManager
    from topbar_widget import TopBarWidget
    from footbar_widget import FootBarWidget
    from init_thread import InitLayer
    print(f"Finish importing widgets after: {time.time() - start}s")

    # Create and show the main window
    window = ColorPickerApp()
    stylesheet_filename = os.path.join('stylesheet', 'stylesheet.css')
    with open(stylesheet_filename, "r") as file:
        stylesheet = file.read()
        app.setStyleSheet(stylesheet)
    window.show()
    splash.finish(window)
    temp_path = os.path.join('temp', 'temp.proj')
    if os.path.exists(temp_path):
        response = QMessageBox.question(window,
                                        window.data["message"]['load_project_text'].get(window.language_code),
                                        window.data["message"]['load_project_text'].get(window.language_code),
                                        QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            window.footbar_widget.load_project(temp_path)
            window.setWindowTitle("LEDGO (edited)")


    # Start the event loop
    ws_client.disconnect()
    sys.exit(app.exec())

