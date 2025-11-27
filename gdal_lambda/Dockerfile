# Lambda + Python 3.11 + GDAL 3.8 + Python bindings
FROM ghcr.io/lambgeo/lambda-gdal:3.8-python3.11

# Lambda expects code in /var/task
WORKDIR /var/task

# Optional: if you have extra Python deps, list them here.
# IMPORTANT: do NOT put GDAL itself in requirements.txt.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Your Lambda code (for now just app.py, later your full backend)
COPY app.py .

# Tell Lambda which handler to call: app.lambda_handler
CMD ["app.lambda_handler"]
