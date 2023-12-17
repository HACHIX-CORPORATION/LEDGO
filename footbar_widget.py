import sys
import json
import os
import numpy as np  # Import NumPy
import glob
import zipfile
from io import BytesIO
import time
import imageio
import cv2
import tempfile
from PIL import Image

from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGraphicsView, \
    QGraphicsScene, \
    QGraphicsRectItem, QWidget, QProgressDialog, QSizePolicy, QColorDialog, QComboBox, QFileDialog, QMessageBox, \
    QSlider, QCheckBox, QSpacerItem, QSpinBox, QGraphicsProxyWidget
from PySide6.QtGui import QPen, QBrush, QColor, QImage, QPainter, QFont, QIcon, QPixmap, QMovie
from PySide6.QtCore import Qt, QEvent, QSize, Signal, QRectF, QByteArray, QBuffer, QIODevice, QPointF, QThread, QObject, \
    Signal, QMutex

DEFAULT_VALUE_OF_ITEM = None
TEMP_DIR = tempfile.TemporaryDirectory()


class FootBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.save_project_button = QPushButton("Save Project")
        self.save_project_button.setObjectName("SaveProjectButton")
        self.load_project_button = QPushButton("Load Project")
        self.load_project_button.setObjectName("LoadProjectButton")
        self.generate_bmp_button = QPushButton("Generate BMP")
        self.generate_bmp_button.setObjectName("GenerateBMPButton")
        self.generate_data_array_button = QPushButton("Generate Array Data")
        self.generate_data_array_button.setObjectName("GenerateDataArrayButton")

        self.save_project_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.load_project_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.generate_bmp_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.generate_data_array_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        button_width = self.save_project_button.sizeHint().width()
        self.save_project_button.setFixedWidth(button_width + button_width // 3)
        self.load_project_button.setFixedWidth(
            button_width + button_width // 3)  # Set the fixed width for the Import BMP button
        self.generate_bmp_button.setFixedWidth(button_width + button_width // 3)
        self.generate_data_array_button.setFixedWidth(button_width + button_width // 3)

        font = QFont()
        self.save_project_button.setFont(font)
        self.load_project_button.setFont(font)
        self.generate_bmp_button.setFont(font)
        self.generate_data_array_button.setFont(font)

        self.layout = QHBoxLayout()
        self.layout.addStretch(1)

        self.layout.addWidget(self.save_project_button)
        self.layout.addWidget(self.load_project_button)
        self.layout.addWidget(self.generate_bmp_button)
        self.layout.addWidget(self.generate_data_array_button)

        self.button_w_ratio = 10
        self.button_h_ratio = 20
        # self.num_col = self.parent.num_col
        # self.num_row = self.parent.num_row
        self.dot_size = 2
        self.save_project_button.clicked.connect(lambda: self.save_project())
        # self.clear_button.clicked.connect(self.clear_colors)
        self.load_project_button.clicked.connect(lambda: self.load_project())
        self.generate_bmp_button.clicked.connect(lambda: self.generate_bmp())
        self.generate_data_array_button.clicked.connect(lambda: self.generate_bmp(True))

        self.setLayout(self.layout)

    def get_widget(self):
        # Method to get the actual top bar widget
        return self

    def update_button_sizes(self, app_width, app_height):

        """
        Updates the sizes and font point sizes of specific buttons in the application based on the current 
        window dimensions.

        Parameters:
        - app_width (int): The current width of the application window.
        - app_height (int): The current height of the application window.

        """

        # Calculate button width and height based on the window dimensions
        button_width = app_width // self.button_w_ratio  # Adjust the ratio as needed
        button_height = app_height // self.button_h_ratio  # Adjust the ratio as needed

        for button in [self.save_project_button, self.load_project_button, self.generate_bmp_button,
                       self.generate_data_array_button]:
            button.setFixedSize(button_width + 50, button_height)
            font = button.font()
            font.setPointSize(int(button.height() * 0.25))
            button.setFont(font)

    def getZoomedViewRect(self):
        # Get viewport size
        viewport_size = self.parent().graphics_view.viewport().size()
        print(viewport_size)

        # Calculate the current center coordinates of the view in the scene
        center_point = self.parent().graphics_view.mapToScene(self.parent().graphics_view.viewport().rect().center())

        # Calculate the size of QRectF based on the zoom ratio
        width = viewport_size.width() / self.parent().graphics_view.zoom_factor
        height = viewport_size.height() / self.parent().graphics_view.zoom_factor

        # Create QRectF with center coordinates and calculated dimensions
        view_rect = QRectF(center_point.x() - width / 2, center_point.y() - height / 2, width, height)

        return view_rect

    def prepare_project_data(self):
        layers_data = {}
        selected_layers = [row_layout.itemAt(3).widget().text().split(" :")[0]
                           for checkbox, row_layout in self.parent().layer_widget.checkbox_to_row.items()
                           if checkbox.isChecked()]
        view_rect = str(self.getZoomedViewRect())
        print("----------------", view_rect)
        for layer_name, layer_value in list(self.parent().layer_widget.layers.items()):
            items = []
            items_text = []
            # selected_squares = self.selected_squares.get(z_value, set())
            z_index = layer_value.get("z_index", 0)
            # print(self.layer_widget.layers.get())
            for item in self.parent().graphics_scene.items():
                if item.zValue() == z_index and isinstance(item, QGraphicsRectItem):
                    if hasattr(item, "brush"):
                        color = item.brush().color()
                        color_name = "transparent" if color.alpha() == 0 else color.name()

                        item_data = {
                            "x": item.rect().x(),
                            "y": item.rect().y(),
                            "color": color_name,
                            # "selected": (item.rect().x(), item.rect().y()) in selected_squares
                        }
                        items.append(item_data)
            for item in layer_value.get("items_text", []):
                color = item.brush().color()
                color_name = "transparent" if color.alpha() == 0 else color.name()

                item_data = {
                    "x": item.rect().x(),
                    "y": item.rect().y(),
                    "w": item.rect().width(),
                    "h": item.rect().height(),
                    "color": color_name,
                    # "selected": (item.rect().x(), item.rect().y()) in selected_squares
                }
                items_text.append(item_data)

            graphic_scene = layer_value.get("graphic_scene",
                                            np.full((self.parent().num_col, self.parent().num_row),
                                                    DEFAULT_VALUE_OF_ITEM))
            color = layer_value.get("color", "")
            save_gif_path = ""
            if layer_value.get("type_img", "") == "gif":
                temp_file = f"{time.perf_counter()}.gif"
                self.prepare_original_gif(layer_value.get("gif"), temp_file)
                save_gif_path = temp_file

            layers_data[layer_name] = {
                "z_value": layer_value.get("z_index", 0),
                "text": layer_value.get("text", ""),
                "font_size": layer_value.get("font_size", 0),
                "graphic_scene": graphic_scene.tolist() if isinstance(graphic_scene, np.ndarray) else graphic_scene,
                "layer_type": layer_value.get("layer_type", "image"),
                "is_checked": layer_name in selected_layers,
                "color": color.name() if isinstance(color, QColor) else color,
                "items": items,
                "items_text": items_text,
                "first_pos": layer_value.get("first_pos", [0, 0]),
                "rotate_angle": layer_value.get("rotate_angle", 0),
                "gif_path": save_gif_path
            }

        project_data = {
            "layers": layers_data,
            "grid_border": self.parent().topbar_widget.grid_border_checkbox.isChecked(),
            "grid_color": self.parent().topbar_widget.gray_slider.value(),
            "selected_color": self.parent().selected_color.name(),
            "grid_col": self.parent().num_col,
            "grid_row": self.parent().num_row,
            "zoom_factor": self.parent().graphics_view.zoom_factor,
            "view_rect": view_rect
        }
        return project_data

    def prepare_original_gif(self, gif, file_path):
        """
        Processes each frame of the input gif to adjust its size according to the specified dot size and 
        creates a new gif with these processed frames.

        Parameters:
        - gif (QMovie): The gif to be processed, which is an instance of QMovie that allows frame by frame access.
        - file_path (str): The path where the new gif should be saved.

        Returns:
        None: The function does not return a value but instead writes the processed gif to the specified file path.
        """
        frames = []
        # loop frame of gif
        for i in range(gif.frameCount()):
            # jump to frame i
            gif.jumpToFrame(i)
            # get QImage from gif
            frame_gif = gif.currentImage()
            # Create a QImage with the size and fill it with white color
            image = QImage(frame_gif.width() / self.dot_size, frame_gif.height() / self.dot_size, QImage.Format_RGB32)
            image.fill(Qt.white)

            # return original size
            frame_gif = frame_gif.scaled(frame_gif.size() / self.dot_size)
            painter = QPainter(image)
            painter.drawImage(0, 0, frame_gif)
            painter.end()
            frames.append(image)
        # write gif
        self.write_gif(frames, gif.nextFrameDelay() / 1000, file_path)

    def save_project(self, project_path=None):
        """
        Save the current project to a file. This function will prompt the user to choose a save
        location and then save the project data and associated images.
        """
        if project_path is None:
            options = QFileDialog.Options()
            project_path = \
            QFileDialog.getSaveFileName(self, "Save Project", "", "Project Files (*.proj);;All Files (*)",
                                        options=options)[0]

        if not project_path:
            return

        # Ensure the path ends with ".proj"
        if not project_path.endswith('.proj'):
            project_path += '.proj'

        # Prepare the data to be saved
        project_data = self.prepare_project_data()

        with zipfile.ZipFile(project_path, 'w') as project_zip:
            # Save project data as JSON
            project_data_str = json.dumps(project_data)
            project_zip.writestr('data.json', project_data_str)
            # Save each layer as an image
            for layer_name in self.parent().layer_widget.layers.keys():
                if layer_name != "Layer 0":
                    # get gif_path save in zip
                    gif_path = project_data.get("layers")[layer_name].get("gif_path")
                    if gif_path != "":
                        project_zip.write(gif_path)
                        os.remove(gif_path)
                    image = QImage(self.parent().num_col, self.parent().num_row, QImage.Format_RGB32)
                    image.fill(Qt.white)
                    items = self.parent().layer_widget.layers[layer_name].get("graphic_scene")
                    for x in range(items.shape[0]):
                        for y in range(items.shape[1]):
                            # Check if the square is in the selected squares
                            # Update the pixel color
                            if items[x][y] is not None:
                                image.setPixelColor(x, y, QColor(items[x][y]))

                    # Save the image in memory
                    byte_array = QByteArray()
                    buffer = QBuffer(byte_array)
                    buffer.open(QIODevice.WriteOnly)
                    image.save(buffer, "PNG")

                    # Write from memory to ZIP file
                    image_file_in_memory = BytesIO(byte_array.data())
                    project_zip.writestr(f'assets/{layer_name}.png', image_file_in_memory.getvalue())

        print("Done save project")
        # QMessageBox.information(self, self.parent().data["message"]["Project_Saved"].get(self.parent().language_code), self.parent().data["message"]["Project_Saved"].get(self.parent().language_code))

    def load_project(self, temp_path=None):
        print("temp :", temp_path)
        if temp_path == None:
            options = QFileDialog.Options()
            project_path = \
            QFileDialog.getOpenFileName(self, "Open Project File", "", "Project Files (*.proj);;All Files (*)",
                                        options=options)[0]

            if not project_path:
                return
        else:
            project_path = temp_path
        # Clear the current project state
        self.parent().layer_widget.clear_layers()
        # self.parent().selected_squares = {}
        # Extract and load project data from the ZIP file
        with zipfile.ZipFile(project_path, 'r') as project_zip:
            with project_zip.open('data.json') as file:
                project_data = json.loads(file.read().decode("utf-8"))
            num_col = project_data.get("grid_col", 480)
            num_row = project_data.get("grid_row", 384)
            zoom_factor = project_data.get("zoom_factor", 1.25)
            view_rect = project_data.get("view_rect", "")
            rect_expression = view_rect.replace("PySide6.QtCore.", "")
            view_rect = eval(rect_expression)
            print("view_rect:", view_rect)
            center_point = view_rect.center()
            old_col = self.parent().num_col
            old_row = self.parent().num_row

            if num_col != old_col or num_row != old_row:
                self.parent().reset_global()
                self.parent().num_col = int(num_col)
                self.parent().num_row = int(num_row)
                self.parent().reset_grid(int(num_col), int(num_row))
            self.parent().topbar_widget.updateSize(int(num_col), int(num_row))

            graphics_view = self.parent().graphics_view
            scene = self.parent().graphics_view.scene()

            for layer_name, layer_data in dict(
                    sorted(project_data["layers"].items(), key=lambda x: x[1]["z_value"])).items():
                z_value = layer_data.get("z_value", 0)
                items_text = []

                for item in layer_data.get("items_text", []):
                    x = item.get("x", 0)
                    y = item.get("y", 0)
                    w = item.get("w", 0)
                    h = item.get("h", 0)
                    found_items = scene.items(QRectF(x, y, w, h))
                    for found_item in found_items:
                        if isinstance(found_item, QGraphicsRectItem) and found_item.zValue() == 1:
                            items_text.append(found_item)
                border_color = Qt.white if layer_name == "Layer 0" else Qt.gray

                if layer_name != "Layer 0":
                    is_checked = layer_data.get("is_checked", False)
                    layer_type = layer_data.get("layer_type", "image")
                    color = layer_data.get("color", "")

                    graphic_scene = np.array(layer_data.get("graphic_scene",
                                                            np.full((self.parent().num_col, self.parent().num_row),
                                                                    DEFAULT_VALUE_OF_ITEM)))
                    self.parent().layer_widget.layers[layer_name] = {}
                    self.parent().layer_widget.layers[layer_name]["z_index"] = z_value
                    self.parent().layer_widget.layers[layer_name]["text"] = layer_data.get("text", "")
                    self.parent().layer_widget.layers[layer_name]["font_size"] = layer_data.get("font_size", 0)
                    self.parent().layer_widget.layers[layer_name]["graphic_scene"] = graphic_scene
                    self.parent().layer_widget.layers[layer_name]["layer_type"] = layer_type
                    self.parent().layer_widget.layers[layer_name]["color"] = QColor(color) if color != "" else color
                    self.parent().layer_widget.layers[layer_name]["items_text"] = items_text
                    self.parent().layer_widget.layers[layer_name]["rotate_angle"] = layer_data.get("rotate_angle", 0)
                    self.parent().layer_widget.layers[layer_name]["first_pos"] = layer_data.get("first_pos", [0, 0])

                    if layer_type == "image":
                        # case gif
                        gif_path = layer_data.get("gif_path", "")
                        # if this is gif layer extract to temp directory
                        if gif_path != "":
                            temp_file = os.path.join(TEMP_DIR.name, gif_path)
                            project_zip.extract(gif_path, TEMP_DIR.name)
                            self.parent().import_gif(temp_file, layer_name)
                            self.parent().layer_widget.layers[layer_name]["type_img"] = "gif"
                        self.parent().layer_widget.add_layer_row(layer_name, z_value, is_checked)
                        self.parent().layer_widget.layer_counter += 1
                    else:
                        self.parent().layer_widget.add_text_layer_row(layer_name, z_value, is_checked)
                        self.parent().layer_widget.text_layer_counter += 1
                        self.parent().layer_widget.layer_counter += 1
                        # self.parent().layer_widget.text_layer_z_index -= 1

                    # update thumbnail
                    self.parent().layer_widget.set_thumbnail_for_layer(layer_name)

            # App state:
            is_grid_border_checked = project_data.get("grid_border", False)
            grid_color_value = project_data.get("grid_color", 80)
            selected_color = project_data.get("selected_color", self.parent().colors[0])

            self.parent().topbar_widget.grid_border_checkbox.setChecked(is_grid_border_checked)
            self.parent().topbar_widget.gray_slider.setValue(grid_color_value)
            self.parent().selected_color = QColor(selected_color)
            # self.parent().topbar_widget.update_selected_color()
            for label_color in self.parent().topbar_widget.basic_color_labels:
                color_bg = label_color.palette().color(label_color.backgroundRole()).name()

                if selected_color == color_bg:
                    label_color.setStyleSheet(
                        f"background-color: {selected_color}; border: 4px solid green; border-radius: 5px;")  # Add rounded corners and border
                    label_color.setProperty("selected", True)
                else:
                    label_color.setStyleSheet(
                        f"background-color: {color_bg}; border: 1px solid black; border-radius: 5px;")  # Add rounded corners
                    label_color.setProperty("selected", False)
            # draw image
            self.parent().layer_widget.handle_view_layer_visibility()  # update view eyes
            print(f"Current view size items: {len(self.parent().list_item_layer_view)}")

            if num_col != old_col or num_row != old_row:
                self.parent().worker_init_item.finished.connect(self.parent().thread_finished)
            else:
                self.parent().set_layer_visibility()
                self.parent().layer_widget.update_function_icons_state()
            graphics_view.scale(zoom_factor, zoom_factor)
            graphics_view.centerOn(center_point)
            graphics_view.zoom_factor = zoom_factor
            self.parent().topbar_widget.curent_zoom_factor.setText(f"x{zoom_factor:.2f}")
        print(f"Project '{os.path.basename(project_path)}' loaded successfully")

        project_name = os.path.basename(project_path)  # Extract the project name from the directory path
        message = f"Load proj {project_name} done"
        # QMessageBox.information(self, self.parent().data["message"]["Project_loaded"].get(self.parent().language_code), message)

    def generate_bmp(self, isGenerateC=False):
        # Get the file path and name from the user using QFileDialog
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        if self.parent().language_code == "eng":
            file_dialog.setWindowTitle("Save BMP, GIF File")
        else:
            file_dialog.setWindowTitle("BMP、GIFファイルを保存")
        file_dialog.setNameFilter("BMP Files (*.bmp);; GIF File (*.gif)")

        if file_dialog.exec_() == QFileDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            if file_path.split(".")[-1].lower() == "gif":
                frames = []
                # get matrix image from seleted layer
                items = self.parent().get_matrix_layer()

                # Initialize the progress dialog for GIF frames
                progress_dialog = QProgressDialog(
                    self.parent().data["progress"]["Generating_GIF"].get(self.parent().language_code),
                    self.parent().data["progress"]["Cancel"].get(self.parent().language_code), 0,
                    self.parent().gif.frameCount(), self)
                progress_dialog.setWindowTitle(
                    self.parent().data["message"]["Processing"].get(self.parent().language_code))
                progress_dialog.setWindowModality(Qt.WindowModal)
                current_progress = 0
                # loop frame of gif
                for i in range(self.parent().gif.frameCount()):
                    # Create a QImage with the size 480x384 and fill it with white color
                    image = QImage(self.parent().num_col, self.parent().num_row, QImage.Format_RGB32)
                    image.fill(Qt.white)
                    # jump to frame i
                    self.parent().gif.jumpToFrame(i)
                    # get QImage from gif
                    frame_gif = self.parent().gif.currentImage()
                    # return original size
                    frame_gif = frame_gif.scaled(frame_gif.size() / self.dot_size)
                    # create painter to write frame into image
                    painter = QPainter(image)
                    painter.drawImage(0, 0, frame_gif)
                    # loop matrix image from selected layer an write pixel into image
                    if items is not None:
                        for x in range(items.shape[0]):
                            for y in range(items.shape[1]):
                                # Update the pixel color
                                if items[x][y] is not None:
                                    image.setPixelColor(x, y, QColor(items[x][y]))
                    painter.end()
                    frames.append(image)
                    current_progress += 1
                    progress_dialog.setValue(current_progress)
                    QApplication.processEvents()
                # write gif
                with imageio.get_writer(file_path, mode="I", duration=self.parent().gif.nextFrameDelay() / 1000) as f:
                    for frame in frames:
                        # create temp image
                        frame.save("temp.png")
                        # read numpy image
                        numpy_image = cv2.imread("temp.png")
                        numpy_image = cv2.cvtColor(numpy_image, cv2.COLOR_BGR2RGB)
                        # append into
                        f.append_data(numpy_image)
                progress_dialog.close()
                self.write_gif(frames, self.parent().gif.nextFrameDelay() / 1000, file_path, isGenerateC)
                QMessageBox.information(self, self.parent().data["message"]["Success"].get(self.parent().language_code),
                                        f"GIF file saved at {file_path}")
            else:
                image = QImage(self.parent().num_col, self.parent().num_row, QImage.Format_RGB32)
                image.fill(Qt.white)
                items = self.parent().get_matrix_layer()
                if items is not None:
                    progress_dialog = QProgressDialog(
                        self.parent().data["progress"]["Generating_BMP"].get(self.parent().language_code),
                        self.parent().data["progress"]["Cancel"].get(self.parent().language_code), 0,
                        items.shape[0] * items.shape[1], self)
                    progress_dialog.setWindowTitle(
                        self.parent().data["message"]["Processing"].get(self.parent().language_code))
                    progress_dialog.setWindowModality(Qt.WindowModal)
                    current_progress = 0
                    for x in range(items.shape[0]):
                        for y in range(items.shape[1]):
                            # Update the pixel color
                            if items[x][y] is not None:
                                image.setPixelColor(x, y, QColor(items[x][y]))
                            current_progress += 1
                            progress_dialog.setValue(current_progress)
                            QApplication.processEvents()
                    progress_dialog.close()

                # Save the image as a BMP file
                image.save(file_path, "BMP")
                if isGenerateC:
                    self.image_to_c_array_32bit(file_path)
                QMessageBox.information(self, self.parent().data["message"]["Success"].get(self.parent().language_code),
                                        f"BMP file saved at {file_path}")

    def write_gif(self, frames, duration, file_path, isGenerateC = False):
        """Write gif from fames, duration and file path

        Args:
            frames (List): List of frames
            duration (float): duration
            file_path (str): path to save
        """
        with imageio.get_writer(file_path, mode="I", duration=duration) as f:
            temp_file = f"{time.perf_counter()}.png"
            for frame in frames:
                # create temp image
                frame.save(temp_file)
                # read numpy image
                numpy_image = cv2.imread(temp_file)
                numpy_image = cv2.cvtColor(numpy_image, cv2.COLOR_BGR2RGB)
                # append into
                f.append_data(numpy_image)
            if len(frames) > 0:
                os.remove(temp_file)
        if isGenerateC:
            self.image_to_c_array_32bit(file_path)

    @staticmethod
    def image_to_c_array_32bit(image_path):
        try:
            print('test image_to_c_array_32bit')
            # Open the image file
            img = Image.open(image_path)


            # Get pixel data
            pixel_data = list(img.getdata())

            # Format pixel data into a C-style array with 32-bit hex values
            c_array = "const uint32_t image[] = {\n"
            for i in range(0, len(pixel_data), 4):
                pixels = pixel_data[i:i + 4]
                hex_value = 0
                for j, pixel in enumerate(pixels):
                    r, g, b = pixel[:3]  # Extract RGB values
                    hex_value |= (r << 16) | (g << 8) | b  # Combine RGB into a 32-bit value
                c_array += f"0x{hex_value:08X},\n"
            c_array += "};"
            path = image_path.split(".")[0] + ".c"
            with open(path, "w") as output_file:
                output_file.write(c_array)

        except FileNotFoundError:
            return "File not found"
        except Exception as e:
            return f"Error: {e}"
