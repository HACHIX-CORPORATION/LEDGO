import numpy as np
import os
import math
from pathlib import Path
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QFont, QFontMetrics, QTextLayout, QTextDocument, QFontDatabase, QFontMetricsF
def get_width_height_from_text(text, font_size, font_family):
    """get Rectangle from text and font size

    Args:
        text (str): plain text
        font_size (int): font size
        font_family (str): font family

    Returns:
        width (int): Returns the width of text
        height (int): Returns the height of text
    """
    if font_family is not None:
        font = QFont(font_family)
    else:
        font = QFont()
    font.setPixelSize(font_size)

    font.setPixelSize(font_size)
    metrics = QFontMetrics(font)
    rect = metrics.boundingRect(QRect(0,0,0,0), Qt.AlignTop, text)
    height = rect.height()
    width = rect.width()
    return width, height

def get_max_font_size(text, max_width, max_height, font_family):
    """get max font size

    Args:
        text (str): text
        max_width (int): width
        max_height (int): height
        font_family (str): font family

    Returns:
        font_size (int): font size
    """
    font_size = 1
    while True:
        text_width, text_height = get_width_height_from_text(text, font_size + 1, font_family)
        if not (text_width <= max_width and text_height <= max_height and font_size + 1 <= max_height):
            break
        font_size += 1

    return font_size

def get_std_threshold(colors):
    color_values = np.array([color.getRgb()[:3] for color in colors])
    mean_color = np.mean(color_values, axis=0)
    std_color = np.std(color_values, axis=0)
    threshold = mean_color + 2 * std_color

    return threshold

def get_font_family():
    """Register font family

    Returns:
        font_family (str): font family
    """
    font_file = 'HiraginoKakuGothicProW3.otf'
    font_path = os.path.join(os.path.dirname(__file__), 'font', font_file)
    font_id = QFontDatabase.addApplicationFont(font_path)
    font_family = None
    if font_id != -1:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
    return font_family