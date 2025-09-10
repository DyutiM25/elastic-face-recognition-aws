# Elastic Face Recognition Application (CSE 546 Project 1 Part II)

## 📌 Overview
This project implements an **elastic, multi-tiered face recognition application** using AWS IaaS resources. It leverages **EC2, S3, and SQS** to build a scalable cloud system with autoscaling, where requests are dynamically processed by application-tier instances running a deep learning face recognition model.  

The system consists of:
- **Web Tier (`server.py`)** – Handles HTTP requests, stores images in S3, forwards requests to SQS, and returns results.
- **Application Tier (`backend.py`)** – Processes recognition requests using a PyTorch-based deep learning model.
- **Autoscaling Controller (`controller.py`)** – Manages scaling of application-tier instances (up to 15 instances).

---

## ⚙️ Architecture
1. **Web Tier**
   - Receives image upload requests (`inputFile`) via HTTP POST on port **8000**.
   - Stores images in **S3 input bucket** (`<ASU ID>-in-bucket`).
   - Sends requests to **SQS request queue** (`<ASU ID>-req-queue`).
   - Retrieves results from **SQS response queue** (`<ASU ID>-resp-queue`) and returns plain-text output:  
     ```
     <filename>:<prediction>
     ```

2. **Application Tier**
   - Instances launched from a pre-built **AMI** containing PyTorch and model code.
   - Retrieves requests from **SQS**, fetches corresponding images from S3, performs model inference, and stores results in the **S3 output bucket** (`<ASU ID>-out-bucket`).
   - Pushes results to the **response queue**.

3. **Autoscaling**
   - Implemented manually in `controller.py` (not AWS Auto Scaling).
   - Rules:
     - `0` app instances if no requests are pending.
     - Scale up to `15` instances based on demand.
     - Each instance processes **1 request at a time**.
     - Instances stop automatically when idle.

---

## 🛠️ Setup Instructions

### Prerequisites
- AWS account with access to **EC2, S3, SQS** (US-East-1 region).
- Python 3.x
- Required packages:
  ```bash
  pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
  pip3 install boto3 flask
