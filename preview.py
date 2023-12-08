from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QGraphicsView
from PySide6.QtGui import QPixmap, QPainter, QImage, QColor
import asyncio

class HoverLabel(QLabel):
    def __init__(self, sibling_widget=None):
        super(HoverLabel, self).__init__(sibling_widget.parentWidget() if sibling_widget else None)
        self.setMouseTracking(True)
        self.width=240
        self.height=192
        
        # Define the enlarged label
        self.enlarged_label = QLabel(self.parentWidget())
        self.enlarged_label.setWindowFlags(Qt.ToolTip)  # Makes it a floating window
        self.enlarged_label.hide()

    def enterEvent(self, event):
        # When mouse enters, show the enlarged label
        if self.pixmap():
            enlarged_pixmap = self.pixmap().scaled(self.width, self.height)
            self.enlarged_label.setPixmap(enlarged_pixmap)
            self.enlarged_label.adjustSize()
            self.enlarged_label.move(self.mapToGlobal(self.rect().topRight()))
            self.enlarged_label.show()

    def leaveEvent(self, event):
        # When mouse leaves, hide the enlarged label
        self.enlarged_label.hide()


class PreviewWidget(QVBoxLayout):
    def __init__(self, graphics_scene,num_col,num_row):
        super(PreviewWidget, self).__init__()
        self.graphics_scene = graphics_scene
        self.width = 60
        self.height = 48
        self.initUI()
        self.num_col = num_col
        self.num_row = num_row

    def initUI(self):
        self.preview_label = QLabel("Preview")
        self.image_label = HoverLabel(self.preview_label)  # Pass the sibling widget
        
        self.pixmap = QPixmap(self.width, self.height)
        painter = QPainter(self.pixmap)
        
        # Render the scene onto the pixmap
        self.graphics_scene.render(painter)
        painter.end()
        self.painter = painter
        
        # Set the pixmap to the label
        self.image_label.setPixmap(self.pixmap.scaled(self.width, self.height))
        
        self.addWidget(self.preview_label) 
        self.addWidget(self.image_label)

    # Temporarily using async for prevent blocking
    # TODO: display the preview in real time
    def update_preview(self, items):
        print("Scene changed. Update preview")
        # painter = QPainter(self.pixmap)
        # self.graphic_scene.render(painter)
        # painter.end()
        # self.image_label.setPixmap(self.pixmap.scaled(self.width, self.height))
        image = QImage(self.num_col, self.num_row, QImage.Format_RGB32)
        image.fill(Qt.white)
        if items is not None:
            for x in range(items.shape[0]):
                for y in range(items.shape[1]):
                    # Check if the square is in the selected squares
                    # Update the pixel color
                    if items[x][y] is not None:
                        image.setPixelColor(x, y, QColor(items[x][y]))
        pixmap = QPixmap.fromImage(image)
        self.image_label.setPixmap(pixmap.scaled(self.width, self.height))

    # # This method use Threading to prevent blocking
    def update_preview_by_image(self, image):
        print("Scene changed. Update preview")
        pixmap = QPixmap.fromImage(image)
        self.image_label.setPixmap(pixmap.scaled(self.width, self.height))
