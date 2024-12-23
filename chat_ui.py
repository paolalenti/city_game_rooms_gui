import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QLineEdit, QVBoxLayout, QWidget, \
    QComboBox


class ChatUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # Установка заголовка окна
        self.setWindowTitle('Chat UI')
        self.setGeometry(100, 100, 600, 400)

        # Основной виджет и его компоновка
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Добавление текстового поля для чата
        self.chat_text_edit = QTextEdit(self)
        self.chat_text_edit.setReadOnly(True)
        layout.addWidget(self.chat_text_edit)

        # Добавление текстового поля для ввода сообщения
        self.message_line_edit = QLineEdit(self)
        layout.addWidget(self.message_line_edit)

        # Добавление комбобокса для выбора комнаты
        self.rooms_combo_box = QComboBox(self)
        self.rooms_combo_box.addItems(['room1', 'room2', 'room3'])
        layout.addWidget(self.rooms_combo_box)

        # Кнопка отправки сообщения
        self.send_button = QPushButton('Отправить', self)
        layout.addWidget(self.send_button)

        # Кнопка "Бан"
        self.ban_button = QPushButton('Бан', self)
        layout.addWidget(self.ban_button)
        # self.ban_button.setDisabled(True)

        # Кнопка "Смена комнаты"
        self.change_room_button = QPushButton('Смена комнаты', self)
        layout.addWidget(self.change_room_button)

        # Кнопка "Выход"
        self.exit_button = QPushButton('Выход', self)
        layout.addWidget(self.exit_button)

        # Привязываем основную компоновку к центральному виджету
        central_widget.setLayout(layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ChatUI()
    window.show()
    app.exec()
