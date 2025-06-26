import boto3
import time

ak_mengjiDyuti = "**********"
sk_mengjiDyuti = "**********"
region_mengjiDyuti = "us-east-1"

# AWS Configuration
REGION = "us-east-1"
MAX_INSTANCES = 15
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/043309345838/1232833006-req-queue"  

# Initialize AWS Clients
session = boto3.Session(aws_access_key_id=ak_mengjiDyuti, aws_secret_access_key=sk_mengjiDyuti)
ec2 = session.client('ec2', region_name=REGION)
sqs = session.client('sqs', region_name=REGION)

# Function to get the number of pending messages in the request queue
def get_queue_size():
    response = sqs.get_queue_attributes(
        QueueUrl=QUEUE_URL, AttributeNames=['ApproximateNumberOfMessages']
    )
    return int(response['Attributes'].get('ApproximateNumberOfMessages', 0))

# Function to get the list of running application tier instances
def get_running_instances():
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']},
            {'Name': 'tag:Name', 'Values': ['app-tier-instance*']}
        ]
    )
    return [i['InstanceId'] for r in response['Reservations'] for i in r['Instances']]

# Function to get the list of stopped instances that can be started
def get_stopped_instances():
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['stopped']},
            {'Name': 'tag:Name', 'Values': ['app-tier-instance*']}
        ]
    )
    return [i['InstanceId'] for r in response['Reservations'] for i in r['Instances']]

# Function to start stopped instances
def start_instances(instance_ids):
    if instance_ids:
        ec2.start_instances(InstanceIds=instance_ids)
        print(f"Started instances: {instance_ids}")

# Function to stop running instances
def stop_instances(instance_ids):
    if instance_ids:
        ec2.stop_instances(InstanceIds=instance_ids)
        print(f"Stopped instances: {instance_ids}")


# Autoscaling function
# def autoscale():
#     while True:
#         queue_size = get_queue_size()
#         running_instances = get_running_instances()
#         stopped_instances = get_stopped_instances()
#         num_running = len(running_instances)

#         print(f"Queue Size: {queue_size}, Running Instances: {num_running}")

#         if queue_size == 0 and num_running > 0:
#             print("No pending requests. Stopping all running instances immediately.")
#             stop_instances(running_instances)

#             # Wait up to 5 seconds for instances to stop
#             start_time = time.time()
#             while time.time() - start_time < 5:
#                 running_instances = get_running_instances()
#                 if not running_instances:
#                     print("All instances successfully stopped.")
#                     break
#                 time.sleep(1)  # Check every second

#         elif queue_size > 0:
#             needed_instances = min(queue_size, MAX_INSTANCES) - num_running
#             if needed_instances > 0:
#                 instances_to_start = stopped_instances[:needed_instances]
#                 start_instances(instances_to_start)

#         time.sleep(2)  # Reduced sleep time for faster reaction

# if __name__ == "__main__":
#     autoscale()

def autoscale():
    count = 0  # Initialize outside the loop to track consecutive zeroes

    while True:
        queue_size = get_queue_size()
        running_instances = get_running_instances()
        stopped_instances = get_stopped_instances()
        num_running = len(running_instances)

        print(f"Queue Size: {queue_size}, Running: {num_running}, Stopped: {len(stopped_instances)}")

        # Scale-Out: Start stopped instances if there are pending requests
        if queue_size > 0:
            needed_instances = min(queue_size, MAX_INSTANCES) - num_running
            instances_to_start = stopped_instances[:needed_instances]
            start_instances(instances_to_start)
            count = 0  # Reset count when queue_size is not zero
        
        # Scale-In: Stop instances only if there are at least 3 continuous 0s in queue_size
        elif queue_size == 0 and num_running > 0:
            count += 1  # Increment count when queue_size is 0
            if count >= 3:  # Stop instances only after 3 continuous occurrences
                stop_instances(running_instances)
        else:
            count = 0  # Reset count if queue_size is not 0

        time.sleep(1.5)  # Adjust sleep time for balanced autoscaling

if __name__ == "__main__":
    autoscale()
