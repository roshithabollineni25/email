import os
from flask import Flask, request, jsonify, render_template
from flask_mail import Mail, Message
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mail = Mail(app)

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client["email_service"]

@app.route('/org', methods=["POST"])
def add_org():
    data = request.json
    db.organizations.update_one(
        {'org_name': data["org_name"]},
        {'$set': {'emails': data['emails']}},
        upsert=True
    )
    return jsonify({"message": "Org Saved Successfully"})

@app.route('/sendmail/<org_name>', methods=["POST"])
def sendemail(org_name):
    payload = request.json
    
   
    org = db.organizations.find_one({'org_name': org_name})
    if not org:
        return jsonify({"message": "Org not found"})
        
    emails = org['emails']
    
   
    msg = Message(
        subject=f'Contact Form - {org_name}',
        sender=os.getenv("MAIL_USERNAME"),  
        recipients=emails
    )
    
    
    msg.body = str(payload)
    
  
    mail.send(msg)
    
   
    db.email_logs.insert_one({
        "org_name": org_name,
        "email": emails,
        "Content": payload
    })
    
    return jsonify({"Message": "Email sent Successfully"})

@app.route("/emails")
def emails():
    logs = list(db.email_logs.find({}, {"_id": 0}))
    return render_template("emails.html", logs=logs)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

