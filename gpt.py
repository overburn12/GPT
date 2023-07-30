import openai
import json
import markdown

from PyQt5.QtWidgets import QApplication, QGridLayout, QListWidget, QPushButton, QWidget, QPlainTextEdit, QTextBrowser, QInputDialog
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal, QObject, QEvent
from openai.error import OpenAIError

class OpenAIAPIThread(QThread):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(OpenAIError)

    def __init__(self):
        super().__init__()
        #load the api key 
        with open('not-an-api-key.txt', 'r') as file:
            openai.api_key = file.read()

    def run(self, chat_history):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=chat_history  # Pass the entire conversation history
            )
            ai_message = {"role": "assistant", "content": response['choices'][0]['message']['content']}
            self.response_received.emit(ai_message)
        except OpenAIError as e:
            self.error_occurred.emit(e)

class ChatHistory(QObject):
    chat_updated = pyqtSignal()
    chat_histories_update = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.fileName = "chat_history.json"
        self.init_chat()
    
    def init_chat(self):
        self.html_head = ""
        self.html_chat = ""
        self.html_tail = ""
        self.chat_histories = {}
        self.current_chat = ""

    def load_chat_file(self):
        # Load all chat histories from the file
        try:
            with open(self.fileName, 'r') as f:
                self.chat_histories = json.load(f)
        except FileNotFoundError:
                #default chat
                self.chat_histories = {"chat1": [{"role": "system", "content": "You are a helpful assistant."}]}
                self.current_chat = "chat1"
        self.chat_histories_update.emit()
    
    def save_chat_file(self):
        with open(self.fileName, 'w') as f:
            json.dump(self.chat_histories, f)
    
    def send_api_message(self, user_msg):
        if user_msg.strip() != "":  # only send the message if it's not empty
            message = {"role": "user", "content": user_msg}

            self.thread = OpenAIAPIThread(message)
            self.thread.response_received.connect(self.handle_api_message)
            self.thread.error_occurred.connect(self.handle_api_error)
            self.thread.start()

    def switch_to_chat(self, selectedchat):
        self.current_chat = selectedchat
        self.html_chat = ""
        for message in self.chat_histories[selectedchat]:
            self.html_chat += self.convert_msg_to_html(message)
        self.chat_updated.emit()

    def add_message_to_chat(self, message):
        self.chat_histories[self.current_chat].append(message)
        self.html_chat += self.convert_msg_to_html(message)
        self.chat_updated.emit()
    
    def convert_msg_to_html(self, message):
        role = message['role'].lower()
        content = message['content']
        
        if role == "user":
            color = "blue"
        elif role == "assistant":
            color = "red"
        else:
            color = "black"

        return markdown.markdown(f"<b style='color:{color};'>{role}:</b> {content}", extras=["fenced-code-blocks"])

    #def add_new_chat(self):
    #def rename_chat(self):
    #def delete_chat(self):
    #def select_chat(self):

    @pyqtSlot()
    def handle_api_message(self, ai_message):
        self.add_message_to_chat(ai_message)
        self.chat_histories[self.current_chat].append(ai_message)

    @pyqtSlot()
    def handle_api_error(self, error):
        self.chat_history.insert('Error: ' + str(error))
    
class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.init_ui()
        self.chat_obj = ChatHistory()
        
        self.chat_obj.chat_updated.connect(self.update_chat_display)
        self.chat_obj.chat_histories_update.connect(self.populate_chat_histories_listbox)

        self.chat_obj.load_chat_file()

    def init_ui(self):
        layout = QGridLayout()
        self.button_add_chat = QPushButton("Add Chat")
        self.button_rename_chat = QPushButton("Rename Chat")
        self.button_delete_chat = QPushButton("Delete Chat")
        self.button_send_chat = QPushButton("Send")
        self.text_user_input = QPlainTextEdit()
        self.list_chat_histories = QListWidget()
        self.browser_chat_html = QTextBrowser()

        #send the chatname to select_chat_history() when the chatlist is clicked
        self.list_chat_histories.itemClicked.connect(lambda item: self.select_chat_history(item.text()))

        #construct the layout of the GUI
        chat_list_left = 14
        button_width = 2
        layout.addWidget(self.browser_chat_html, 0, 0, 9, chat_list_left)  
        layout.addWidget(self.list_chat_histories, 0, chat_list_left, 6, button_width)  
        layout.addWidget(self.text_user_input, 9, 0, 3, chat_list_left)
        layout.addWidget(self.button_send_chat, 9, chat_list_left, 3, button_width) 
        layout.addWidget(self.button_add_chat, 6, chat_list_left, 1, button_width)
        layout.addWidget(self.button_rename_chat, 7, chat_list_left, 1, button_width) 
        layout.addWidget(self.button_delete_chat, 8, chat_list_left, 1, button_width)
        self.setLayout(layout)

    def closeEvent(self, event: QEvent):
        self.chat_obj.save_chat_file()
        super().closeEvent(event)

    @pyqtSlot()
    def select_chat_history(self, clickedname):
        self.chat_obj.switch_to_chat(clickedname)

    @pyqtSlot()
    def populate_chat_histories_listbox(self):
        self.list_chat_histories.clear()
        for chat_name in self.chat_obj.chat_histories.keys():
            self.list_chat_histories.addItem(chat_name)

    @pyqtSlot()
    def update_chat_display(self):
        self.browser_chat_html.setHtml(self.chat_obj.html_head +
                                       self.chat_obj.html_chat +
                                       self.chat_obj.html_tail )

    @pyqtSlot()
    def get_response(self):
        self.button.setEnabled(False)
        self.thread = OpenAIAPIThread("Hello, how are you?")
        self.thread.response_received.connect(self.update_label)
        self.thread.start()

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
