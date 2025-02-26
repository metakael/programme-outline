"""
Programme Outline Generator Web App
-----------------------------------
Main application entry point
"""

from app import app, db

# Create database tables
@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
