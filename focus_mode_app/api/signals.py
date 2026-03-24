"""
Thread-safe queue bridge for the FastAPI server to communicate with the Tkinter GUI.

This module guarantees that state mutations requested via the API are passed
safely to the main Tkinter event loop using a thread-safe Queue, preventing
framework crashes.
"""

import queue

# A thread-safe queue to pass requested state changes from the API to the GUI
api_action_queue = queue.Queue()
