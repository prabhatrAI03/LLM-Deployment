# Day 8 --- Deploy FastAPI on AWS EC2

**Project:** LLM Deployment\
**Focus:** Deploying an existing FastAPI backend to a cloud virtual
machine and accessing it remotely.

## 1. Objective

Deploy the FastAPI application to AWS EC2, connect it to the vLLM model
server running on Kaggle, and verify that the API can be reached from a
mobile browser.

## 2. Architecture

``` text
Mobile Browser
     |
     | HTTP request to EC2 public IP :3002
     v
AWS Security Group
     |
     v
EC2 instance — FastAPI / Uvicorn (port 3002)
     |
     | Request through the configured Kaggle proxy
     v
Kaggle proxy
     |
     v
vLLM API (port 8000) — Qwen/Qwen2.5-0.5B-Instruct
     |
     | Generated response
     v
FastAPI on EC2
     |
     v
Mobile Browser
```

The mobile browser does not connect directly to the vLLM port. It sends
requests to FastAPI, which calls the model API through the configured
proxy.

## 3. Work completed

-   Launched an AWS EC2 instance running Amazon Linux.
-   Connected to the instance from WSL using SSH and a private `.pem`
    key.
-   Created a project directory and Python virtual environment on EC2.
-   Installed the backend dependencies from `requirements.txt`.
-   Copied the existing FastAPI application to the EC2 instance.
-   Configured the Kaggle proxy through an environment variable.
-   Verified that EC2 could reach the vLLM API and receive a model
    response.
-   Started FastAPI with Uvicorn on port `3002`.
-   Configured an inbound Security Group rule to allow access to the
    FastAPI port.
-   Tested the health endpoint and Swagger UI from a mobile browser
    using the EC2 public IP.

## 4. Running the application on EC2

From the project directory:

``` bash
source venv/bin/activate
python L3_fastAPI.py
```

Keep the process running while testing the API. Stop it with `Ctrl+C`.

## 5. Endpoints used for testing

Replace `<EC2-PUBLIC-IP>` with the current public IP address of the
instance.

-   Health endpoint: `http://<EC2-PUBLIC-IP>:3002/`
-   Swagger UI: `http://<EC2-PUBLIC-IP>:3002/docs`

The API was reachable from a mobile browser using the public IP. The
public DNS hostname initially produced an SSL protocol error, while the
HTTP URL using the public IP worked. This is consistent with a browser
HTTPS-upgrade or hostname-related issue; the application endpoint was
serving plain HTTP.

## 6. Key concepts learned

-   **EC2:** A cloud virtual machine used to host an application.
-   **SSH:** A secure way to access the remote machine's terminal.
-   **Uvicorn:** Runs the FastAPI application and listens for HTTP
    requests.
-   **Port 3002:** The port used by FastAPI on EC2.
-   **`0.0.0.0`:** Tells the server to listen on all available IPv4
    interfaces; it does not independently make the service public.
-   **Security Group:** Controls permitted inbound and outbound network
    traffic for the EC2 instance.
-   **Public IP and DNS:** Ways to address a publicly reachable cloud
    instance.
-   **HTTP and HTTPS:** HTTP is unencrypted; HTTPS uses TLS encryption
    and certificate validation.
-   **Backend and model server:** FastAPI handles the application API,
    while vLLM runs model inference.
-   **Environment variables:** Keep configuration separate from code and
    protect credentials.

## 7. Request-response workflow

1.  The user submits a prompt through the browser.
2.  The browser sends an HTTP request to the EC2 public IP on port
    `3002`.
3.  AWS networking rules allow the request to reach the instance.
4.  Uvicorn receives the request and passes it to FastAPI.
5.  FastAPI validates the request and calls the vLLM API through the
    Kaggle proxy.
6.  vLLM runs the Qwen model and generates a response.
7.  The response returns through the proxy to FastAPI.
8.  FastAPI sends the HTTP response back to the browser.

## 8. Security and operational notes

-   Do not commit `.env` files, private keys, or proxy credentials.
-   Since an `.env` file was previously pushed to Git, treat credentials
    in it as exposed: rotate or regenerate them. Removing the file in a
    later commit does not remove it from earlier Git history.
-   Public access to port `3002` means other people may be able to call
    the API. Use authentication and restrict access when appropriate.
-   Configure HTTPS with a valid TLS certificate before production use.
-   A Kaggle session or proxy can expire, so it is not a reliable
    permanent production model host.
-   Stop the FastAPI process when finished testing. Stop the EC2
    instance when it is no longer needed, while considering any storage
    or other resources that may still incur charges.

## 9. Day 8 outcome

The existing FastAPI backend was deployed to AWS EC2 and tested remotely
from a mobile browser. The deployment connected the cloud-hosted backend
to a vLLM model server running on Kaggle, demonstrating the basic
workflow of a cloud backend calling a separate AI inference service.

## 10. Suggested Git commit

``` text
docs: document AWS EC2 deployment
```
