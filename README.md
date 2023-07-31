# OpenAI Chat Application

This Python application provides a graphical user interface for chatting with OpenAI's GPT-3 model. It's built with PyQt5 and uses the OpenAI API.

## Features

- Multithreaded API calls to ensure GUI responsiveness.
- Ability to save and load chat history in JSON format.
- Dynamic HTML chat display with different colors for user, assistant, and system messages.
- Ability to create, select, and delete multiple chat histories.

## Libraries Used

- `openai` for the AI model.
- `json` for handling JSON data.
- `markdown` for markdown to HTML conversion.
- `PyQt5` for creating the GUI.

## How to Run

The application can be run as a standard Python script:
python gpt.py

## Structure of the Code

The code is structured into several classes:

- `OpenAIAPIThread`: Handles the API calls to the OpenAI GPT-3 model in a separate thread.
- `ChatHistory`: Manages the chat history.
- `MyTextEdit`: A custom text edit field used for the user to enter their chat messages.
- `MainWindow`: The main window of the application.
