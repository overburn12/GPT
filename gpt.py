import openai
import json
import tkinter as tk
from openai.error import OpenAIError
from tkinter import simpledialog, messagebox

class ChatApp:
    def __init__(self):
        # load the API key
        with open('not-an-api-key.txt', 'r') as file:
            openai.api_key = file.read()

        self.fileName = "chat_history.json"

        self.chat_histories = {}
        self.current_chat = "chat1"

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

        # Add a list box for selecting chat histories
        self.chat_listbox = tk.Listbox(self.root)
        self.chat_listbox.grid(column=2, row=0, sticky='nsew')
        #self.chat_listbox.bind('<<ListboxSelect>>', self.load_selected_chat)
        self.chat_listbox.bind('<<ListboxSelect>>', self.load_selected_chat_if_focused)

        # Add buttons for adding and deleting chats
        add_chat_button = tk.Button(self.root, text="Add Chat", command=self.add_chat)
        add_chat_button.grid(column=2, row=1, sticky='nsew')
        delete_chat_button = tk.Button(self.root, text="Delete Chat", command=self.delete_chat)
        delete_chat_button.grid(column=2, row=2, sticky='nsew')
        rename_chat_button = tk.Button(self.root, text="Rename Chat", command=self.rename_chat)
        rename_chat_button.grid(column=2, row=3, sticky='nsew')
        

        # Load chat histories file
        self.load_chat_histories(self.fileName)

        self.user_input = tk.Text(self.root, height=5)
        self.user_input.grid(column=0, row=1, sticky='nsew')
        self.user_input.bind("<Return>", self.send_message)

        # Configure column and row weights
        self.root.grid_columnconfigure(0, weight=1)  # the first column should expand
        self.root.grid_rowconfigure(0, weight=1)  # the first row should expand

        self.root.mainloop()

    def load_chat_histories(self, filename):
        # Load all chat histories from the selected file
        try:
            with open(filename, 'r') as f:
                self.chat_histories = json.load(f)
        except FileNotFoundError:
            self.chat_histories = {"chat1": [{"role": "system", "content": "You are a helpful assistant."}]}

        # Populate the list box with chat history names
        self.chat_listbox.delete(0, tk.END)  # clear the list box
        for chat_name in self.chat_histories.keys():
            self.chat_listbox.insert(tk.END, chat_name)

        # Load the first chat history
        self.load_selected_chat()

    def load_selected_chat(self, event=None):
        # Get the selected chat history
        selection = self.chat_listbox.curselection()
        if selection:
            self.current_chat = self.chat_listbox.get(selection[0])
        else:
            # If nothing is selected, default to the first chat history
            self.current_chat = list(self.chat_histories.keys())[0]

        # Clear the current chat display
        self.chat_history.delete('1.0', tk.END)

        # Display the selected chat history
        for message in self.chat_histories[self.current_chat]:
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

            self.chat_histories[self.current_chat].append(message)

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=self.chat_histories[self.current_chat]  # Pass the entire conversation history
                )
                ai_message = {"role": "assistant", "content": response['choices'][0]['message']['content']}

                self.add_message_to_chat(ai_message)
                self.chat_histories[self.current_chat].append(ai_message)

            except OpenAIError as e:
                self.chat_history.insert(tk.END, 'Error: ' + str(e) + '\n')

            return "break"  # prevent the default behavior of the Enter key

    def on_closing(self):
        # Save all chat histories to JSON file
        with open(self.fileName, 'w') as f:
            json.dump(self.chat_histories, f)
        self.root.destroy()

    def add_chat(self):
        # Prompt the user for a new chat name
        new_chat_name = simpledialog.askstring("New Chat", "Enter name for new chat:")
        if new_chat_name:
            if new_chat_name in self.chat_histories:
                messagebox.showerror("Error", "A chat with that name already exists.")
            else:
                self.chat_histories[new_chat_name] = []
                self.chat_listbox.insert(tk.END, new_chat_name)

    def delete_chat(self):
        # Delete the currently selected chat
        selection = self.chat_listbox.curselection()
        if selection:
            chat_name = self.chat_listbox.get(selection[0])
            if messagebox.askyesno("Delete Chat", f"Are you sure you want to delete {chat_name}? This cannot be undone."):
                del self.chat_histories[chat_name]
                self.chat_listbox.delete(selection[0])
                
                # Check if all chat histories are deleted
                if len(self.chat_histories) == 0:
                    # If so, recreate a default chat history
                    default_chat_name = "chat1"
                    self.chat_histories[default_chat_name] = [{"role": "system", "content": "You are a helpful assistant."}]
                    self.chat_listbox.insert(tk.END, default_chat_name)

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

    def rename_chat(self):
        # Prompt the user for a new chat name
        new_chat_name = simpledialog.askstring("Rename Chat", "Enter new name for the chat:")
        if new_chat_name:
            if new_chat_name in self.chat_histories:
                messagebox.showerror("Error", "A chat with that name already exists.")
            else:
                # Get the currently selected chat
                selection = self.chat_listbox.curselection()
                if selection:
                    old_chat_name = self.chat_listbox.get(selection[0])
                    # Rename the chat in the chat_histories dictionary
                    self.chat_histories[new_chat_name] = self.chat_histories.pop(old_chat_name)
                    # Update the name in the listbox
                    self.chat_listbox.delete(selection[0])
                    self.chat_listbox.insert(selection[0], new_chat_name)

    def load_selected_chat_if_focused(self, event=None):
        if self.chat_listbox is self.root.focus_get():
            self.load_selected_chat()

if __name__ == "__main__":
    app = ChatApp()