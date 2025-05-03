from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
import requests
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from LLM import send_message  # Ensure that your LLM module is correctly imported

###################IMPORTING MODULES###################
load_dotenv()  # Load environment variables from .env file
app = Flask(__name__)
app.secret_key = 'sanath@123'

###################LOADING USERS###################
def load_users():
    if not os.path.exists("users.json"):
        return {}
    with open("users.json", "r") as f:
        return json.load(f)

###################SAVING USERS###################
def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f)

###################HOME PAGE###################
@app.route('/')
def home():
    return redirect(url_for('login'))

###################REGISTER PAGE###################
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            
            # Validate required fields
            if not all([username, password, email, phone, address]):
                flash("All fields are required!", "error")
                return render_template('register.html')
                
            users = load_users()
            if email in users:
                flash("Email already exists!", "error")
            else:
                users[email] = {
                    'password': password,
                    'username': username,
                    'phone': phone,
                    'address': address,
                }
                save_users(users)
                flash("Registered successfully! Please log in.", "success")
                return redirect(url_for('login'))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
    return render_template('register.html')

###################LOGIN PAGE###################
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_users()
        if email in users and users[email]['password'] == password:
            session['username'] = users[email]['username']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password!", "error")
    return render_template('login.html')

###################DASHBOARD PAGE###################
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'username' not in session:
        flash("You must be logged in to view the dashboard.", "error")
        return redirect(url_for('login'))
    
    # Use get instead of pop to retain session data
    plant_result = session.get('plant_result')
    plant_image_url = session.get('plant_image_url')
    
    return render_template('dashboard.html', 
                         username=session['username'], 
                         plant_result=plant_result, 
                         plant_image_url=plant_image_url)

###################UPLOAD PAGE###################
@app.route('/check', methods=['GET', 'POST'])
def check():
    plant_result = None
    plant_image_url = None
    error = None

    if request.method == 'POST':
        if 'username' not in session:
            flash("You must be logged in to upload.", "error")
            return redirect(url_for('login'))

        file = request.files.get('plant_image')
        organ = request.form.get('organ')

        if not file or file.filename == '' or not organ:
            flash("Please select both an image and an organ type.", "error")
        else:
            # Ensure 'static/uploads' folder exists
            if not os.path.exists('static/uploads'):
                os.makedirs('static/uploads')

            # Save temporarily with secure filename
            filename = secure_filename(file.filename)
            filepath = os.path.join("static/uploads", filename)
            file.save(filepath)

            # PlantNet API call
            api_url = "https://my-api.plantnet.org/v2/identify/all"
            params = {
                "include-related-images": "false",
                "no-reject": "false",
                "nb-results": "10",
                "lang": "en",
                "api-key": os.getenv('PLANTNET_API_KEY') 
            }

            try:
                with open(filepath, "rb") as image_file:
                    files = {'images': image_file}
                    data = {'organs': organ}
                    response = requests.post(api_url, params=params, files=files, data=data)
                response.raise_for_status()
                result = response.json()
                if result.get("results"):
                    plant_result = send_message(str(result["results"][0]['species']['commonNames']))

                    plant_image_url = url_for('static', filename=f'uploads/{filename}')
                    session['plant_result'] = plant_result
                    session['plant_image_url'] = plant_image_url
                else:
                    flash("No results found from PlantNet API.", "error")
            except Exception as e:
                flash(f"Error processing image: {str(e)}", "error")
                error = str(e)
            finally:
                # Keep the image until rendering is complete (delete later if needed)
                pass

    return render_template('check.html', 
                         plant_result=plant_result, 
                         plant_image_url=plant_image_url, 
                         error=error)

###################LOGOUT PAGE###################
@app.route('/logout')
def logout():
    # Clean up user-specific uploads
    user_folder = os.path.join('static/uploads', session.get('username', 'temp'))
    if os.path.exists(user_folder):
        for file in os.listdir(user_folder):
            os.remove(os.path.join(user_folder, file))
        os.rmdir(user_folder)
    session.pop('username', None)
    session.pop('plant_result', None)
    session.pop('plant_image_url', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('home'))

###################GET RESPONSE###################
def get_response(data):
    format_type = """
    Given the identified species, provide detailed agricultural information based on the following points in markdown format:
    1. Types (including scientific and common names)
    2. Expected diseases affecting this crop
    3. Nutrients needed for optimal growth
    4. Best season to harvest
    5. Farming requirements and cost estimate
    6. Current market price in India
    7. Ideal temperature and climate for growth
    Format the entire response in markdown with clear section headings.
    """
    return send_message(str(data) + format_type)


@app.route('/admin_page')
def admin_page():
    if 'username' not in session:
        flash("You must be logged in to view the admin page.", "error")
        return redirect(url_for('login'))
    
    users = load_users()
    return render_template('admin_page.html', users=users)

###################MAIN FUNCTION###################
if __name__ == '__main__':
    app.run(debug=True)
