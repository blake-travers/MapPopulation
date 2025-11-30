#Amazonlinux Docker images and AWS Lambda layers with GDAL
FROM ghcr.io/lambgeo/lambda-gdal:3.8-python3.11

COPY backend /var/task/backend

CMD ["backend.gdal_lambda.app.lambda_handler"]
