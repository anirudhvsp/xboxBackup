import json
import base64
from supabase import create_client
from pywebpush import webpush, WebPushException

# Read secrets from the JSON file
with open('secret_key', 'r') as file:
    secrets = json.load(file)

# Initialize Supabase client
supabase_url = secrets['supabase_url']
supabase_key = secrets['supabase_key']
supabase = create_client(supabase_url, supabase_key)
print(secrets)
vapid_private_key = secrets['vapid_private_key']

def send_notifications():
    result = supabase.table('subscribers').select('id', 'push_token').execute()
    subscribers = result.data
    print(f"Fetched {len(subscribers)} subscribers")

    payload = json.dumps({
        "title": "Testing push notifications",
        "body": "checkout this amazing cycling video",
        "url" : "https://streamitnow.site/stream/20240923_006"
    })

    for index, subscriber in enumerate(subscribers):
        print(f"Processing subscriber {index + 1}")
        print(f"Subscriber data: {subscriber}")
        
        try:
            push_token_base64 = subscriber['push_token']
            print(f"Raw push_token (base64): {push_token_base64}")
            
            # Decode the base64 string
            push_token_json = base64.b64decode(push_token_base64).decode('utf-8')
            print(f"Decoded push_token (JSON string): {push_token_json}")
            
            # Parse the JSON string
            decoded_token = json.loads(push_token_json)
            print(f"Parsed push_token: {decoded_token}")
            
            webpush(
                subscription_info=decoded_token,
                data=payload,
                vapid_private_key=vapid_private_key,
                vapid_claims={
                    "sub": "mailto:anirudhvsp@gmail.com",
                }
            )
            print(f"Notification sent successfully to subscriber {index + 1}")
        except WebPushException as e:
            if e.response.status_code == 410:
                print(f"Subscriber {index + 1} has unsubscribed or expired. Deleting from database.")
                supabase.table('subscribers').delete().eq('id', subscriber['id']).execute()
            else:
                print(f"Push failed for subscriber {index + 1}: {e}")
        except base64.binascii.Error as base64_error:
            print(f"Base64 decode error for subscriber {index + 1}: {base64_error}")
        except json.JSONDecodeError as json_error:
            print(f"JSON decode error for subscriber {index + 1}: {json_error}")
        except Exception as e:
            print(f"Unexpected error for subscriber {index + 1}: {e}")

if __name__ == "__main__":
    send_notifications()
