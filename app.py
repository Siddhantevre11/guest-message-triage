from backend.bootstrap import load_environment

load_environment()

from frontend.app import app

if __name__ == "__main__":
    app.run(debug=True)
