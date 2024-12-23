import pickle
import sys
import socket
import threading
from time import sleep

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import pyqtSignal, QObject
from chat_ui import ChatUI


class ChatClient(QObject):
    message_received = pyqtSignal(str)
    room_changed = pyqtSignal(str)
    banned = pyqtSignal()

    def __init__(self, host, port):
        super().__init__()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))

        threading.Thread(target=self.receive_messages, daemon=True).start()

    def receive_messages(self):
        while True:
            try:
                message = pickle.loads(self.client_socket.recv(1024))
                if message.startswith("Switched to "):
                    self.room_changed.emit(message)
                elif message.startswith("banned"):
                    self.banned.emit()
                else:
                    self.message_received.emit(message)
            except OSError as e:
                print(f"Socket error: {e}")
                break

    def send_message(self, message):
        if self.client_socket:
            self.client_socket.send(pickle.dumps(message))

    def exit_chat(self):
        try:
            if self.client_socket:
                self.send_message("/exit")
                sleep(0.5)
                self.client_socket.close()
        except Exception as e:
            print(f"Error closing socket: {e}")


class ChatWindow(ChatUI):
    def __init__(self, client):
        super().__init__()
        self.client = client

        self.client.room_changed.connect(self.room_changed)
        self.client.banned.connect(self.exit_chat)

        self.client.message_received.connect(self.add_message)
        self.send_button.clicked.connect(self.send_message)
        self.ban_button.clicked.connect(self.ban_user)
        self.exit_button.clicked.connect(self.exit_chat)

        self.change_room_button.clicked.connect(self.change_room)

    def room_changed(self, message):
        self.chat_text_edit.clear()
        self.chat_text_edit.append(message)

    def add_message(self, message):
        self.chat_text_edit.append(message)

    def send_message(self):
        message = self.message_line_edit.text()
        self.client.send_message(message)
        self.message_line_edit.clear()

    def change_room(self):
        room_name = self.rooms_combo_box.currentText()
        self.client.send_message(f"/switch {room_name}")

    def ban_user(self):
        self.client.send_message('/ban')
        self.chat_text_edit.append("Пользователь забанен!")

    def exit_chat(self):
        self.client.exit_chat()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = ChatClient('localhost', 12345)
    window = ChatWindow(client)
    window.show()
    app.exec()
