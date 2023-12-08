from PySide6.QtGui import QColor, QBrush
from PySide6.QtCore import Signal, QObject, Signal

class ViewLayer(QObject):
    finished = Signal()
    def update_view(self, list_item_layer_view_eyes, 
                    original_matrix_layer, 
                    transparent_red, 
                    convert_rect_to_grid, 
                    pen,
                    find_diff_func):
        try:
            print("View changed. Update view.")
            changed_item_idx = find_diff_func()
            for idx in changed_item_idx:
                item = list_item_layer_view_eyes[idx]
                if original_matrix_layer is None:
                    # when no layer is selected
                    item.setBrush(transparent_red) 
                    continue
                
                x_pos, y_pos = convert_rect_to_grid(item.rect())
                cell_color = original_matrix_layer[x_pos][y_pos]

                if cell_color != None:
                    # set color for item
                    custom_color = QColor(cell_color)
                    color = QBrush(custom_color)
                else:
                    color = transparent_red
                item.setBrush(color)
                item.setPen(pen)
        except Exception as e:
            print(f"Error when changing view. {e}")
        self.finished.emit()

class WorkerThread(QObject):
    finished = Signal()
    def run_thread(self, callback):
        callback()
        self.finished.emit()