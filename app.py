from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route('/')
def dashboard():
    log_folder = 'static/facelogs'
    
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    images = sorted(os.listdir(log_folder), reverse=True)
    image_paths = [
        f'{log_folder}/{img}' for img in images if img.lower().endswith('.jpg')
    ]

    return render_template('dashboard.html', images=image_paths)

if __name__ == '__main__':
    app.run(debug=True)
