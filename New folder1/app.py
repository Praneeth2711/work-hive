import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client # Import the Twilio client

# --- Step 1: Initialize Flask and Firebase ---

# Initialize Flask App
app = Flask(__name__)
# Enable CORS to allow requests from your front-end
CORS(app)

# Initialize Firebase Admin SDK
# IMPORTANT: Make sure 'serviceAccountKey.json' is in the same folder as this file.
try:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase connection successful.")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    db = None

# A simple dictionary to temporarily store OTPs. 
# In a real app, use a more robust solution like Redis.
otp_storage = {}

# --- Twilio Configuration ---
# Replace these with your actual credentials from the Twilio dashboard
TWILIO_ACCOUNT_SID ='AC03b3ad5b0702a7e432f8f5f8ed9c09fb'
TWILIO_AUTH_TOKEN = '68c2b3f10ed458f4257bf743c0949f03'
TWILIO_PHONE_NUMBER = '+17193165331'
 # Must be a phone number you got from Twilio

# Initialize the Twilio client
try:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    print("Twilio client initialized.")
except Exception as e:
    client = None
    print(f"Error initializing Twilio client: {e}. Please check your credentials.")

# --- Email Configuration for Forgot Password ---
# IMPORTANT: Use a Gmail "App Password", not your regular password.
EMAIL_ADDRESS = 'your-email@gmail.com'
EMAIL_PASSWORD = 'your-16-character-app-password'


# --- Step 2: API Endpoints ---

@app.route('/')
def index():
    return "Flask + Firebase backend is running!"

# API Endpoint for Hirer Registration
@app.route('/api/register/hirer', methods=['POST'])
def register_hirer():
    if not db:
        return jsonify({'message': 'Firebase connection not available.'}), 503

    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if not email or not password or not name:
            return jsonify({'message': 'Missing required fields: name, email, and password.'}), 400

        # Check if a user with this email already exists
        hirer_doc = db.collection('hirers').document(email).get()
        if hirer_doc.exists:
            return jsonify({'message': 'A user with this email already exists.'}), 409

        # Hash the password for security before storing it
        hashed_password = generate_password_hash(password)

        # Create a new document in the 'hirers' collection
        db.collection('hirers').document(email).set({
            'name': name,
            'email': email,
            'password_hash': hashed_password,
            'createdAt': firestore.SERVER_TIMESTAMP,
            # Adding placeholder data for the new fields
            'company': 'Your Company',
            'industry': 'Your Industry',
            'phone': 'Not set',
            'about': 'Tell us about your company.',
            'location': 'Your Location'
        })

        return jsonify({'message': f'Hirer "{name}" registered successfully!'}), 201

    except Exception as e:
        print(f"An Error Occurred during hirer registration: {e}")
        return jsonify({'message': 'An error occurred on the server.'}), 500

# API Endpoint for Hirer Login
@app.route('/api/login/hirer', methods=['POST'])
def login_hirer():
    if not db:
        return jsonify({'message': 'Firebase connection not available.'}), 503

    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'message': 'Email and password are required.'}), 400

        # Fetch the user document from Firestore
        hirer_ref = db.collection('hirers').document(email)
        hirer_doc = hirer_ref.get()

        if not hirer_doc.exists:
            return jsonify({'message': 'User not found. Please check your email or register.'}), 404

        # Get user data from the document
        user_data = hirer_doc.to_dict()
        stored_password_hash = user_data.get('password_hash')

        # Check if the provided password matches the stored hash
        if check_password_hash(stored_password_hash, password):
            # Passwords match! Login is successful.
            # Return user's name along with the success message
            return jsonify({'message': 'Login successful!', 'name': user_data.get('name')}), 200
        else:
            # Passwords do not match.
            return jsonify({'message': 'Invalid credentials. Please try again.'}), 401

    except Exception as e:
        print(f"An Error Occurred during hirer login: {e}")
        return jsonify({'message': 'An error occurred on the server.'}), 500

# API Endpoint to Get Hirer Profile Details
@app.route('/api/hirer/profile/<email>', methods=['GET'])
def get_hirer_profile(email):
    if not db:
        return jsonify({'message': 'Firebase connection not available.'}), 503
    try:
        if not email:
            return jsonify({'message': 'Email is required.'}), 400

        hirer_doc = db.collection('hirers').document(email).get()

        if not hirer_doc.exists:
            return jsonify({'message': 'Hirer profile not found.'}), 404

        return jsonify(hirer_doc.to_dict()), 200
    except Exception as e:
        print(f"An Error Occurred fetching hirer profile: {e}")
        return jsonify({'message': 'An error occurred on the server.'}), 500

# API Endpoint to Update Hirer Profile
@app.route('/api/hirer/profile/update', methods=['POST'])
def update_hirer_profile():
    if not db:
        return jsonify({'message': 'Firebase connection not available.'}), 503
    try:
        data = request.get_json()
        email = data.get('email')
        if not email:
            return jsonify({'message': 'Email is required to update profile.'}), 400

        hirer_ref = db.collection('hirers').document(email)
        
        # Prepare data for update, excluding the email itself
        update_data = {
            'company': data.get('company'),
            'industry': data.get('industry'),
            'phone': data.get('phone'),
            'about': data.get('about'),
            'location': data.get('location')
        }
        
        hirer_ref.update(update_data)
        
        return jsonify({'message': 'Profile updated successfully!'}), 200
    except Exception as e:
        print(f"An Error Occurred updating hirer profile: {e}")
        return jsonify({'message': 'An error occurred on the server.'}), 500


# API Endpoint to Send OTP for Worker Registration
@app.route('/api/register/worker/send-otp', methods=['POST'])
def send_worker_otp():
    if not client:
        return jsonify({'message': 'Twilio service is not configured correctly.'}), 503
        
    data = request.get_json()
    phone = data.get('phone')

    if not phone or len(phone) != 10:
        return jsonify({'message': 'A valid 10-digit phone number is required.'}), 400
    
    # Generate a 4-digit OTP
    otp = str(random.randint(1000, 9999))
    otp_storage[phone] = otp

    try:
        # Send the OTP via Twilio SMS
        message = client.messages.create(
            body=f"Your WorkHive verification code is: {otp}",
            from_=TWILIO_PHONE_NUMBER,
            to=f'+91{phone}'  # Add the country code for India
        )
        print(f"OTP for {phone} is: {otp}. SMS SID: {message.sid}")
        return jsonify({'message': 'OTP sent successfully!'}), 200
    except Exception as e:
        print(f"Twilio Error: {e}")
        return jsonify({'message': 'Failed to send OTP. Please check the server logs.'}), 500


# API Endpoint to Verify OTP and Register Worker
@app.route('/api/register/worker/verify', methods=['POST'])
def verify_worker_and_register():
    if not db:
        return jsonify({'message': 'Firebase connection not available.'}), 503

    try:
        data = request.get_json()
        phone = data.get('phone')
        otp = data.get('otp')
        name = data.get('name')
        # ... get other worker details (gender, age, etc.)

        if not phone or not otp or not name:
            return jsonify({'message': 'Missing required fields.'}), 400

        # Verify OTP
        if otp_storage.get(phone) != otp:
            return jsonify({'message': 'Invalid OTP. Please try again.'}), 401
        
        # OTP is correct, now register the user in Firestore
        worker_doc = db.collection('workers').document(phone).get()
        if worker_doc.exists:
            return jsonify({'message': 'A worker with this phone number already exists.'}), 409

        # Add new worker to the 'workers' collection
        db.collection('workers').document(phone).set({
            'name': name,
            'phone': phone,
            'gender': data.get('gender'),
            'age': data.get('age'),
            'occupation': data.get('occupation'),
            'location': data.get('location'),
            'createdAt': firestore.SERVER_TIMESTAMP
        })

        # Clean up the used OTP
        del otp_storage[phone]

        return jsonify({'message': f'Worker "{name}" registered successfully!'}), 201

    except Exception as e:
        print(f"An Error Occurred during worker registration: {e}")
        return jsonify({'message': 'An error occurred on the server.'}), 500

# API Endpoint to Send OTP for Worker Login
@app.route('/api/login/worker/send-otp', methods=['POST'])
def send_worker_login_otp():
    if not client:
        return jsonify({'message': 'Twilio service is not configured correctly.'}), 503
        
    data = request.get_json()
    phone = data.get('phone')

    if not phone or len(phone) != 10:
        return jsonify({'message': 'A valid 10-digit phone number is required.'}), 400

    # Check if a worker with this phone number exists
    worker_doc = db.collection('workers').document(phone).get()
    if not worker_doc.exists:
        return jsonify({'message': 'No worker is registered with this phone number.'}), 404
    
    # Generate and send OTP
    otp = str(random.randint(1000, 9999))
    otp_storage[phone] = otp

    try:
        message = client.messages.create(
            body=f"Your WorkHive login code is: {otp}",
            from_=TWILIO_PHONE_NUMBER,
            to=f'+91{phone}'
        )
        print(f"Login OTP for {phone} is: {otp}. SMS SID: {message.sid}")
        return jsonify({'message': 'Login OTP sent successfully!'}), 200
    except Exception as e:
        print(f"Twilio Error: {e}")
        return jsonify({'message': 'Failed to send OTP. Please check the server logs.'}), 500

# API Endpoint to Verify OTP and Log In Worker
@app.route('/api/login/worker/verify', methods=['POST'])
def verify_worker_login():
    data = request.get_json()
    phone = data.get('phone')
    otp = data.get('otp')

    if not phone or not otp:
        return jsonify({'message': 'Phone number and OTP are required.'}), 400

    # Verify OTP
    if otp_storage.get(phone) != otp:
        return jsonify({'message': 'Invalid OTP. Please try again.'}), 401

    # Clean up the used OTP
    del otp_storage[phone]

    return jsonify({'message': 'Login successful!'}), 200
    
# API Endpoint for Hirer Forgot Password
@app.route('/api/hirer/forgot-password', methods=['POST'])
def hirer_forgot_password():
    if not db:
        return jsonify({'message': 'Firebase connection not available.'}), 503

    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email is required.'}), 400

    # Check if user exists
    hirer_ref = db.collection('hirers').document(email)
    if not hirer_ref.get().exists:
        # We don't want to reveal if an email is registered or not for security
        return jsonify({'message': 'If an account with that email exists, a new password has been sent.'}), 200

    # Generate a new random temporary password
    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    new_password_hash = generate_password_hash(temp_password)

    # Update the user's password in Firestore
    hirer_ref.update({'password_hash': new_password_hash})

    # Send the temporary password to the user's email
    try:
        msg = MIMEText(f"Hello,\n\nYour temporary password for WorkHive is: {temp_password}\n\nPlease log in with this password and change it immediately.\n\nThank you,\nThe WorkHive Team")
        msg['Subject'] = 'Your Temporary WorkHive Password'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp_server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
        
        print(f"Temporary password sent to {email}")

    except Exception as e:
        print(f"Email sending failed for {email}: {e}")
        # Even if email fails, we don't tell the user, for security.
    
    return jsonify({'message': 'If an account with that email exists, a new password has been sent.'}), 200

# --- NEW: API Endpoints for Worker Profile ---
@app.route('/api/worker/profile/<phone>', methods=['GET'])
def get_worker_profile(phone):
    if not db:
        return jsonify({'message': 'Firebase connection not available.'}), 503
    try:
        worker_doc = db.collection('workers').document(phone).get()
        if not worker_doc.exists:
            return jsonify({'message': 'Worker profile not found.'}), 404
        return jsonify(worker_doc.to_dict()), 200
    except Exception as e:
        print(f"An Error Occurred fetching worker profile: {e}")
        return jsonify({'message': 'An error occurred on the server.'}), 500

@app.route('/api/worker/profile/update', methods=['POST'])
def update_worker_profile():
    if not db:
        return jsonify({'message': 'Firebase connection not available.'}), 503
    try:
        data = request.get_json()
        phone = data.get('phone')
        if not phone:
            return jsonify({'message': 'Phone number is required to update profile.'}), 400

        worker_ref = db.collection('workers').document(phone)
        
        update_data = {
            'name': data.get('name'),
            'occupation': data.get('occupation'),
            'location': data.get('location')
        }
        
        worker_ref.update(update_data)
        
        return jsonify({'message': 'Profile updated successfully!'}), 200
    except Exception as e:
        print(f"An Error Occurred updating worker profile: {e}")
        return jsonify({'message': 'An error occurred on the server.'}), 500


# --- Step 3: Run the App ---

if __name__ == '__main__':
    # Use port 8000 to avoid conflicts with other services
    app.run(debug=True, port=8000)
