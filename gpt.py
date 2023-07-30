import openai
import json
import markdown2

from PyQt5.QtWidgets import QApplication, QGridLayout, QListWidget, QPushButton, QWidget, QPlainTextEdit, QTextBrowser
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal
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

class ChatHistory():
    def __init__(self):
        self.fileName = "chat_history.json"
        self.init_chat()
        self.load_chat_file()
    
    def init_chat(self):
        self.html_head = ""
        self.html_chat = ""
        self.html_tail = ""
        self.chat_histories = {"chat1": [{"role": "system", "content": "You are a helpful assistant."}]}
        self.current_chat = "chat1"

    def load_chat_file(self):
        # Load all chat histories from the file
        try:
            with open(self.fileName, 'r') as f:
                self.chat_histories = json.load(f)
        except FileNotFoundError:
            self.init_chat()
        
        #todo: load the chat history names into the GUI listbox
        # clear the list box
        # Populate the list box with chat history names
        #for chat_name in self.chat_histories.keys():
        #    self.chat_listbox.insert(tk.END, chat_name)
        # Load the first chat history
    
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

    def init_ui(self):

        layout = QGridLayout()
        button_add_chat = QPushButton("Add Chat")
        button_rename_chat = QPushButton("Rename Chat")
        button_delete_chat = QPushButton("Delete Chat")
        button_send_chat = QPushButton("Send")
        text_user_input = QPlainTextEdit()
        list_chat_histories = QListWidget()
        browser_chat_html = QTextBrowser()

        #button_send_chat.clicked.connect(self.get_response)

        layout.addWidget(browser_chat_html, 0, 0, 9, 12)  
        layout.addWidget(list_chat_histories, 0, 12, 6, 3)  
        layout.addWidget(text_user_input, 9, 0, 3, 12)

        layout.addWidget(button_send_chat, 9, 12, 3, 3) 
        layout.addWidget(button_add_chat, 6, 12, 1, 3)
        layout.addWidget(button_rename_chat, 7, 12, 1, 3) 
        layout.addWidget(button_delete_chat, 8, 12, 1, 3)

        self.setLayout(layout)

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
