import boto3
import os
import json
import time
from flask import Flask, request, jsonify
import threading
import asyncio

ak_mengjiDyuti = "**********"
sk_mengjiDyuti = "**********"
region_mengjiDyuti = "us-east-1"

S3_BUCKET = "1232833006-in-bucket"
SQS_REQUEST_QUEUE = "1232833006-req-queue"
SQS_RESPONSE_QUEUE = "1232833006-resp-queue"
AWS_REGION = "us-east-1"

iam_client = boto3.Session(aws_access_key_id=ak_mengjiDyuti, aws_secret_access_key=sk_mengjiDyuti) 
s3 = iam_client.client("s3", region_name=AWS_REGION)
sqs = iam_client.client("sqs", region_name=AWS_REGION)

sqs_req_url = sqs.get_queue_url(QueueName=SQS_REQUEST_QUEUE)["QueueUrl"]
sqs_resp_url = sqs.get_queue_url(QueueName=SQS_RESPONSE_QUEUE)["QueueUrl"]

app = Flask(__name__)

request_results = {}


async def upload_to_s3(file_obj, filename):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: s3.upload_fileobj(file_obj, S3_BUCKET, filename))

async def send_req_to_app_tier(filename):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: sqs.send_message(QueueUrl=sqs_req_url, MessageBody=json.dumps({"filename": filename})))

def poll_response_queue():
    while True:
        response = sqs.receive_message(QueueUrl=sqs_resp_url, MaxNumberOfMessages=10, WaitTimeSeconds=2)
        if "Messages" in response:
            for message in response["Messages"]:
                body = json.loads(message["Body"])
                filename = body["filename"]
                result = body["result"]

                request_results[filename] = result

                sqs.delete_message(QueueUrl=sqs_resp_url, ReceiptHandle=message["ReceiptHandle"])
        time.sleep(1)


threading.Thread(target=poll_response_queue, daemon=True).start()


@app.route("/", methods=["POST"])
async def handle_request():
    if "inputFile" not in request.files:
        return "Missing inputFile", 400

    file = request.files["inputFile"]
    filename = file.filename

    await upload_to_s3(file, filename)

    await send_req_to_app_tier(filename)

    start_time = time.time()
    while (filename not in request_results):  
        await asyncio.sleep(1)
    result = request_results.pop(filename)
    return f"{filename}:{result}", 200

    return "Timeout: No response received", 504

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)