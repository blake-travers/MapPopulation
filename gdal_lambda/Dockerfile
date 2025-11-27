# Dockerfile
# Lambda + Python 3.11 + GDAL 3.8 C libs
FROM ghcr.io/lambgeo/lambda-gdal:3.8-python3.11

# Lambda expects code in /var/task
WORKDIR /var/task

# 1) Install GDAL Python bindings to match C libs
RUN python3 -m pip install --no-cache-dir "GDAL==$(gdal-config --version)"

# 2) Your extra Python deps (NO GDAL here)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) Lambda code
COPY app.py .
COPY lambda_COG_aggregator.py .

# Lambda handler
CMD ["app.lambda_handler"]



#Build:      docker build -f Dockerfile -t gdal-lambda .
#Run (exits immediately):      docker run -p 9000:8080 gdal-lambda
#Check if worked:       docker ps -a