from flask import Flask, render_template, request, jsonify
import json
import base64
from supabase import create_client
from pywebpush import webpush, WebPushException
import subprocess
import time


app = Flask(__name__)

# Read secrets from the JSON file
with open('secret_key', 'r') as file:
    secrets = json.load(file)

# Initialize Supabase client
supabase_url = secrets['supabase_url']
supabase_key = secrets['supabase_key']
supabase = create_client(supabase_url, supabase_key)
vapid_private_key = secrets['vapid_private_key']

@app.route('/notificationTool/')
def index():
    return render_template('notification_form.html')

@app.route('/notificationTool/subscribers', methods=['GET'])
def get_subscribers():
    result = supabase.table('subscribers').select('id', 'push_token', 'metadata').execute()
    return jsonify(result.data)

@app.route('/notificationTool/send_notification', methods=['POST'])
def send_notification():
    data = request.json
    payload = json.dumps({
        "title": data['title'],
        "body": data['body'],
        "url": data['url']
    })

    for subscriber_id in data['subscribers']:
        try:
            # Fetch subscriber data
            subscriber_result = supabase.table('subscribers').select('push_token').eq('id', subscriber_id).execute()
            subscriber = subscriber_result.data[0]

            push_token_base64 = subscriber['push_token']
            push_token_json = base64.b64decode(push_token_base64).decode('utf-8')
            decoded_token = json.loads(push_token_json)

            webpush(
                subscription_info=decoded_token,
                data=payload,
                vapid_private_key=vapid_private_key,
                vapid_claims={
                    "sub": "mailto:anirudhvsp@gmail.com",
                }
            )
            print(f"Notification sent successfully to subscriber {subscriber_id}")
        except WebPushException as e:
            if e.response.status_code == 410:
                print(f"Subscriber {subscriber_id} has unsubscribed or expired. Deleting from database.")
                supabase.table('subscribers').delete().eq('id', subscriber_id).execute()
            else:
                print(f"Push failed for subscriber {subscriber_id}: {e}")
        except base64.binascii.Error as base64_error:
            print(f"Base64 decode error for subscriber {subscriber_id}: {base64_error}")
        except json.JSONDecodeError as json_error:
            print(f"JSON decode error for subscriber {subscriber_id}: {json_error}")
        except Exception as e:
            print(f"Unexpected error for subscriber {subscriber_id}: {e}")

    return jsonify({"status": "success"})


@app.route("/notificationTool/github-webhook", methods=["POST"])
def webhook():
    data = request.json
    print(data)

    if data["ref"] == "refs/heads/aws_mods":
        # Pull latest changes from the remote aws_mods branch
        repo_dir = "/home/ec2-user/xboxBackup"
        try:
            subprocess.run(["git", "-C", repo_dir, "pull", "origin", "aws_mods"], check=True)
            # Call the restart script
            subprocess.Popen(["/home/ec2-user/xboxBackup/restart_gunicorn.sh"], 
                             start_new_session=True)
            return "OK", 200
        except subprocess.CalledProcessError as e:
            print(f"Error during git pull or restarting Gunicorn: {e}")
            return "Error during update process", 500
    
    return "No action taken", 200
