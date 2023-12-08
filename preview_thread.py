from PySide6.QtGui import QColor, QImage
from PySide6.QtCore import Qt, Signal, QObject, Signal
import time

class PreviewManager(QObject):
    """This class is not used.
       Keep for reference. This class in sub thread generates preview image from matrix layer.
       And emit signal to update preview widget in main thread.
    Args:
        QObject (_type_): _description_
    """
    finished = Signal()
    updateImage = Signal()

    def draw(self, items, image):
        image.fill(Qt.white)
         # Sort items based on their zValue
        start = time.time()
        # Iterate through the colored squares and set the corresponding pixels
        if items is not None:
            print("Input array:", items.shape)
            for x in range(items.shape[0]):
                for y in range(items.shape[1]):
                    # Check if the square is in the selected squares
                    # Update the pixel color
                    if items[x][y] is not None:
                        image.setPixelColor(x, y, QColor(items[x][y]))
            # image = QImage(items, items.shape[0], items.shape[1], QImage.Format_RGB32)
            print(f"Finished draw: {time.time() - start} s")
        self.updateImage.emit()
        self.finished.emit()