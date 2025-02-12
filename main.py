import sys
print("Using Python from:", sys.executable)

from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

