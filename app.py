from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os
from supabase import create_client, Client 
import supabase
from dotenv import load_dotenv
from urllib.parse import unquote, urlparse
import uuid
from werkzeug.utils import secure_filename


SUPABASE_URL = "https://jgaapanxbjpbduxamlgf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpnYWFwYW54YmpwYmR1eGFtbGdmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIxMTY5OTYsImV4cCI6MjA1NzY5Mjk5Nn0.8k2g2dryfGuS7DgbUQmmN4at_gXxNKYCvxs4EFxf0yE"
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
#CORS(app)  # Enable CORS for frontend access

if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate('Temp.json'))

# Get Firestore database reference
db = firestore.client()
def createFire(collection_path, data, documentName=False):
    
    # Add the document to Firestore
    if documentName:
        doc_ref = db.collection(collection_path).document(documentName)
    else:
        doc_ref = db.collection(collection_path).document()
    doc_ref.set(data,merge=True)
    return doc_ref

@app.route('/upload-file/<p_ID>', methods=['POST'])
def upload_file(p_ID):
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        filename = secure_filename(file.filename)
        file_path = f"files/{filename}"  # Storing in 'profile/files/'

        # Upload to Supabase Storage
        response = supabase_client.storage.from_("profile").upload(file_path, file.read(), file.content_type)
        print("Supabase Response:", response)  # Debugging

        # Get Public URL
        public_url = supabase_client.storage.from_("profile").get_public_url(file_path)

        # Save URL in Firebase
        pText = {"cv-resume": public_url}
        createFire(f"Users/{p_ID}/Profile", pText, "p_Text")

        return jsonify({"message": "File uploaded successfully", "url": public_url, "response": response}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Flask Route to Add or Update Links
@app.route('/edit-link/<p_ID>/<platform>', methods=['GET'])
def update_link(p_ID, platform):
    try:
        link = request.args.get('link')

        if not link:
            return jsonify({"error": "Missing link parameter"}), 400

        # Firestore update
        pText = {platform: link}
        success = createFire(f"Users/{p_ID}/Profile", pText, "p_text")

        if not success:
            return jsonify({"error": "Failed to update Firestore"}), 500

        return jsonify({
            "message": f"{platform} link updated successfully",
            "updated_link": link,
            "p_text": pText
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to update link: {str(e)}"}), 500
    

# Supabase Configuration
SUPABASE_URL = "https://jgaapanxbjpbduxamlgf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpnYWFwYW54YmpwYmR1eGFtbGdmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIxMTY5OTYsImV4cCI6MjA1NzY5Mjk5Nn0.8k2g2dryfGuS7DgbUQmmN4at_gXxNKYCvxs4EFxf0yEy"
SUPABASE_BUCKET = "files"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


ALLOWED_EXTENSIONS = {'pdf', 'pptx', 'docx', 'xlsx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/uploads/filee", methods=['POST'])
def upload_filee():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    try:
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        file_id = str(uuid.uuid4()) + "." + file_ext
        file_path = f"uploads/{file_id}"

        # Upload file to Supabase Storage
        response = supabase.storage.from_(SUPABASE_BUCKET).upload(file_path, file.stream, file_ext)
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{file_path}"

        # Store file details in Firestore
        file_data = {
            "filename": file.filename,
            "url": public_url,
            "uploaded_at": firestore.SERVER_TIMESTAMP
        }
        db.collection("Files").add(file_data)

        return jsonify({"success": True, "url": public_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


# Run Flask App
if __name__ == '__main__':
    app.run(debug=True)
