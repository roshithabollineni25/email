import os
from flask import Flask, request, jsonify, render_template
from flask_mail import Mail, Message
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Mail Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mail = Mail(app)

# MongoDB Connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client["email_service"]


# ---------------- HOME PAGE ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- ADD ORGANIZATION ----------------
@app.route("/org-form", methods=["POST"])
def org_form():

    org_name = request.form["org_name"]
    emails = request.form["emails"].split(",")

    db.organizations.update_one(
        {"org_name": org_name},
        {"$set": {"emails": emails}},
        upsert=True
    )

    return "<h2>Organization Saved Successfully</h2><a href='/'>Go Back</a>"


# ---------------- SEND EMAIL ----------------
@app.route("/sendmail-form", methods=["POST"])
def sendmail_form():

    org_name = request.form["org_name"]

    payload = {
        "name": request.form["name"],
        "message": request.form["message"]
    }

    org = db.organizations.find_one(
        {"org_name": org_name}
    )

    if not org:
        return "<h2>Organization Not Found</h2>"

    msg = Message(
        subject=f"Contact Form - {org_name}",
        sender=os.getenv("MAIL_USERNAME"),
        recipients=org["emails"]
    )

    msg.body = f"""
Name: {payload['name']}

Message:
{payload['message']}
"""

    mail.send(msg)

    db.email_logs.insert_one({
        "org_name": org_name,
        "emails": org["emails"],
        "content": payload
    })

    return "<h2>Email Sent Successfully</h2><a href='/'>Go Back</a>"


# ---------------- EMAIL LOGS ----------------
@app.route("/emails")
def emails():

    logs = list(
        db.email_logs.find({}, {"_id": 0})
    )

    return render_template(
        "emails.html",
        logs=logs
    )


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)