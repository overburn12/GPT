import openai
import json
import tkinter as tk
from openai.error import OpenAIError

class ChatApp:
    def __init__(self):
        # load the API key
        with open('not-an-api-key.txt', 'r') as file:
            openai.api_key = file.read()

        self.chat_history_list = []
        self.root = tk.Tk()
        self.root.title("Chat with AI")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        scrollbar = tk.Scrollbar(self.root)
        scrollbar.grid(column=1, row=0, sticky='ns')

        self.chat_history = tk.Text(self.root, wrap='word', yscrollcommand=scrollbar.set)
        self.chat_history.configure(exportselection=True) # enable text selection 
        self.chat_history.grid(column=0, row=0, sticky='nsew')

        # Link the scrollbar to the chat window
        scrollbar.config(command=self.chat_history.yview)

        # Configure tags
        self.chat_history.tag_config("user_role", foreground="blue", background="light gray", font=("Helvetica", 10, "bold"))
        self.chat_history.tag_config("assistant_role", foreground="red", background="white", font=("Helvetica", 10, "bold"))
        self.chat_history.tag_config("user_content", foreground="black", background="light gray")

        # Load chat history file
        self.load_chat_history('chat_history.json')

        self.user_input = tk.Text(self.root, height=5)
        self.user_input.grid(column=0, row=1, sticky='nsew')
        self.user_input.bind("<Return>", self.send_message)

        # Configure column and row weights
        self.root.grid_columnconfigure(0, weight=1)  # the first column should expand
        self.root.grid_rowconfigure(0, weight=1)  # the first row should expand

        self.root.mainloop()

    def load_chat_history(self, filename):
        # Load chat history from the selected file
        try:
            with open(filename, 'r') as f:
                self.chat_history_list = json.load(f).get('chat_history', [])
        except FileNotFoundError:
            self.chat_history_list = [{"role": "system", "content": "You are a helpful assistant."}]

        # Clear the current chat display
        self.chat_history.delete('1.0', tk.END)

        # Display the loaded chat history
        for message in self.chat_history_list:
            self.add_message_to_chat(message)

    def send_message(self, event=None):
        # Check if the event was a keypress event and the Shift key was being held down
        if event and event.state & 0x1:
            return  # don't send the message if the Shift key was held down

        message_content = self.user_input.get("1.0", "end-1c")
        if message_content.strip() != "":  # only send the message if it's not empty
            message = {"role": "user", "content": message_content}
            self.add_message_to_chat(message)
            self.user_input.delete("1.0", tk.END)

            self.chat_history_list.append(message)

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=self.chat_history_list  # Pass the entire conversation history
                )
                ai_message = {"role": "assistant", "content": response['choices'][0]['message']['content']}

                self.add_message_to_chat(ai_message)
                self.chat_history_list.append(ai_message)

            except OpenAIError as e:
                self.chat_history.insert(tk.END, 'Error: ' + str(e) + '\\n')

            return "break"  # prevent the default behavior of the Enter key

    def on_closing(self):
        # Save chat history to JSON file
        with open('chat_history.json', 'w') as f:
            json.dump({"chat_history": self.chat_history_list}, f)
        self.root.destroy()

    def add_message_to_chat(self, message):
        role = message['role'].capitalize()
        content = message['content']

        # Insert the role part of the text with the role tag
        if role.lower() == "user":
            self.chat_history.insert(tk.END, f"{role}: ", "user_role")
        else:
            self.chat_history.insert(tk.END, f"{role}: ", "assistant_role")

        # Insert the content part of the text with the content tag
        if role.lower() == "user":
            self.chat_history.insert(tk.END, f"{content}\n", "user_content")
        else:
            self.chat_history.insert(tk.END, f"{content}\n")

if __name__ == "__main__":
    app = ChatApp()
