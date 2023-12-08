from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QSpinBox, QMessageBox, QWidget, QScrollArea, QPushButton
from PySide6.QtGui import QPixmap, QMovie, QImage, QColor
from PySide6.QtCore import QSize, Qt
import numpy as np
THUMBNAIL_SIZE = 24
DEFAULT_VALUE_OF_ITEM = None # Default value item GraphicsScene for layer >0
class LayersWidget(QVBoxLayout):
    def __init__(self, color_picker_app):
        super(LayersWidget, self).__init__()
        self.color_picker_app = color_picker_app
        self.layers = {"Layer 0": {"z_index": 0, "graphic_scene": []}}
        self.layer_counter = 1
        self.text_layer_counter = 1
        self.text_layer_z_index = 100  # Initialize the z-index for text layers
        self.inner_widget = QWidget()
        self.inner_layout = QVBoxLayout(self.inner_widget)

        # Create a QScrollArea to contain the above widget.
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)  # Make sure the widget inside is resizable
        self.scroll_area.setWidget(self.inner_widget)  
        parent_height = self.color_picker_app.height()
        parent_width = self.color_picker_app.screen_width
        self.scroll_area.setFixedWidth(parent_width*0.14)
        # Change main layout to contain QScrollArea instead of controls directly.
        self.addWidget(self.scroll_area) 
        self.checkbox_to_row = {}
        self.build_widget()
        for label in self.color_picker_app.functions_widget.icon_labels:
            if label.objectName() not in ["text", "image"]:
                label.setEnabled(False)

        self.current_view =  np.full((color_picker_app.num_col, color_picker_app.num_row), DEFAULT_VALUE_OF_ITEM)
        self.thumbnail_collection = {}

    def build_widget(self):
        for name, graphic in self.layers.items():
            self.add_layer_row(name, graphic.get("z_index", 0))

        add_layer_icon = self.create_icon_label('icons/icons8-add-30.png', 'Add a new layer')
        self.add_layer_text = QLabel("Add Layer")
        delete_layer_icon = self.create_icon_label('icons/icons8-trash-30.png', 'Delete selected layers')
        self.delete_layer_text = QLabel("Delete Selected Layer")

        font = self.add_layer_text.font()
        font.setPointSizeF(font.pointSizeF() * 1.2)
        self.add_layer_text.setFont(font)
        self.add_layer_text.setFixedWidth(100)
        self.delete_layer_text.setFont(font)
        self.delete_layer_text.setFixedWidth(150)

        add_layer_icon.mousePressEvent = lambda event: self.add_layer()
        self.add_layer_text.mousePressEvent = lambda event: self.add_layer()
        delete_layer_icon.mousePressEvent = lambda event: self.delete_layer()
        self.delete_layer_text.mousePressEvent = lambda event: self.delete_layer()

        add_layer_layout = QHBoxLayout()
        add_layer_layout.addWidget(add_layer_icon)
        add_layer_layout.addWidget(self.add_layer_text)
        add_layer_layout.addStretch(1)


        delete_layout = QHBoxLayout()
        delete_layout.addWidget(delete_layer_icon)
        delete_layout.addWidget(self.delete_layer_text)
        delete_layout.addStretch(1)

        add_text_layer_layout = QHBoxLayout()

        button_layout = QVBoxLayout()
        button_layout.addLayout(add_layer_layout)
        button_layout.addLayout(add_text_layer_layout)  # Include the new text layer controls
        button_layout.addLayout(delete_layout)

        self.create_select_all()
        self.addStretch()
        self.addLayout(button_layout)
    
    def update_scroll_area_size(self, app_height):
        scroll_area_height = app_height*0.65
        self.scroll_area.setFixedHeight(scroll_area_height)


    def create_icon_label(self, icon_path, tool_tip):
        label = QLabel()
        pixmap = QPixmap(icon_path).scaled(QSize(self.color_picker_app.width()/32, self.color_picker_app.width()/32), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)
        label.setFixedSize(QSize(self.color_picker_app.width()/32, self.color_picker_app.width()/32))
        label.setStyleSheet("border: none;")
        label.setToolTip(tool_tip)
        return label

    def create_select_all(self):
        top_layout = QVBoxLayout()
        self.row_layout_select_all = QHBoxLayout()
        self.label_select_all = QLabel("Select all")
        self.label_select_all.setAlignment(Qt.AlignLeft)
        checkbox = QCheckBox()
        checkbox.setFixedWidth(30)
        checkbox.stateChanged.connect(lambda checked, checkbox=checkbox: self.select_all_checkbox(checkbox))
        checkbox.stateChanged.connect(self.color_picker_app.on_action)
        self.row_layout_select_all.addWidget(checkbox)
        self.row_layout_select_all.addWidget(self.label_select_all)
        top_layout.addLayout(self.row_layout_select_all)
        self.insertLayout(0, top_layout)

    def unselect_all_checkbox_view(self):
        for other_checkbox, value in self.checkbox_to_row.items():
            # disconnect to avoid recall handle_layer_visibility
            other_checkbox.stateChanged.disconnect()
            other_checkbox.setChecked(False)
            # re-connect
            other_checkbox.stateChanged.connect(lambda checked, other_checkbox=other_checkbox: self.handle_layer_visibility(other_checkbox))
            other_checkbox.stateChanged.connect(self.update_function_icons_state)
            # view icon
            view_icon = value.itemAt(1).widget()
            view_icon.stateChanged.disconnect()
            view_icon.setChecked(False)
            view_icon.stateChanged.connect(self.handle_view_layer_visibility)
            view_icon.stateChanged.connect(self.color_picker_app.set_layer_visibility)
            view_icon.stateChanged.connect(self.update_function_icons_state)
            layer_name = value.itemAt(3).widget().text()
            self.set_thumbnail_for_layer(layer_name)
        
        # render
        self.handle_view_layer_visibility() # update view eyes
        self.color_picker_app.set_layer_visibility()

    def select_all_checkbox(self, checkbox):
        is_select_all = False
        if checkbox.isChecked():
            is_select_all = True
        else:
            is_select_all = False
        for other_checkbox in self.checkbox_to_row.keys():
            # disconnect to avoid recall handle_layer_visibility
            other_checkbox.stateChanged.disconnect()
            other_checkbox.setChecked(is_select_all)
            # re-connect
            other_checkbox.stateChanged.connect(lambda checked, other_checkbox=other_checkbox: self.handle_layer_visibility(other_checkbox))
            other_checkbox.stateChanged.connect(self.update_function_icons_state)
            other_checkbox.stateChanged.connect(self.color_picker_app.on_action)

        # render
        self.handle_view_layer_visibility() # update view eyes
        self.color_picker_app.set_layer_visibility()
    
    def handle_view_layer_visibility(self):
        self.color_picker_app.thread_view.start()


    def get_combine_matrix_view_layer(self):
        # get selected layers name
        # layer_selected_arr = [row_layout.itemAt(2).widget().text().split(" :")[0]
        #                 for checkbox, row_layout in self.checkbox_to_row.items()
        #                 if checkbox.isChecked()]
        self.previous_view = np.copy(self.current_view)
        gif_layers = [ layer for layer, value in self.layers.items() if value.get("type_img", "") == "gif"]
        view_layers = [row_layout.itemAt(3).widget().text().split(" :")[0]
                        for checkbox, row_layout in self.checkbox_to_row.items()
                        if row_layout.itemAt(1).widget().isChecked()]
        for gif_layer in gif_layers:
            proxy_gif = self.layers[gif_layer]["proxy"]
            if gif_layer in view_layers:
                proxy_gif.show()
            else:
                proxy_gif.hide()

        # init default matrix
        original_matrix_layer =  np.full((self.color_picker_app.num_col, self.color_picker_app.num_row), DEFAULT_VALUE_OF_ITEM)
        # combined_layer_name = list(set(layer_selected_arr + view_layers))
        combined_layer_name = list(set(view_layers))
        # find value of layers in all layers
        layer_selected_dict =  {key: value for key, value in self.layers.items() if key in combined_layer_name}
        sorted_layers = dict(sorted(layer_selected_dict.items(), key=lambda x: x[1]['z_index'] ))
        for layer in sorted_layers.values():
            colors = layer["graphic_scene"]
            diff_default_color_idx = np.where(colors != DEFAULT_VALUE_OF_ITEM)
            original_matrix_layer[diff_default_color_idx] = colors[diff_default_color_idx]
        self.current_view = original_matrix_layer
        return original_matrix_layer
    
    def find_diff(self):
        col,row = self.current_view.shape
        print(f"Current view shape:{self.current_view.shape}")
        diff_idx = []
        for i in range(col):
            for j in range(row):
                if (self.previous_view[i,j] != self.current_view[i,j]):
                    diff_idx.append(j*col + i)

        return diff_idx

    def handle_btn_play_gif(self, checkbox):
        """handle gif from checkbox (layer)

        Args:
            checkbox (QCheckBox): layer checkbox
        """
        layer_name = self.checkbox_to_row[checkbox].itemAt(3).widget().text().split(" :")[0]
        gif = self.layers[layer_name].get("gif", "")
        if isinstance(gif, QMovie):
            btn_play = self.checkbox_to_row[checkbox].itemAt(3).widget() # index 3 is play/pause button
            gif.finished.connect(lambda:  btn_play.setChecked(False))
            if btn_play.isChecked():
                gif.start()
            else:
                gif.setPaused(True)

    def create_btn_play_gif(self):
        btn_play = QCheckBox()
        btn_play.setChecked(False)
        btn_play.setObjectName("PlayGifCheckbox")
        return btn_play

    def handle_btn_eraser(self, layer_name):
        self.layers[layer_name]["graphic_scene"] = np.full(
            (self.color_picker_app.num_col, self.color_picker_app.num_row),
            DEFAULT_VALUE_OF_ITEM)
        self.handle_view_layer_visibility() # update view eyes
        self.color_picker_app.set_layer_visibility()
        print(self.thumbnail_collection)

    def create_view_icon(self):
        view_icon = QCheckBox()
        view_icon.setChecked(True)
        view_icon.stateChanged.connect(self.handle_view_layer_visibility)
        view_icon.stateChanged.connect(self.color_picker_app.set_layer_visibility)
        view_icon.stateChanged.connect(self.update_function_icons_state)
        view_icon.stateChanged.connect(self.color_picker_app.on_action)

        view_icon.setObjectName("ViewIconCheckbox")
        return view_icon
    
    def create_btn_with_object_name(self, object_name):
        """create button with object name

        Args:
            object_name (str): name of the button to set the style

        Returns:
            button (QPushButton): button with object name
        """
        button = QPushButton()
        button.setObjectName(object_name)
        return button
    
    def create_layer_thumbnail(self):
        """create layer thumbnail

        Returns:
            thumbnail (QLabel): thumbnail with pixmap
        """
        thumbnail = QLabel()
        pixmap = QPixmap(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
        pixmap.fill(Qt.white)
        thumbnail.setPixmap(pixmap)
        return thumbnail

    def handle_btn_change_index(self, layer_name, checkbox, is_btn_down=False):
        """Handles the click event of the move button to update the z-index value of the layer

        Args:
            layer_name (str): layer name
            checkbox (QCheckBox): checkbox in row layout
            is_btn_down (bool, optional): is the move down button. Defaults to False.
        """
        # sorted list z-index
        list_z_idx = sorted([layer_value["z_index"] for layer_value in self.layers.values()])
        # remove z-index of layer 0
        list_z_idx.remove(0)
        # get z-index of this layer and index in sorted list 
        current_z_index = self.layers[layer_name]["z_index"]
        current_index_in_list = list_z_idx.index(current_z_index)
        # get the row layout and index of this class in the row
        row_layout = self.checkbox_to_row[checkbox]
        row_widget = row_layout.parent()
        index_row_layout = self.inner_layout.indexOf(row_widget) # now is row_widget
        is_found = False # is new z-index found
        new_z_index = current_z_index
        if is_btn_down:
            if current_index_in_list > 0:
                # get previous value
                new_z_index= list_z_idx[current_index_in_list - 1]
                is_found = True
                index_row_insert = 1
        else:
            if current_index_in_list < len(list_z_idx) - 1:
                # get next value
                new_z_index= list_z_idx[current_index_in_list + 1]
                is_found = True
                index_row_insert = - 1
        
        if is_found:
            found_layer = self.get_layer_name_from_z_index(new_z_index)
            if found_layer is None:
                return
            # swap z-index
            self.layers[found_layer]["z_index"] = current_z_index
            self.layers[layer_name]["z_index"] = new_z_index
            # remove row layout
            self.inner_layout.removeWidget(row_widget)
            del self.checkbox_to_row[checkbox]
            # insert row layout in to new position
            self.inner_layout.addWidget(row_widget)
            self.inner_layout.insertWidget(index_row_layout + index_row_insert, row_widget)
            self.checkbox_to_row[checkbox] = row_layout
            # # update view
            self.handle_view_layer_visibility() # update view eyes
            self.color_picker_app.set_layer_visibility()
    def update_row_background(self, checkbox, row_widget):
        """Update the background color of the row widget based on the checkbox state."""
        if checkbox.isChecked():
            row_widget.setStyleSheet("background-color: lightgray;")
        else:
            row_widget.setStyleSheet("")

    def add_layer_row(self, name, z_value, is_checked=False):
        layer_name = QLabel(name)
        layer_name.mousePressEvent = lambda event: self.toggle_layer_checkbox(layer_name)

        
        row_layout = QHBoxLayout()
        checkbox = QCheckBox()
        checkbox.setChecked(is_checked)
        checkbox.stateChanged.connect(lambda: self.update_row_background(checkbox, row_widget))

        if name != "Layer 0":
            view_icon = self.create_view_icon()
            self.checkbox_to_row[checkbox] = row_layout

            checkbox.stateChanged.connect(lambda checked, checkbox=checkbox: self.handle_layer_visibility(checkbox))
            checkbox.stateChanged.connect(self.update_function_icons_state)
            checkbox.stateChanged.connect(self.color_picker_app.on_action)

            row_layout.addWidget(checkbox)
            row_layout.addWidget(view_icon)

            thumbnail = self.create_layer_thumbnail()
            self.thumbnail_collection[name] = thumbnail
            row_layout.addWidget(thumbnail)

        row_layout.addWidget(layer_name)
        if self.layers[name].get("layer_type", "image") == "image" and name != "Layer 0":

            if self.layers[name].get("type_img", "") == "gif":
                btn_play_gif = self.create_btn_play_gif()

                btn_play_gif.stateChanged.connect(lambda checked, checkbox=checkbox: self.handle_btn_play_gif(checkbox))
                row_layout.addWidget(btn_play_gif)
            else:
                btn_eraser = self.create_btn_with_object_name("EraserButton")
                btn_eraser.clicked.connect(lambda: self.handle_btn_eraser(name))
                row_layout.addWidget(btn_eraser)
            # add button move up, move down
            btn_move_up = self.create_btn_with_object_name("MoveUpButton")
            btn_move_up.clicked.connect(lambda: self.handle_btn_change_index(name, checkbox, False))
            btn_move_down = self.create_btn_with_object_name("MoveDownButton")
            btn_move_down.clicked.connect(lambda: self.handle_btn_change_index(name, checkbox, True))
            row_layout.addWidget(btn_move_up)
            row_layout.addWidget(btn_move_down)

        # Add to the top of the layout
        row_widget = QWidget()
        row_widget.setLayout(row_layout)
        self.inner_layout.addWidget(row_widget)
        self.inner_layout.insertWidget(0, row_widget)

        

    def add_layer(self, type_img="", is_checked=False):
        name = "Layer {}".format(self.layer_counter)
        z_value = self.layer_counter
        self.layers[name] = {}
        self.layers[name]["z_index"] = z_value
        self.layers[name]["layer_type"] = "image"
        self.layers[name]["color"] = ""
        self.layers[name]["type_img"] = type_img
        self.color_picker_app.add_items_to_layer(name)  # Assume a method exists for this

        # Deselect all other checkboxes before adding the new layer
        for checkbox in self.checkbox_to_row.keys():
            checkbox.setChecked(False)

        # Set is_checked to True for the new layer
        self.add_layer_row(name, z_value, is_checked=True)
        new_layer_checkbox = next(cb for cb, row in self.checkbox_to_row.items() if row.itemAt(3).widget().text() == name)
        new_layer_checkbox.stateChanged.emit(new_layer_checkbox.isChecked())
        self.layer_counter += 1

        self.color_picker_app.on_action()
        # self.color_picker_app.setWindowTitle("LED480x384 (edited)")
        # QMessageBox.information(None, 'Layer Created', f'Layer "{name}" with z-index {z_value} has been created.')

    def add_text_layer(self):
        name = "Text Layer {}".format(self.text_layer_counter)
        z_value = self.layer_counter
        self.layers[name] = {}
        self.layers[name]["z_index"] = z_value
        self.layers[name]["text"] = ""
        self.layers[name]["layer_type"] = "text"
        self.layers[name]["color"] = ""
        self.layers[name]["items_text"] = []
        self.layers[name]["rotate_angle"] = 0
        self.color_picker_app.add_items_to_layer(name)  # Assume a method exists for this
        new_layer_checkbox = self.add_text_layer_row(name, z_value)
        for other_checkbox in self.checkbox_to_row:
            other_checkbox.setChecked(False)

        # Activate the checkbox of the new text layer
        # Call this function after all other checkboxes have been disabled to avoid conflicts
        new_layer_checkbox.setChecked(True)
        self.layer_counter += 1

        self.text_layer_counter += 1
        self.color_picker_app.on_action()
    
    def add_text_layer_row(self, name, z_value, is_checked=False):
        row_layout = QHBoxLayout()
        checkbox = QCheckBox()
        checkbox.setChecked(is_checked)
        self.checkbox_to_row[checkbox] = row_layout
        checkbox.stateChanged.connect(lambda: self.update_row_background(checkbox, row_widget))
        checkbox.stateChanged.connect(lambda checked, checkbox=checkbox: self.handle_layer_visibility(checkbox))
        checkbox.stateChanged.connect(self.update_function_icons_state)
        checkbox.stateChanged.connect(self.color_picker_app.on_action)
        new_layer_checkbox = checkbox
        layer_name = QLabel(name)
        layer_name.mousePressEvent = lambda event: self.toggle_layer_checkbox(layer_name)

        row_layout.addWidget(checkbox)
        # second position
        view_icon = self.create_view_icon()
        row_layout.addWidget(view_icon)
        # add thumbnail
        thumbnail = self.create_layer_thumbnail()
        self.thumbnail_collection[name] = thumbnail
        row_layout.addWidget(thumbnail)

        row_layout.addWidget(layer_name)
        # add button move up, move down
        btn_move_up = self.create_btn_with_object_name("MoveUpButton")
        btn_move_up.clicked.connect(lambda: self.handle_btn_change_index(name, checkbox, False))
        btn_move_down = self.create_btn_with_object_name("MoveDownButton")
        btn_move_down.clicked.connect(lambda: self.handle_btn_change_index(name, checkbox, True))
        row_layout.addWidget(btn_move_up)
        row_layout.addWidget(btn_move_down)

        row_widget = QWidget()
        row_widget.setLayout(row_layout)
        self.inner_layout.addWidget(row_widget)
        self.inner_layout.insertWidget(0, row_widget)

        return new_layer_checkbox

    def delete_layer(self, show_msg=True):
        checked_boxes = [cb for cb in self.checkbox_to_row.keys() if cb.isChecked()]
        print(checked_boxes)
        if show_msg:
            if not checked_boxes:
                # Display a message if no rows are selected
                QMessageBox.warning(None, self.color_picker_app.data["message"]["Warning"].get(self.color_picker_app.language_code), self.color_picker_app.data["message"]["none_delete_layer"].get(self.color_picker_app.language_code))
                return
                
            # Confirm deletion
            response = QMessageBox.question(None, self.color_picker_app.data["message"]["delete_layer"].get(self.color_picker_app.language_code), self.color_picker_app.data["message"]["delete_layer_question"].get(self.color_picker_app.language_code), QMessageBox.Yes | QMessageBox.No)
            if response == QMessageBox.No:
                return
        
        # Collect all z_values to delete in a set for efficiency
        z_values_to_delete = set()

        for cb in checked_boxes:
            row_layout = self.checkbox_to_row[cb]
            print(row_layout)
            layer_name = row_layout.itemAt(3).widget().text().split(" :")[0]
            z_value = self.layers[layer_name].get("z_index",0)  # Get the z_value of the layer
            z_values_to_delete.add(z_value)
                
            while row_layout.count():
                item = row_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            self.removeItem(row_layout)
            deleted_layer = self.layers[layer_name]
            if deleted_layer.get("type_img", "") == "gif":
                self.color_picker_app.graphics_scene.removeItem(deleted_layer["proxy"])
            del self.layers[layer_name]
            del self.checkbox_to_row[cb]
            del self.thumbnail_collection[layer_name]
            row_widget = row_layout.parentWidget()
            if row_widget is not None:
                row_widget.deleteLater()

        # Update the layer_counter based on the highest existing layer number
        existing_layer_numbers = [int(name.split(" ")[-1]) for name in self.layers.keys() ]
        existing_text_layer_numbers = [int(name.split(" ")[-1]) for name in self.layers.keys() if name.startswith("Text")]
        text_layer = [name for name in self.layers.keys() if name.startswith("Text")]
        if existing_layer_numbers:
            self.layer_counter = max(existing_layer_numbers) + 1
        else:
            self.layer_counter = 1  # If all layers (except Layer 0) are deleted, reset the counter

        if existing_text_layer_numbers:
            self.text_layer_counter = max(existing_text_layer_numbers) + 1
        else:
            self.text_layer_counter = 1  # If all layers (except Layer 0) are deleted, reset the counter
        self.handle_view_layer_visibility() # update view eyes
        self.color_picker_app.set_layer_visibility("","") # update view
        self.update_function_icons_state()  
        self.color_picker_app.off_action()

    
    def delete_items_with_z_value(self, z_value):
        items_to_delete = [item for item in self.color_picker_app.graphics_scene.items() if item.zValue() == z_value]
        for item in items_to_delete:
            self.color_picker_app.graphics_scene.removeItem(item)


    def handle_layer_visibility(self, checkbox):

        # Get the corresponding layer name
        layer_name = self.checkbox_to_row[checkbox].itemAt(3).widget().text().split(" :")[0]
        z_value = self.layers[layer_name].get("z_index", 0)
        # # Update the visibility in the main app
        self.handle_view_layer_visibility() # update view eyes
        self.color_picker_app.thread_handle_layer.start()
        if not checkbox.isChecked():
            self.set_thumbnail_for_layer(layer_name)


        
    def update_function_icons_state(self):
        checked_boxes = [cb for cb in self.checkbox_to_row.keys() if cb.isChecked()]
        print(f"Number of checked_boxes: {len(checked_boxes)}")
        if len(checked_boxes) != 1:
            for label in self.color_picker_app.functions_widget.icon_labels:
                self.color_picker_app.current_tool = None
                if label.objectName() not in ["zoom", "text", "image"]:
                    label.setEnabled(False)
                    label.setStyleSheet(None)
            self.color_picker_app.graphics_view.release_mouse_select_box()        
        else:
            selected_checkbox = checked_boxes[0]
            row_layout = self.checkbox_to_row[selected_checkbox]
            layer_name_label = row_layout.itemAt(3).widget()
            eye_icon = row_layout.itemAt(1).widget()
            layer_name = layer_name_label.text().split(" :")[0]  

            is_text_layer = layer_name.startswith("Text Layer")
            is_text_content = False
            if is_text_layer:
                is_text_content = len(self.layers[layer_name]['text']) > 0
            for label in self.color_picker_app.functions_widget.icon_labels:
                if eye_icon.isChecked():
                    # Enable or disable specific labels based on whether it's a text layer
                    label.setEnabled(True)
                    if label.objectName() == "mouse":
                        self.color_picker_app.current_tool = "mouse"
                        self.color_picker_app.functions_widget.iconClicked(label)
                    if is_text_layer and not is_text_content:
                        self.color_picker_app.current_tool = "text"
                else:
                    if label.objectName() not in ["image", "text"]:
                        label.setEnabled(False)
                    self.color_picker_app.current_tool = None
                    label.setStyleSheet(None)
    
    def handle_z_index_change(self, spinbox, new_value):
        # Find the layer name corresponding to this spinbox
        layer_name = None
        for checkbox, row_layout in self.checkbox_to_row.items():
            if row_layout.itemAt(2).widget() == spinbox:
                layer_name = row_layout.itemAt(2).widget().text().split(" :")[0]
                break        
        if layer_name is None:
            # Could not find the layer, handle error
            return

        old_value = self.layers[layer_name]

        # Get all z-values excluding the current layer's value
        other_z_values = [z for key, z in self.layers.items() if key != layer_name]

        # Check for z-index duplicate        
        if new_value in other_z_values:
            QMessageBox.warning(None, 'Warning', 'This z-index is already in use. Please choose a different value.')
            spinbox.setValue(old_value)  # Reset the spinbox value
            return


        # Update the z-index of all items in the scene
        for item in self.color_picker_app.graphics_scene.items():
            if item.zValue() == old_value:
                item.setZValue(new_value)

        # Update the layers dictionary with the new z-value
        self.layers[layer_name]["z_index"] = new_value

    def get_selected_layer_z_index(self):
        checked_boxes = [cb for cb in self.checkbox_to_row.keys() if cb.isChecked()]
        if not checked_boxes:
            return 0  # Default to Layer 0
        layer_name = self.checkbox_to_row[checked_boxes[0]].itemAt(3).widget().text().split(" :")[0]
        return self.layers[layer_name].get("z_index")
    
    def toggle_layer_checkbox(self, layer_name_label):
        """
        Toggles the checkbox when the QLabel containing the layer name is clicked.
        
        Args:
            layer_name_label (QLabel): The QLabel containing the layer name.
        """
        for checkbox, row_layout in self.checkbox_to_row.items():
            if row_layout.itemAt(3).widget() == layer_name_label:
                checkbox.setChecked(not checkbox.isChecked())
                break

    def get_selected_layer_name(self):
        """
        Retrieve the name of the currently selected (checked) layer.

        :return: The name of the selected layer or None if no layer is selected.
        """
        # Iterate through all checkboxes in the self.checkbox_to_row dictionary
        for checkbox, row_layout in self.checkbox_to_row.items():
            if checkbox.isChecked():
                # If the checkbox is selected, get the layer name from the Label widget
                layer_name_label = row_layout.itemAt(3).widget() 
                layer_name = layer_name_label.text().split(" :")[0]  # Split the string to get the layer name
                return layer_name  

        # If no layers are selected, return None        
        return None
    
    def set_layers(self, layers_data):
        # Clear the current layers
        self.layers.clear()  # Assuming layers is a dictionary or similar data structure
        
        # Update layers based on the loaded data
        for layer_name, layer_info in layers_data.items():
            z_value = layer_info["z_value"]
            self.layers[layer_name]["z_index"] = z_value

    
    def clear_layers(self):
        # List to store the checkboxes that need to be removed (all except for "Layer 0")
        checkboxes_to_remove = []

        # Iterate through the checkbox_to_row dictionary to identify which rows (layers) need to be removed
        for checkbox, row_layout in self.checkbox_to_row.items():
            layer_name = row_layout.itemAt(3).widget().text().split(" :")[0]
            if layer_name != "Layer 0":
                checkboxes_to_remove.append(checkbox)

        # Remove the identified layers
        for checkbox in checkboxes_to_remove:
            row_layout = self.checkbox_to_row[checkbox]
            layer_name = row_layout.itemAt(3).widget().text().split(" :")[0]  # Get the name before removing items
            while row_layout.count():
                item = row_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            self.removeItem(row_layout)
            del self.layers[layer_name]
            del self.checkbox_to_row[checkbox]

        # Reset layer counter to 2 (assuming Layer 0 is 1 and always exists)
        self.layer_counter = 1
        self.text_layer_counter = 1
        self.text_layer_z_index = 100  # Initialize the z-index for text layers

    def get_list_selected_layer_name(self):
        """
        Retrieve a list of names of the currently selected (checked) layer.

        :return: A list of names of the selected layer or empty list if no layer is selected.
        """
        # Iterate through all checkboxes in the self.checkbox_to_row dictionary
        list_selected_layer = []
        for checkbox, row_layout in self.checkbox_to_row.items():
            if checkbox.isChecked():
                layer_name_label = row_layout.itemAt(3).widget()  
                layer_name = layer_name_label.text().split(" :")[0]  
                list_selected_layer.append(layer_name)
        print("Selected layer name:", list_selected_layer)
        return list_selected_layer
    
    def set_color_at_pos(self, layer_name, x, y, color):
        """Set color at position by layer name

        Args:
            layer_name (str): Layer name
            x (int): X postion
            y (int): Y position
            color (HexRgb): color. Example: "#000000"
        """
        self.layers[layer_name]["graphic_scene"][x][y] = color

    def delete_all_layers(self):
        # Create a list containing all the checkboxes (layers) that need to be deleted
        checkboxes_to_remove = [checkbox for checkbox in self.checkbox_to_row]
        # Delete each layer
        for checkbox in checkboxes_to_remove:
            row_layout = self.checkbox_to_row[checkbox]
            layer_name = row_layout.itemAt(3).widget().text().split(" :")[0]

            # Skip deleting "Layer 0"
            if layer_name == "Layer 0":
                continue

            # Remove widget from row_layout
            while row_layout.count():
                item = row_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            self.removeItem(row_layout)

            # Xóa layer khỏi self.layers và self.checkbox_to_row
            del self.layers[layer_name]
            del self.checkbox_to_row[checkbox]

        # Update counters and indexes
        self.layer_counter = 1
        self.text_layer_counter = 1
        self.text_layer_z_index = 100

    def get_layer_name_from_z_index(self, z_index):
        """get layer name from z-index, if not found return None

        Args:
            z_index (int): z-index of layer

        Returns:
            layer (str): layer name
        """
        for layer, layer_value in self.layers.items():
            if layer_value.get("z_index",0) == z_index:
                return layer
        return None
    
    def set_thumbnail_for_layer(self, layer_name):
        """Set thumbnail for layer from layer_name

        Args:
            layer_name (str): layer name
        """
        items = self.layers[layer_name].get("graphic_scene")
        width, height = items.shape
        image = QImage(width, height, QImage.Format_RGB32)
        image.fill(Qt.white)
        for x in range(width):
            for y in range(height):
                # Check if the square is in the selected squares
                # Update the pixel color
                if items[x][y] is not None:
                    image.setPixelColor(x, y, QColor(items[x][y]))
        image = image.scaled(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
        pixmap = QPixmap.fromImage(image)
        self.thumbnail_collection[layer_name].setPixmap(pixmap)
