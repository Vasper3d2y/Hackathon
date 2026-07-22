import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from backend import app, init_db

if __name__ == '__main__':
    init_db()
    print("Server running at http://127.0.0.1:5050/")
    app.run(debug=True, host='127.0.0.1', port=5050)
