import sqlite3
import os
import json
import hashlib
from docx import Document

class CodeSnippetManager:
    def __init__(self, storage_path='snippet_manager.db'):
        self.storage_path = storage_path
        self.connection = self.create_connection()
        self.create_table()
        self.user_id = None
        self.snippets = self.load_snippets()

    def create_connection(self):
        return sqlite3.connect(self.storage_path)

    def create_table(self):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS snippets (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    code TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tags TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

    def load_snippets(self):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT name, code, category, tags FROM snippets WHERE user_id = ?
            ''', (self.user_id,))
            return {'snippets': [{'name': row[0], 'code': row[1], 'category': row[2], 'tags': row[3]} for row in cursor.fetchall()]}

    def save_snippet(self, name, code, category='Uncategorized', tags=None):
        if tags is None:
            tags = []
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO snippets (user_id, name, code, category, tags) VALUES (?, ?, ?, ?, ?)
            ''', (self.user_id, name, code, category, ','.join(tags)))
            self.connection.commit()

    def search_snippets(self, keyword):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT name, code, category, tags FROM snippets
                WHERE user_id = ? AND (name LIKE ? OR code LIKE ? OR category LIKE ? OR tags LIKE ?)
            ''', (self.user_id, f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
            return [{'name': row[0], 'code': row[1], 'category': row[2], 'tags': row[3]} for row in cursor.fetchall()]

    def delete_snippet(self, name):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute('''
                DELETE FROM snippets WHERE user_id = ? AND name = ?
            ''', (self.user_id, name))
            self.connection.commit()

class UserManager:
    def __init__(self, storage_path='snippet_manager.db'):
        self.storage_path = storage_path
        self.connection = sqlite3.connect(self.storage_path)
        self.create_table()

    def create_table(self):
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL
                )
            ''')

    def create_user(self, username, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO users (username, password) VALUES (?, ?)
            ''', (username, hashed_password))
            self.connection.commit()

    def validate_user(self, username, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT id FROM users WHERE username = ? AND password = ?
            ''', (username, hashed_password))
            user_id = cursor.fetchone()
            return user_id[0] if user_id else None

# Function to log interactions to Word document
def log_interaction(doc, interaction):
    doc.add_paragraph(interaction)

# Login
# Updated login function
def login(user_manager, doc):
    while True:
        username = input("Enter your username: ")
        password = input("Enter your password: ")
        user_id = user_manager.validate_user(username, password)
        if user_id:
            log_interaction(doc, "Login successful!\n")
            return user_id
        else:
            log_interaction(doc, "Invalid credentials. Please try again.\n")
            create_account = input("Do you want to create a new account? (y/n): ")
            if create_account.lower() == 'y':
                user_manager.create_user(username, password)
                log_interaction(doc, f"Account for '{username}' created successfully.\n")
            else:
                log_interaction(doc, "Returning to the main menu.\n")
                break


# Main program
if __name__ == "__main__":
    user_manager = UserManager()
    code_manager = None

    # Creating a Word document
    doc = Document()

    while True:
        log_interaction(doc, "Code Snippet Manager")
        log_interaction(doc, "1. Login")
        log_interaction(doc, "2. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            user_id = login(user_manager, doc)
            code_manager = CodeSnippetManager()
            code_manager.user_id = user_id

            while True:
                log_interaction(doc, "\nCode Snippet Manager")
                log_interaction(doc, "1. List Snippets")
                log_interaction(doc, "2. Add Snippet")
                log_interaction(doc, "3. Search Snippets")
                log_interaction(doc, "4. Delete Snippet")
                log_interaction(doc, "5. Logout")

                user_choice = input("Enter your choice: ")

                if user_choice == '1':
                    code_manager.snippets = code_manager.load_snippets()
                    code_manager.list_snippets()
                elif user_choice == '2':
                    name = input("Enter snippet name: ")
                    code = input("Enter code: ")
                    category = input("Enter category (default is 'Uncategorized'): ")
                    tags = input("Enter tags (comma-separated): ").split(',')
                    code_manager.save_snippet(name, code, category, tags)
                    log_interaction(doc, f"Snippet '{name}' added successfully.")
                elif user_choice == '3':
                    keyword = input("Enter keyword to search: ")
                    results = code_manager.search_snippets(keyword)
                    if results:
                        log_interaction(doc, "\nSearch Results:")
                        for result in results:
                            log_interaction(doc, f"{result['name']} ({result['category']})")
                    else:
                        log_interaction(doc, "No matching snippets found.")
                elif user_choice == '4':
                    name = input("Enter the name of the snippet to delete: ")
                    code_manager.delete_snippet(name)
                    log_interaction(doc, f"Snippet '{name}' deleted successfully.")
                elif user_choice == '5':
                    log_interaction(doc, "Logging out.\n")
                    break
                else:
                    log_interaction(doc, "Invalid choice. Please enter a valid option.")
        elif choice == '2':
            log_interaction(doc, "Exiting Code Snippet Manager. Goodbye!")
            break
        else:
            log_interaction(doc, "Invalid choice. Please enter a valid option.")

    # Save interactions to a Word document
    doc.save("CodeSnippetManagerInteractions.docx")
