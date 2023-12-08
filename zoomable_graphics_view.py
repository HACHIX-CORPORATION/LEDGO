import math
from PySide6.QtWidgets import QGraphicsView, QGraphicsRectItem, QInputDialog, \
    QGraphicsItem, QMessageBox, QTextEdit, QHBoxLayout, QLabel, QPushButton

from PySide6.QtGui import QPainter, QFont, QBrush, QImage, QColor, QFontMetrics, QPen, QTransform, QFontDatabase
from PySide6.QtCore import Qt,QPointF, QRectF, QRect

from PySide6.QtWidgets import QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QDoubleSpinBox, QVBoxLayout
from utils import get_width_height_from_text, get_max_font_size, get_font_family
import numpy as np
import os
DEFAULT_VALUE_OF_ITEM = None # Default value item GraphicsScene for layer >0
MIN_FONT_SIZE = 8 # min size text of paint is 8 
DEFAULT_FONT_SIZE = 16

class MultiInputDialogue(QDialog):
    def __init__(self, parent=None, default_text="", default_scale_v=1.0,
                default_scale_h=1.0, default_rotation=0.0, font_size=None, text_color=None):
        super(MultiInputDialogue, self).__init__(parent)
        self.zoomable = parent
        self.selected_text_color = text_color
        self.initUI(default_text, default_scale_v, default_scale_h, default_rotation, font_size)
        if self.zoomable.parent.language_code == "eng":
            self.setWindowTitle("Edit")
        else:
            self.setWindowTitle("編集")


    def initUI(self, default_text, default_scale_v, default_scale_h, default_rotation, font_size=None):
        # Set up layout
        vbox = QVBoxLayout()

        # Create form layout to add fields
        formLayout = QFormLayout()

        # Text input field
        self.textLineEdit = QTextEdit()
        self.textLineEdit.setPlainText(default_text)
        formLayout.addRow(self.zoomable.parent.data["input"]["Text"].get(self.zoomable.parent.language_code), self.textLineEdit)

        # Font size
        self.font_spinbox = QDoubleSpinBox()
        self.font_spinbox.setRange(MIN_FONT_SIZE, 384.0)
        self.font_spinbox.setSingleStep(0.1)
        if font_size is not None:
            self.font_spinbox.setValue(font_size)
            formLayout.addRow(self.zoomable.parent.data["input"]["Font_size"].get(self.zoomable.parent.language_code), self.font_spinbox)

        # Scale input field
        self.scaleVSpinBox = QDoubleSpinBox()
        self.scaleVSpinBox.setRange(0.1, 100) 
        self.scaleVSpinBox.setSingleStep(0.1) 
        self.scaleVSpinBox.setValue(default_scale_v)
        formLayout.addRow(self.zoomable.parent.data["input"]["Scale_v"].get(self.zoomable.parent.language_code), self.scaleVSpinBox)
        
        self.scaleHSpinBox = QDoubleSpinBox()
        self.scaleHSpinBox.setRange(0.1, 100)  
        self.scaleHSpinBox.setValue(default_scale_h)
        self.scaleHSpinBox.setSingleStep(0.1)
        formLayout.addRow(self.zoomable.parent.data["input"]["Scale_h"].get(self.zoomable.parent.language_code), self.scaleHSpinBox)

        # Rotation input field
        self.rotationSpinBox = QDoubleSpinBox()
        self.rotationSpinBox.setRange(-360.0, 360.0)
        self.rotationSpinBox.setValue(default_rotation)
        self.rotationSpinBox.setSingleStep(0.1)
        formLayout.addRow(self.zoomable.parent.data["input"]["Rotation"].get(self.zoomable.parent.language_code), self.rotationSpinBox)
        # Select color
        if self.selected_text_color is not None:

            self.select_color = QHBoxLayout()
            self.list_button_color = []
            for color in self.zoomable.parent.colors:
                button = QPushButton()
                if color.lower() == self.selected_text_color:
                    button.setStyleSheet(
                    f"background-color: {color}; border: 4px solid green; border-radius: 5px;")  # Add rounded corners and border
                    button.setProperty("selected", True)
                else:
                    button.setStyleSheet(f"background-color: {color}; border: 1px solid black; border-radius: 5px;")
                    button.setProperty("selected", False)
                button.clicked.connect(self.on_click_button_color(button))
                self.list_button_color.append(button)
                self.select_color.addWidget(button)

            formLayout.addRow(self.zoomable.parent.data["label"]["topbar_widget.select_color_label"].get(self.zoomable.parent.language_code), self.select_color)
        # end select color
        vbox.addLayout(formLayout)

        # OK and Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

        # Add QDialogButtonBox to layout
        vbox.addWidget(buttons)

        # Access the "Ok" and "Cancel" buttons and set text for them
        ok_button = buttons.button(QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        ok_button.setText(self.zoomable.parent.data["message"]["Yes"].get(self.zoomable.parent.language_code))
        cancel_button.setText(self.zoomable.parent.data["message"]["Cancel"].get(self.zoomable.parent.language_code))
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)


        self.setLayout(vbox)

    def getInputs(self):
        return self.textLineEdit.toPlainText(), self.font_spinbox.value(), self.scaleVSpinBox.value(), self.scaleHSpinBox.value(), self.rotationSpinBox.value()

    def handle_click_button(self, button):
        color = button.palette().color(button.backgroundRole())
        print(color)
        print("Property: ",button.property("selected"))
        if not button.property("selected"):
            button.setStyleSheet(
                f"background-color: {color.name()}; border: 4px solid green; border-radius: 5px;")  # Add rounded corners and border
            button.setProperty("selected", True)
        else:
            button.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid black; border-radius: 5px;")  # Add rounded corners
            button.setProperty("selected", False)
        for other_button in self.list_button_color:
            if other_button != button and other_button.property("selected"):
                other_button.setStyleSheet(
                    f"background-color: {other_button.palette().color(other_button.backgroundRole()).name()}; border: 1px solid black; border-radius: 5px;")  # Add rounded corners
                other_button.setProperty("selected", False)
        self.selected_text_color = color.name()
    
    def on_click_button_color(self, button):
        return lambda: self.handle_click_button(button)

class InputTextDialog(QDialog):
    def __init__(self, parent=None, default_text="", font_size=MIN_FONT_SIZE, topleft_pos = (0,0)):
        super(InputTextDialog, self).__init__(parent)
        self.zoomable = parent
        self.topleft_pos = topleft_pos
        self.setWindowTitle(self.zoomable.parent.data["input"]["Enter_text"].get(self.zoomable.parent.language_code))
        self.initUI(default_text, font_size)
    
    def initUI(self, default_text, font_size):
        # Set up layout
        vbox = QVBoxLayout()

        # Create form layout to add fields
        formLayout = QFormLayout()
        # Text input field
        self.textLineEdit = QTextEdit()
        self.textLineEdit.setPlainText(default_text)
        formLayout.addRow(self.zoomable.parent.data["input"]["Text"].get(self.zoomable.parent.language_code), self.textLineEdit)

        # Scale input field
        self.font_spinbox = QDoubleSpinBox()
        self.font_spinbox.setRange(0, self.zoomable.parent.num_row)  
        self.font_spinbox.setValue(font_size)
        formLayout.addRow(self.zoomable.parent.data["input"]["Font_size"].get(self.zoomable.parent.language_code), self.font_spinbox)

        vbox.addLayout(formLayout)

        # OK and Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        
        # Connect the QDialogButtonBox's rejected event to the QDialog's reject method
        buttons.rejected.connect(self.reject)

        # Add QDialogButtonBox to the layout
        vbox.addWidget(buttons)

        # Access the "Ok" and "Cancel" buttons and set text for them
        ok_button = buttons.button(QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        ok_button.setText(self.zoomable.parent.data["message"]["Yes"].get(self.zoomable.parent.language_code))
        cancel_button.setText(self.zoomable.parent.data["message"]["Cancel"].get(self.zoomable.parent.language_code))
        ok_button.clicked.connect(self.on_accept)
        cancel_button.clicked.connect(self.reject)

        self.setLayout(vbox)

    def on_accept(self):
        text = self.textLineEdit.toPlainText()
        dot_size = self.zoomable.parent.dot_size
        x_first, y_first = self.topleft_pos
        x_coord, y_coord = math.ceil(x_first)/dot_size, math.ceil(y_first)/dot_size
        # check height width oversize
        width, height = get_width_height_from_text(text, self.font_spinbox.value(), self.zoomable.font_family)
        max_height = self.zoomable.parent.num_row
        max_width = self.zoomable.parent.num_col
        if y_coord + height > max_height or x_coord + width > max_width:
            font_size = get_max_font_size(text, max_width - x_coord, max_height - y_coord, self.zoomable.font_family)
            self.font_spinbox.setValue(font_size)
        
        self.accept()

    def getInputs(self):
        print("New font:", self.font_spinbox.value())
        return self.textLineEdit.toPlainText(), self.font_spinbox.value()


class CustomRectItem(QGraphicsRectItem):
    def __init__(self, rect, graphics_view, *args, **kwargs):
        super().__init__(rect, *args, **kwargs)  # rect is the rectangle dimensions
        self.graphics_view = graphics_view 
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)  
        print(f"Mouse released after move customRect: {event}")
        self.graphics_view.handle_custom_rect_item_released()



class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene)
        self.parent = parent

        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.zoom_factor_base = 1.25  # or any desired zoom factor
        self.dot_size = 2
        self.last_known_rubberband_rect = 0
        self.layer_color = QColor.fromRgbF(0.313726, 0.313726, 0.313726, 1.000000)
        self.transparent_color = QColor(0, 0, 0, 0)
        self.num_col = self.parent.num_col
        self.num_row = self.parent.num_row
        self.text_color = None
        self.is_selected = False
        self.zoom_factor = 1
        self.font_family = get_font_family()
    
    def wheelEvent(self, event):
        if self.parent.current_tool == "zoom":
            zoom_in_factor = self.zoom_factor_base
            zoom_out_factor = 1 / self.zoom_factor_base

            if event.angleDelta().y() > 0:
                scale_factor  = zoom_in_factor
            else:
                scale_factor  = zoom_out_factor
            self.zoom_factor *= scale_factor

            self.scale(scale_factor , scale_factor )
            self.parent.topbar_widget.curent_zoom_factor.setText(f"x{self.zoom_factor:.2f}")

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self.dragMode() == QGraphicsView.RubberBandDrag:
            # Stores the last known rubber band rect size
            self.last_known_rubberband_rect = self.rubberBandRect()

    def mouse_select_box(self):
        """Create object box in layer when click "Mouse button"
        """
        self.parent.graphics_view.setDragMode(QGraphicsView.RubberBandDrag)
        layer_name = self.parent.layer_widget.get_list_selected_layer_name()[0]
        graphic_scence = self.parent.layer_widget.layers[layer_name].get("graphic_scene", 
                                                                         np.full((self.parent.num_col, self.parent.num_row), DEFAULT_VALUE_OF_ITEM))
        item_indices = np.where(graphic_scence != DEFAULT_VALUE_OF_ITEM)
        if len(item_indices[0]) > 0 and len(item_indices[1]) > 0 and not self.is_selected:
            self.is_selected = True # flag to avoid create multiple
            padding_vertical = 0
            if self.parent.layer_widget.layers[layer_name]["layer_type"] == "text":
                font_size = self.parent.layer_widget.layers[layer_name].get("font_size", MIN_FONT_SIZE)
                if self.font_family is not None:
                    font = QFont(self.font_family)
                else:
                    font = QFont()
                font.setPixelSize(font_size)
                metrics = QFontMetrics(font)
                padding_vertical = metrics.descent()

            # get top left and right bottom
            x_min  = np.min(item_indices[0])
            x_max = np.max(item_indices[0]) + 1
            y_min = max(np.min(item_indices[1]) - padding_vertical, 0)
            y_max = min(np.max(item_indices[1]) + 1 + padding_vertical, self.parent.num_row)
            # create rectangle
            dot_size = self.parent.dot_size
            rect = QRectF(QPointF(x_min*dot_size, y_min*dot_size), QPointF(x_max*dot_size, y_max*dot_size))
            self.selection_rectangle = CustomRectItem(rect, self)
            self.selection_rectangle.setFlags(QGraphicsItem.ItemIsMovable)
            pen_width = 0.5
            pen = QPen(Qt.black, pen_width)
            self.selection_rectangle.setPen(pen)
            self.selection_rectangle.setZValue(999)
            self.scene().addItem(self.selection_rectangle)
            self.selection_rectangle.setRect(x_min * dot_size +pen_width/2,
                                y_min * dot_size + pen_width/2,
                                (x_max - x_min) * dot_size - pen_width,
                                (y_max - y_min) * dot_size - pen_width)
            selection_rect = self.selection_rectangle.rect()
            selection_rect_scene = self.selection_rectangle.mapToScene(selection_rect).boundingRect()

            # get item at new position
            selected_items = self.scene().items(selection_rect_scene, Qt.IntersectsItemShape)
            self.filtered_items = [item for item in selected_items if item.zValue() == 1]

    def release_mouse_select_box(self):
        """Release selection rectangle
        """
        if hasattr(self, "selection_rectangle"):
            self.scene().removeItem(self.selection_rectangle)
            self.is_selected = False

    def mouseReleaseEvent(self, event):
        print(f"Current tool:{self.parent.current_tool}")
        print("last known rubber:", self.last_known_rubberband_rect)
        if self.parent.current_tool in ["text"] and self.last_known_rubberband_rect not in [0, None] \
                and self.last_known_rubberband_rect.isValid():
            self.parent.layer_widget.add_text_layer()
        print(f"Current tool:{self.parent.current_tool}")

        checked_boxes = [cb for cb in self.parent.layer_widget.checkbox_to_row.keys() if cb.isChecked()]
        if len(checked_boxes) == 0:
            return
        
        selected_checkbox = checked_boxes[0]
        row_layout = self.parent.layer_widget.checkbox_to_row[selected_checkbox]
        eye_icon = row_layout.itemAt(1).widget()
        # cho phép text có thể tạo không cần eye được check
        if eye_icon.isChecked() or self.parent.current_tool == "text": 
            if self.parent.current_tool in ["text","select", "mouse","zoom"]:
                print("Mouse released in ZoomableGraphicsView")

                self.transparent_brush = QBrush(self.transparent_color)
                gray_value = 255 - self.parent.topbar_widget.gray_slider.value()
                self.pen_color = QColor(gray_value, gray_value, gray_value)
                list_selected_layer = self.parent.layer_widget.get_list_selected_layer_name()
                len_list_selected_layer = len(list_selected_layer)
                # Handle cases with different number of selected layers
                if len_list_selected_layer == 0:
                    layer_name = "Layer 0"
                elif len_list_selected_layer == 1:
                    layer_name = list_selected_layer[0]

                if self.last_known_rubberband_rect and self.last_known_rubberband_rect.isValid() :
                    selection_rect_scene = self.mapToScene(self.last_known_rubberband_rect).boundingRect()

                    selected_items = self.scene().items(selection_rect_scene, Qt.IntersectsItemShape)

                    target_z_index = self.parent.layer_widget.get_selected_layer_z_index()
                    # because item view have z_index = 1
                    self.filtered_items = [item for item in selected_items if item.zValue() == 1]

                    if self.parent.current_tool == "text" and self.dragMode() == QGraphicsView.RubberBandDrag:
                        # Calculate the area to draw text
                        self.text_layer_items = [item for item in selected_items if item.zValue() == 1]
                        
                        self.parent.layer_widget.layers[layer_name]["items_text"] = self.text_layer_items
                        layer_items_text = self.parent.layer_widget.layers[layer_name]["items_text"]
                        w, h = self.calculate_bounding_area_in_pixels(layer_items_text)
                        bounding_items_text = layer_items_text[-1].sceneBoundingRect()
                        x_first = bounding_items_text.left() + (self.parent.pen_size/2) # pen size divided
                        y_first = bounding_items_text.top() + (self.parent.pen_size/2)
                        topleft_pos = (x_first, y_first)
                        # Prompt the user to enter text
                        input_text_dialog = InputTextDialog(self, "", font_size=DEFAULT_FONT_SIZE,topleft_pos=topleft_pos)
                        if input_text_dialog.exec():
                            text, font_size = input_text_dialog.getInputs()
                            # calculate size text
                            text_width, text_height = get_width_height_from_text(text, font_size, self.font_family)
                            dot_size = self.parent.dot_size
                            width_area = w//dot_size
                            height_area = h//dot_size
                            max_width = text_width if text_width > width_area else width_area
                            max_height = text_height if text_height > height_area else height_area
                            
                            # update items text
                            new_rect = QRect(bounding_items_text.left(), bounding_items_text.top(), max_width*dot_size, max_height*dot_size)
                            selected_items = self.scene().items(new_rect, Qt.IntersectsItemShape)
                            self.text_layer_items = [item for item in selected_items if item.zValue() == 1]
                            self.parent.layer_widget.layers[layer_name]["items_text"] = self.text_layer_items
                            self.parent.layer_widget.layers[layer_name]["first_pos"] = [x_first//dot_size, y_first//dot_size]
                            text_image = self.text_to_image(text, max_width, max_height, font_size)
                            self.apply_image_to_items_text(text, text_image, self.parent.layer_widget.layers[layer_name]["items_text"], font_size, target_z_index)
                            self.setDragMode(QGraphicsView.NoDrag)
                            self.parent.functions_widget.deselect_all_tools()
                        else:
                            self.parent.layer_widget.delete_layer(show_msg=False)
                            self.parent.functions_widget.refresh_tools()
                            return
                    if self.parent.current_tool == "select" and self.dragMode() == QGraphicsView.RubberBandDrag:
                        self.selection_rectangle = CustomRectItem(selection_rect_scene, graphics_view=self)
                        self.selection_rectangle.setFlags(QGraphicsItem.ItemIsMovable)
                        pen = QPen(Qt.black, 0.1)
                        self.selection_rectangle.setPen(pen)
                        self.selection_rectangle.setZValue(101)
                        self.scene().addItem(self.selection_rectangle)

                        w, h = self.calculate_bounding_area_in_pixels(self.filtered_items)
                        self.moved_image = self.redraw_image_from_items(self.filtered_items,w,h)
                        self.setDragMode(QGraphicsView.NoDrag)
                elif self.parent.current_tool == "mouse" and self.dragMode() == QGraphicsView.RubberBandDrag:

                    w, h = self.calculate_bounding_area_in_pixels(self.filtered_items)
                    self.moved_image = self.redraw_image_from_items(self.filtered_items,w,h)
                    self.is_selected = False
                    self.setDragMode(QGraphicsView.NoDrag)
            elif self.parent.current_tool == "draw":
                self.parent.drawing = False
            # Release all event
            super().mouseReleaseEvent(event)
            self.last_known_rubberband_rect = None
        else:
            QMessageBox.critical(self, self.parent.data["message"]["Warning"].get(self.parent.language_code),  self.parent.data["message"]["Off_view"].get(self.parent.language_code))
            return

    def handle_custom_rect_item_released(self):
        """
        Handle key press events within the ZoomableGraphicsView.
        """
        dot_size = self.parent.dot_size
        selection_rect = self.selection_rectangle.rect()
        selection_rect_scene = self.selection_rectangle.mapToScene(selection_rect).boundingRect()
        target_z_index = self.parent.layer_widget.get_selected_layer_z_index()
        layer_name = self.parent.layer_widget.get_list_selected_layer_name()[0]
        # get all items in selection_rect_scene
        selected_items = self.scene().items(selection_rect_scene, Qt.IntersectsItemShape)
        # get item at new position
        filtered_items = [item for item in selected_items if item.zValue() == 1]
        first_item = filtered_items[-1].rect()
        x_first, y_first =  first_item.x(), first_item.y() # pixel
        self.parent.layer_widget.layers[layer_name]["items_text"] = filtered_items
        self.apply_image_to_items(self.moved_image, filtered_items, self.filtered_items, target_z_index)
        self.parent.layer_widget.layers[layer_name]["first_pos"] = [x_first//dot_size, y_first//dot_size]
        self.moved_image = None
        self.scene().removeItem(self.selection_rectangle)
        self.parent.functions_widget.deselect_all_tools()

        # Continuously select
        if self.parent.current_tool == "mouse":
            label = self.parent.functions_widget.icon_labels[0] #index of mouse tool in toolbar
            self.parent.functions_widget.iconClicked(label)
  
    def mouseDoubleClickEvent(self, event):
        """
        Handle the double-click event within the ZoomableGraphicsView.
        """
        list_selected_layer = self.parent.layer_widget.get_list_selected_layer_name()
        len_list_selected_layer = len(list_selected_layer)
        target_z_index = self.parent.layer_widget.get_selected_layer_z_index()
        # Handle left mouse button double-click.
        print("Left button double-clicked.")

        # Handle cases with different number of selected layers
        if len_list_selected_layer == 0:
            layer_name = "Layer 0"
        elif len_list_selected_layer == 1:
            layer_name = list_selected_layer[0]

        if event.button() == Qt.LeftButton:
            if "Text" in layer_name :
                items_text = self.parent.layer_widget.layers[layer_name].get("items_text", [])
                print(len(items_text))
                if items_text == []:
                    return
                else :
                    # Get the old text from the selected layer
                    old_text = self.parent.layer_widget.layers[layer_name]["text"]
                    rotate_angle = self.parent.layer_widget.layers[layer_name].get("rotate_angle")
                    old_font_size = self.parent.layer_widget.layers[layer_name].get("font_size", MIN_FONT_SIZE)
                    old_color = self.parent.layer_widget.layers[layer_name].get("color", "#000000")
                    if old_text != "":
                        # Create and display custom dialog
                        dialog = MultiInputDialogue(self, default_text=old_text,
                                                    default_scale_v=1.0, default_scale_h=1.0,
                                                    default_rotation=0.0, font_size=old_font_size,
                                                    text_color=old_color) # or another default scale
                        if dialog.exec():
                            new_text, font_size, scale_value_v, scale_value_h, new_rotate_angle = dialog.getInputs()
                            text_color = dialog.selected_text_color
                            # Update text and scale text image here
                            
                            w, h = self.calculate_bounding_area_in_pixels(items_text)
                            self.parent.layer_widget.layers[layer_name]["rotate_angle"] = new_rotate_angle + rotate_angle

                            if new_text == old_text and font_size == old_font_size \
                                    and scale_value_h == 1 and scale_value_v == 1 \
                                    and new_rotate_angle == rotate_angle and text_color != old_color:

                                layer_data = self.parent.layer_widget.layers[layer_name]
                                layer_data["graphic_scene"][layer_data["graphic_scene"] ==old_color] = text_color
                                layer_data["color"] = text_color
                                # update view eyes
                                self.parent.layer_widget.handle_view_layer_visibility()
                                self.parent.set_layer_visibility()
                                return
                            font = QFont()
                            width = int(w // self.dot_size)
                            height = int(h // self.dot_size)
                            scaled_w = int(w // self.dot_size * scale_value_h)  # scale width
                            scaled_h = int(h // self.dot_size * scale_value_v)  # scale height

                            x_topleft, y_topleft = self.parent.convert_rect_to_grid(items_text[-1].rect(), self.dot_size)
                            if  x_topleft + scaled_w > self.parent.num_col or y_topleft + scaled_h > self.parent.num_row :
                                QMessageBox.critical(self, self.parent.data["message"]["Warning"].get(self.parent.language_code), self.parent.data["message"]["Image_resize_too_big"].get(self.parent.language_code))
                                return
                            else:
                                # dont move above to avoid error
                                # refresh content
                                self.parent.layer_widget.layers[layer_name]["graphic_scene"] = np.full((self.parent.num_col, self.parent.num_row), DEFAULT_VALUE_OF_ITEM)
                                # get image
                                if new_text != old_text or font_size != old_font_size or text_color != old_color:
                                    dot_size = self.parent.dot_size
                                    first_pos = self.parent.layer_widget.layers[layer_name].get("first_pos", [0,0])
                                    x_first, y_first = first_pos[0], first_pos[1]
                                    x_pixel, y_pixel = x_first*dot_size, y_first*dot_size
                                    # calculate size text
                                    text_width, text_height = get_width_height_from_text(new_text, font_size, self.font_family)
                                    if  x_first + text_width > self.parent.num_col \
                                            or y_first + text_height > self.parent.num_row:
                                        font_size = get_max_font_size(new_text, self.parent.num_col - x_first, 
                                                                      self.parent.num_row -y_first, self.font_family)
                                        text_width, text_height = get_width_height_from_text(new_text, font_size, self.font_family)

                                    max_width = text_width if text_width > width else width
                                    max_height = text_height if text_height > height else height
                                    scaled_w = int(max_width  * scale_value_h)  # scale width
                                    scaled_h = int(max_height  * scale_value_v)  # scale height
                                    image = self.text_to_image(new_text, max_width, max_height, font_size, text_color)
                                    # update items text
                                    new_rect = QRect(x_pixel, y_pixel, max_width*dot_size, max_height*dot_size)
                                    selected_items = self.scene().items(new_rect, Qt.IntersectsItemShape)
                                    self.text_layer_items = [item for item in selected_items if item.zValue() == 1]
                                    self.parent.layer_widget.layers[layer_name]["items_text"] = self.text_layer_items
                                else:
                                    image = self.redraw_image_from_items(items_text, w, h)
                                text_image = image.scaled(scaled_w, scaled_h)
                                rotate_image = self.rotate_image(text_image,new_rotate_angle)

                                self.apply_image_to_items_text(new_text, 
                                                               rotate_image, 
                                                               self.parent.layer_widget.layers[layer_name]["items_text"],
                                                               font_size, 
                                                               target_z_index, 
                                                               text_color)
                                graphic_scence = self.parent.layer_widget.layers[layer_name].get("graphic_scene", 
                                                                np.full((self.parent.num_col, self.parent.num_row), DEFAULT_VALUE_OF_ITEM))
                                item_indices = np.where(graphic_scence != DEFAULT_VALUE_OF_ITEM)
                                x_min  = np.min(item_indices[0])
                                x_max = np.max(item_indices[0]) + 1
                                y_min = np.min(item_indices[1])
                                y_max = np.max(item_indices[1]) + 1
                                # create rectangle
                                rect = QRectF(QPointF(x_min*2, y_min*2), QPointF(x_max*2, y_max*2))
                                selection_rectangle = CustomRectItem(rect, self)
                                selection_rect = selection_rectangle.rect()
                                selection_rect_scene = selection_rectangle.mapToScene(selection_rect).boundingRect()
                                selected_items = self.scene().items(selection_rect_scene, Qt.IntersectsItemShape)
                                filtered_items = [item for item in selected_items if item.zValue() == 1]
                                self.parent.layer_widget.layers[layer_name]["items_text"] = filtered_items

            else: #If there is a separate image layer, change else to if + Layer name (currently there is no , working on a normal layer)
                if self.parent.current_tool == "mouse":
                    graphic_scence = self.parent.layer_widget.layers[layer_name].get("graphic_scene", 
                                                                            np.full((self.parent.num_col, self.parent.num_row), DEFAULT_VALUE_OF_ITEM))
                    item_indices = np.where(graphic_scence != DEFAULT_VALUE_OF_ITEM)
                    if len(item_indices[0]) > 0 and len(item_indices[1]) > 0 :
                        dialog = MultiInputDialogue(self, default_text="Resize image", default_scale_v=1.0, default_scale_h=1.0,default_rotation=0.0, font_size=None)
                        dialog.textLineEdit.setEnabled(False)
                        dialog.rotationSpinBox.setEnabled(False)
                        if dialog.exec():
                            new_text, _, scale_value_v, scale_value_h, new_rotate_angle = dialog.getInputs()

                        # get top left and right bottom
                        x_min  = np.min(item_indices[0])
                        x_max = np.max(item_indices[0]) + 1
                        y_min = np.min(item_indices[1])
                        y_max = np.max(item_indices[1]) + 1
                        # create rectangle
                        rect = QRectF(QPointF(x_min*2, y_min*2), QPointF(x_max*2, y_max*2))
                        self.selection_rectangle = CustomRectItem(rect, self)
                        selection_rect = self.selection_rectangle.rect()
                        selection_rect_scene = self.selection_rectangle.mapToScene(selection_rect).boundingRect()

                        # get item at new position
                        selected_items = self.scene().items(selection_rect_scene, Qt.IntersectsItemShape)
                        filtered_items = [item for item in selected_items if item.zValue() == 1]
                        w, h = self.calculate_bounding_area_in_pixels(filtered_items)
                        scaled_w = int(w // self.dot_size * scale_value_h)  # scale width
                        scaled_h = int(h // self.dot_size * scale_value_v)  # scale height
                        x_topleft, y_topleft = self.parent.convert_rect_to_grid(filtered_items[0])
                        if  x_topleft + scaled_w > self.parent.num_col or y_topleft + scaled_h > self.parent.num_row :
                            QMessageBox.critical(self, self.parent.data["message"]["Warning"].get(self.parent.language_code), self.parent.data["message"]["Image_resize_too_big"].get(self.parent.language_code))
                            return
                        else: 
                            image = self.redraw_image_from_items(filtered_items,w,h)
                            scale_image = image.scaled(scaled_w, scaled_h)
                            self.apply_image_scale_to_items(scale_image, filtered_items, filtered_items, target_z_index)
            
            # Redraw bounding box
            if self.parent.current_tool == "mouse":
                self.release_mouse_select_box()
                self.mouse_select_box()    

    def calculate_bounding_area_in_pixels(self,filtered_items):
        if not filtered_items:
            return 0  # No items, no area

        # Initialize min and max coordinates with the first item's bounding rectangle
        first_item_rect = filtered_items[0].sceneBoundingRect()
        min_x = first_item_rect.left()
        max_x = first_item_rect.right()
        min_y = first_item_rect.top()
        max_y = first_item_rect.bottom()
        # Go through all items to find the bounding box
        for item in filtered_items:
            item_rect = item.sceneBoundingRect()
            # Update min and max coordinates based on the bounding rectangles
            min_x = min(min_x, item_rect.left())
            max_x = max(max_x, item_rect.right())
            min_y = min(min_y, item_rect.top())
            max_y = max(max_y, item_rect.bottom())

        # Calculate the width and height of the bounding box
        width = max_x - min_x
        height = max_y - min_y
        return width, height

    def text_to_image(self,text, max_width, max_height, font_size=MIN_FONT_SIZE, text_color=None):
        """
        Creates an image with the given dimensions and draws the text onto it using the largest font size that fits.

        :param text: The text to draw.
        :param max_width: The maximum width of the image.
        :param max_height: The maximum height of the image.
        :return: A QImage containing the text.
        """
        # Create an image with the specified dimensions and a transparent background
        image = QImage(max_width, max_height, QImage.Format_ARGB32)
        image.fill(Qt.transparent)  

        # assign to the property to avoid multiple registrations
        if self.font_family is not None:
            font = QFont(self.font_family)
        else:
            font = QFont() # Fallback to defautl font if neccesary
        font.setPixelSize(font_size)
        # Comment: For reference
        # # Create a QFontMetrics object to measure the text
        # metrics = QFontMetrics(font)

        # # Calculate the text's width and height using the current font size
        # text_width = metrics.horizontalAdvance(text)  # this method is used in newer versions of Qt
        # text_height = metrics.height()

        # # Increase the font size until the text is as big as possible but still fits within the specified dimensions
        # while text_width < max_width and text_height < max_height and font_size < max_height:
        #     font_size += 1
        #     font.setPixelSize(font_size)
        #     metrics = QFontMetrics(font)
        #     text_width = metrics.horizontalAdvance(text)
        #     text_height = metrics.height()


        # # Decrease font size by one to ensure it fits the dimensions
        # font.setPixelSize(font_size - 1)

        # Create a QPainter to draw on the image
        painter = QPainter(image)
        painter.setFont(font)
        if text_color is None:
            pen = self.parent.selected_color
        else:
            pen = QColor(text_color)
        # Set the color for the text and the alignment
        painter.setPen(pen)  # Black color for the text
        text_flags = Qt.AlignTop | Qt.AlignLeft  # Center alignment for the text

        # Draw the text onto the image
        painter.drawText(image.rect(), text_flags, text)
        painter.end()
        return image

    def apply_image_to_items_text(self,text, image, items, font_size, target_z_index = 0, text_color=None):
        """
        Apply the provided image onto the items by setting the color of each item based on the corresponding image pixel.
        
        :param image: The QImage to use as a reference.
        :param items: The list of items to apply the image to.
        """
        if text_color is None:
            text_color = self.parent.selected_color
        white_color = QColor(255, 255, 255)  # Define the white color
        items = items[::-1]

        x_pos, y_pos = self.parent.convert_rect_to_grid(items[0].rect(), cell_size=self.dot_size)
        list_selected_layer = self.parent.layer_widget.get_list_selected_layer_name()
        self.parent.layer_widget.layers[list_selected_layer[0]]["text"] = text
        self.parent.layer_widget.layers[list_selected_layer[0]]["font_size"] = font_size
        self.parent.layer_widget.layers[list_selected_layer[0]]["color"] = text_color

        # calculate threshold to filter color
        list_colors = []
        for y in range(image.height()):
            for x in range(image.width()):
                pixel_color = QColor(image.pixel(x, y))
                if image.pixel(x,y) == 0:
                    # pixel transparent
                    continue
                list_colors.append(pixel_color.getRgb()[:3])

        mean_color = np.mean(list_colors, axis=0)
        std_color = np.std(list_colors, axis=0)
        threshold = mean_color

        for y in range(image.height()):
            for x in range(image.width()):
                pixel_color = QColor(image.pixel(x, y))
                if image.pixel(x,y) == 0:
                    # pixel transparent
                    continue

                color = pixel_color.name()
                self.parent.layer_widget.set_color_at_pos(list_selected_layer[0],x+x_pos,y+y_pos, color)


                
        self.parent.layer_widget.handle_view_layer_visibility() # update view eyes
        self.parent.set_layer_visibility()

    def apply_image_to_items(self, image, items, old_item, target_z_index = 0):
        """
        Apply the provided image onto the items by setting the color of each item based on the corresponding image pixel.
        
        :param image: The QImage to use as a reference.
        :param items: The list of items to apply the image to.
        """
        items = items[::-1]
        layer_name = self.parent.layer_widget.get_list_selected_layer_name()[0]
        if len(items) > 0:
            # get first element in items
            x_topleft, y_topleft = self.parent.convert_rect_to_grid(items[0].rect())
            x_bottomright, y_bottomright = self.parent.convert_rect_to_grid(items[-1].rect())

            if  x_topleft + image.width() - 1 >= self.parent.num_col or y_topleft  + image.height() - 1 >= self.parent.num_row \
                or  x_bottomright + 1 - image.width() < 0 or y_bottomright + 1 - image.height() < 0:
                QMessageBox.critical(self, self.parent.data["message"]["Warning"].get(self.parent.language_code),self.parent.data["message"]["not_move_out_grid"].get(self.parent.language_code))
                return 
            for item in old_item:
                x_pos, y_pos = self.parent.convert_rect_to_grid(item.rect())
                # remove color at position
                self.parent.layer_widget.set_color_at_pos(layer_name, x_pos, y_pos, DEFAULT_VALUE_OF_ITEM)

            for y in range(image.height()):
                for x in range(image.width()):
                    x_pos = x + x_topleft
                    y_pos = y + y_topleft
                    if image.pixel(x,y) == 0:
                        # pixel transparent
                        continue
                    pixel_color = QColor(image.pixel(x, y))
                    
                    # write color into layer at position
                    self.parent.layer_widget.set_color_at_pos(layer_name, x_pos, y_pos, pixel_color.name())
            # refresh view
            self.parent.layer_widget.handle_view_layer_visibility() # update view eyes
            self.parent.set_layer_visibility()
        else:
            QMessageBox.critical(self, self.parent.data["message"]["Warning"].get(self.parent.language_code),self.parent.data["message"]["not_move_out_grid"].get(self.parent.language_code))
            return 
    
    def apply_image_scale_to_items(self, image, items, old_item, target_z_index = 0):
        """
        Apply the provided image onto the items by setting the color of each item based on the corresponding image pixel.
        
        :param image: The QImage to use as a reference.
        :param items: The list of items to apply the image to.
        """
        items = items[::-1]
        layer_name = self.parent.layer_widget.get_list_selected_layer_name()[0]
        if len(items) > 0:
            # get first element in items
            x_topleft, y_topleft = self.parent.convert_rect_to_grid(items[0].rect())
            x_bottomright, y_bottomright = self.parent.convert_rect_to_grid(items[-1].rect())
            for item in old_item:
                x_pos, y_pos = self.parent.convert_rect_to_grid(item.rect())
                # remove color at position
                self.parent.layer_widget.set_color_at_pos(layer_name, x_pos, y_pos, DEFAULT_VALUE_OF_ITEM)

            for y in range(image.height()):
                for x in range(image.width()):
                    x_pos = x + x_topleft
                    y_pos = y + y_topleft
                    if image.pixel(x,y) == 0:
                        # pixel transparent
                        continue
                    pixel_color = QColor(image.pixel(x, y))
                    
                    # write color into layer at position
                    self.parent.layer_widget.set_color_at_pos(layer_name, x_pos, y_pos, pixel_color.name())            
            # refresh view
            self.parent.layer_widget.handle_view_layer_visibility() # update view eyes
            self.parent.set_layer_visibility()
        else:
            QMessageBox.critical(QMessageBox.critical(self, self.parent.data["message"]["Warning"].get(self.parent.language_code),self.parent.data["message"]["not_move_out_grid"].get(self.parent.language_code))
)
            return            
    
    def redraw_image_from_items(self, items, width, height):
        """
        Create an image based on the filtered items.

        :param items: The list of items to include in the image.
        :param width: The width of the resulting image.
        :param height: The height of the resulting image.
        :return: A QImage representing the combined content of the items.
        """
        # Create an image with the specified dimensions
        image = QImage(width//self.dot_size, height//self.dot_size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)  # Start with a transparent image
        # painter = QPainter(image)
        x0,y0 = self.parent.convert_rect_to_grid(items[::-1][0].rect())
        for item in items[::-1]:
            if isinstance(item, QGraphicsRectItem):
                x, y = self.parent.convert_rect_to_grid(item.rect())
                
                # Check if the square is in the selected squares
                color = item.brush().color()
                # Update the pixel color
                image.setPixelColor(x-x0, y-y0, color)
        return image
    

    def rotate_image(self, image, angle):
        """
        Rotate an image by the given angle.

        :param image: The QImage to rotate.
        :param angle: The angle to rotate the image.
        :return: A new QImage with the image rotated.
        """
        print(f"Rotating image by angle: {angle}")
        # Create a QTransform for the rotation

        transform = QTransform().rotate(angle)

        # Use the transform to rotate the image
        rotated_image = image.transformed(transform, Qt.SmoothTransformation)

        # Find the size of the rotated image
        rotated_width = rotated_image.width()
        rotated_height = rotated_image.height()

        # Create a new QImage with a white background that can fit the rotated image
        new_width = max(image.width(), rotated_width)
        new_height = max(image.height(), rotated_height)
        final_image = QImage(new_width, new_height, QImage.Format_ARGB32)
        final_image.fill(Qt.transparent)

        # Create a QPainter to draw the rotated image onto the final image
        painter = QPainter(final_image)
        # Calculate the position to draw the rotated image so that it is centered
        x = (new_width - rotated_width) // 2
        y = (new_height - rotated_height) // 2
        painter.drawImage(x, y, rotated_image)
        painter.end()
        return final_image
