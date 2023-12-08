import time
from PySide6.QtGui import QColor, QBrush, QPen
from PySide6.QtCore import Signal, QObject, Qt
from PySide6.QtWidgets import QGraphicsRectItem


DOT_SIZE = 2

class InitLayer(QObject):
    finished = Signal()
    updateScene = Signal()

    def __init__(self,num_col,num_row):
        super().__init__()
        self._is_running = True
        self.NUM_ROW = num_row
        self.NUM_COL = num_col

    def generate(self, temp_graphs_scene=[]):
        print("In generating items")
        start = time.time()

        pen = QPen(Qt.white, 0.1)
        for i in range(2):
            if not self._is_running:
                break  # Dừng vòng lặp nếu cờ _is_running là False

            for row in range(self.NUM_ROW):
                for col in range(self.NUM_COL):
                    if not self._is_running:
                        break  # Dừng vòng lặp nếu cờ _is_running là False

                    x = col * DOT_SIZE
                    y = row * DOT_SIZE
                    rect_item = QGraphicsRectItem(x, y, DOT_SIZE, DOT_SIZE)
                    rect_item.setZValue(i + 1)
                    rect_item.setVisible(True)
                    rect_item.setPen(pen)
                    brush = QBrush(QColor(0, 0, 0, 0))
                    rect_item.setBrush(brush)

                    temp_graphs_scene.append(rect_item)

        print(f"Finished generation: {time.time() - start} s")
        if self._is_running:
            self.updateScene.emit()  # Phát signal updateScene nếu quá trình hoàn thành mà không bị dừng

        self.finished.emit()  # Phát signal finished khi hoàn thành

    def stop(self):
        self._is_running = False  # Đặt cờ _is_running là False để yêu cầu dừng