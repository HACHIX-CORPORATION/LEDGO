from PySide6.QtCore import QUrl
from PySide6.QtWebSockets import QWebSocket


class WebSocketClient:
    def __init__(self, url):
        self.url = url
        self.socket = QWebSocket()
        self.socket.connected.connect(self.on_connected)
        self.socket.textMessageReceived.connect(self.on_message_received)
        self.socket.errorOccurred.connect(self.on_error)

    def on_connected(self):
        print("Connected to WebSocket server")
        # Example: Send a message when connected
        self.socket.sendTextMessage("Hello, WebSocket Server!")

    @staticmethod
    def on_message_received(message):
        print("Received message:", message)

    @staticmethod
    def on_error(self, error):
        print("WebSocket error:", error)

    def connect(self):
        self.socket.open(QUrl(self.url))

    def disconnect(self):
        self.socket.close()