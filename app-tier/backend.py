import boto3
import json
import torch
import time
import subprocess
from torchvision import transforms
from PIL import Image
import os

from face_recognition import face_match

ak_mengjiDyuti = "**********"
sk_mengjiDyuti = "**********"
region_mengjiDyuti = "us-east-1"

# Configuration
S3_INPUT_BUCKET = "1232833006-in-bucket"
S3_OUTPUT_BUCKET = "1232833006-out-bucket"
SQS_REQUEST_QUEUE = "1232833006-req-queue"
SQS_RESPONSE_QUEUE = "1232833006-resp-queue"
AWS_REGION = "us-east-1"

# AWS Clients
iam_client = boto3.Session(aws_access_key_id=ak_mengjiDyuti, aws_secret_access_key=sk_mengjiDyuti) 
s3 = iam_client.client("s3", region_name=AWS_REGION)
sqs = iam_client.client("sqs", region_name=AWS_REGION)

# Get SQS queue URLs
sqs_req_url = sqs.get_queue_url(QueueName=SQS_REQUEST_QUEUE)["QueueUrl"]
sqs_resp_url = sqs.get_queue_url(QueueName=SQS_RESPONSE_QUEUE)["QueueUrl"]

# Temporary directory to store downloaded images
TMP_FOLDER = "/tmp"


def process_request():
    """
    Fetches requests from SQS, downloads images from S3, runs face recognition,
    stores results in S3, and sends responses back to SQS.
    """
    while True:
        # Receive a message from the request queue
        response = sqs.receive_message(QueueUrl=sqs_req_url, MaxNumberOfMessages=1, WaitTimeSeconds=10)

        if "Messages" not in response:
            time.sleep(2)  # Sleep if no messages found
            continue

        for message in response["Messages"]:
            body = json.loads(message["Body"])
            filename = body["filename"]
            print("Processing: ", filename)

            try:
                # Download the image from S3
                local_image_path = os.path.join(TMP_FOLDER, filename)
                s3.download_file(S3_INPUT_BUCKET, filename, local_image_path)

                # Run face recognition
                recognition_result = face_match(local_image_path, "data.pt")[0]

                # Store the result in S3 output bucket
                s3.put_object(Bucket=S3_OUTPUT_BUCKET, Key=filename, Body=recognition_result)

                # Send the result to the response queue
                sqs.send_message(QueueUrl=sqs_resp_url, MessageBody=json.dumps({"filename": filename, "result": recognition_result}))

            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

            # Delete processed message from SQS
            sqs.delete_message(QueueUrl=sqs_req_url, ReceiptHandle=message["ReceiptHandle"])

if __name__ == "__main__":
    print("Backend worker started, waiting for requests...")
    process_request()