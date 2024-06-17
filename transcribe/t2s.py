import os
import requests
from dotenv import load_dotenv
import boto3
import uuid
import tempfile
import botocore
load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = 'neoworld-stage-neomi-chatbot-audio-chats'

unique_uuid = str(uuid.uuid4())
def delete_local_files(folder_path):
    try:
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                # Check if the file name ends with ".MD"; if so, skip deletion
                if file_name.endswith('.MD'):
                    print(f"Skipped deletion of {file_name} file: {file_path}")
                else:
                    os.remove(file_path)
                    print(f"Local file deleted: {file_path}")
            else:
                print(f"Skipped deletion of non-file: {file_path}")
    except Exception as e:
        print(f"Error deleting local files: {e}")

def generate_audio(input_text):
    api_key = os.getenv("OPENAI_API_KEY")
    url = "https://api.openai.com/v1/audio/speech"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "tts-1",
        "voice": "nova",
        "input": input_text,
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Error: {response.status_code}\n{response.text}")
        return None
def upload_audio_to_s3(bucket_name, audio_data):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    try:
        # Use a temporary file to store the audio data
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
    
        object_name = f"answer_{unique_uuid}.mp3"
        # Upload the file to S3 with the provided object_name
        s3.upload_file(temp_file_path, bucket_name, object_name)
        # After successful upload of audio to S3, delete the temporary file
        os.remove(temp_file_path)
        return object_name
    except botocore.exceptions.ClientError as e:
        print(f"Error uploading file to S3: {e}")
        return None
def generate_presigned_url(bucket_name, object_name, expiration_time=5400):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name='ap-south-1')

    try:
        
        url = s3.generate_presigned_url(      #get object acess gives permission to download the audio file.
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_name},
            ExpiresIn=expiration_time
        )
        return url
    except botocore.exceptions.ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return None
def download_audio(url, output_folder, filename=None):
    response = requests.get(url)
    if response.status_code == 200:
        if not filename:
            filename = unique_uuid + ".mp3"
        output_path = os.path.join(output_folder, filename)

        with open(output_path, 'wb') as audio_file:
            audio_file.write(response.content)
            print(f"Audio file downloaded successfully as '{output_path}'")

        return output_path
    else:
        print(f"Failed to download audio file. Status code: {response.status_code}")
        return None
def delete_local_files(folder_path):
    try:
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Local file deleted: {file_path}")
            else:
                print(f"Skipped deletion of non-file: {file_path}")
    except Exception as e:
        print(f"Error deleting local files: {e}")