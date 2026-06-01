import os
from flask import Flask, request, jsonify, render_template
from flask_mail import Mail, Message
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Mail Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mail = Mail(app)

# MongoDB Configuration
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client["email_service"]

# Home Route
@app.route("/")
def home():
    return """
    <h1>Email Flask App is Running Successfully 🚀</h1>
    <h3>Available Routes:</h3>
    <ul>
        <li>POST /org</li>
        <li>POST /sendmail/&lt;org_name&gt;</li>
        <li><a href="/emails">View Email Logs</a></li>
    </ul>
    """

# Add Organization
@app.route('/org', methods=["POST"])
def add_org():
    data = request.json

    db.organizations.update_one(
        {'org_name': data["org_name"]},
        {'$set': {'emails': data['emails']}},
        upsert=True
    )

    return jsonify({"message": "Org Saved Successfully"})

# Send Email
@app.route('/sendmail/<org_name>', methods=["POST"])
def sendemail(org_name):

    payload = request.json

    org = db.organizations.find_one({'org_name': org_name})

    if not org:
        return jsonify({"message": "Org not found"}), 404

    emails = org['emails']

    msg = Message(
        subject=f'Contact Form - {org_name}',
        sender=app.config['MAIL_USERNAME'],
        recipients=emails
    )

    msg.body = str(payload)

    mail.send(msg)

    db.email_logs.insert_one({
        "org_name": org_name,
        "emails": emails,
        "content": payload
    })

    return jsonify({"message": "Email sent successfully"})

# View Email Logs
@app.route("/emails")
def emails():

    logs = list(db.email_logs.find({}, {"_id": 0}))

    return render_template(
        "emails.html",
        logs=logs
    )

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)