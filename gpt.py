import openai
import json
import markdown

from PyQt5.QtWidgets import QApplication, QGridLayout, QListWidget, QPushButton, QWidget, QPlainTextEdit, QTextBrowser, QInputDialog, QMessageBox
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal, QObject, QEvent, Qt
from openai.error import OpenAIError

class OpenAIAPIThread(QThread):
    response_received = pyqtSignal(dict)
    error_occurred = pyqtSignal(OpenAIError)

    def __init__(self, chat_history):
        super().__init__()
        self.chat_history = chat_history
        self.use_model = "gpt-3.5-turbo" 
        with open("api-key.txt", 'r') as file:
            openai.api_key = file.read()

    def run(self):
        try:
            response = openai.ChatCompletion.create(
                model=self.use_model,
                messages=self.chat_history  # Pass the entire conversation history
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
            self.add_message_to_chat(message)
            self.thread = OpenAIAPIThread(self.chat_histories[self.current_chat])
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
        content = message['content']#.replace('\n', '<br>')
        
        if role == "user":
            color = "blue"
        elif role == "assistant":
            color = "red"
        else:
            color = "black"

        return markdown.markdown(f"<b style='color:{color};'>{role}:</b> {content}", extras=["fenced-code-blocks"])

    def add_new_chat(self, chatname):
        self.chat_histories[chatname] = [{"role": "system", "content": "You are a helpful assistant."}]
        self.chat_histories_update.emit()
        self.switch_to_chat(chatname)

    #def rename_chat(self):

    def delete_chat(self, chatname):
        del self.chat_histories[chatname]
        if not self.chat_histories:
            self.add_new_chat("chat 1")

    @pyqtSlot(dict)
    def handle_api_message(self, ai_message):
        self.add_message_to_chat(ai_message)

    @pyqtSlot(dict)
    def handle_api_error(self, error):
        error_msg =  {"role": "ERROR", "content": str(error)}
        self.html_chat += self.convert_msg_to_html(error_msg)
        self.chat_updated.emit()

class MyTextEdit(QPlainTextEdit):
    def __init__(self, *args, **kwargs):
        super(MyTextEdit, self).__init__(*args, **kwargs)
        self.setPlaceholderText('Enter your message here...')

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Return and not e.modifiers() & Qt.ShiftModifier:
            self.parent().send_chat_message()  # call the send_message method when Enter is pressed without Shift
        else:
            super().keyPressEvent(e)  # default behaviour

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
        self.text_user_input =  MyTextEdit(self)
        self.list_chat_histories = QListWidget()
        self.browser_chat_html = QTextBrowser()

        self.list_chat_histories.itemClicked.connect(lambda item: self.select_chat_history(item.text()))
        self.button_add_chat.clicked.connect(self.add_new_chat)
        self.button_delete_chat.clicked.connect(self.delete_selected_chat)

        #self.list_chat_histories.setFixedWidth(200)

        #construct the layout of the GUI
        chat_list_left = 14
        button_width = 2
        chat_list_height = 9
        layout.addWidget(self.browser_chat_html, 0, 0, chat_list_height, chat_list_left)  
        layout.addWidget(self.list_chat_histories, 0, chat_list_left, chat_list_height, button_width)  
        layout.addWidget(self.text_user_input, chat_list_height, 0, 3, chat_list_left)
        layout.addWidget(self.button_add_chat, chat_list_height, chat_list_left, 1, button_width)
        layout.addWidget(self.button_rename_chat, chat_list_height+1, chat_list_left, 1, button_width) 
        layout.addWidget(self.button_delete_chat, chat_list_height+2, chat_list_left, 1, button_width)
        self.setLayout(layout)

    def closeEvent(self, event: QEvent):
        self.chat_obj.save_chat_file()
        super().closeEvent(event)

    @pyqtSlot()
    def send_chat_message(self):
        user_message = self.text_user_input.toPlainText()
        self.chat_obj.send_api_message(user_message)
        self.text_user_input.clear()

    @pyqtSlot()
    def delete_selected_chat(self):
        if self.list_chat_histories.selectedItems():
            reply = QMessageBox.question(None, "Delete chat", "Are you sure you want to delete the selected chat?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
            selected_item = self.list_chat_histories.selectedItems()[0]
            chatname = selected_item.text()
            item = self.list_chat_histories.takeItem(self.list_chat_histories.row(selected_item))
            del item
            self.chat_obj.delete_chat(chatname)
            #self.list_chat_histories.setCurrentRow(0)
            #self.chat_obj.switch_to_chat(self.list_chat_histories.item(0).text())
        else:
            QMessageBox.warning(None, "Problem", "Cannot delete chat. No chat currently selected.")                

    @pyqtSlot()
    def add_new_chat(self):
        new_chat_name, ok = QInputDialog.getText(None, "New chat", "Enter the name of the new chat:")
        if ok:
            if new_chat_name not in self.chat_obj.chat_histories:
                self.list_chat_histories.addItem(new_chat_name)
                self.chat_obj.add_new_chat(new_chat_name)
            else: 
                QMessageBox.warning(None, "Duplicate chat name", "The chat name is already used. Please choose a different name.")            

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

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
