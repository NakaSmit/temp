from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

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

# Run Flask App
if __name__ == '__main__':
    app.run(debug=True)
