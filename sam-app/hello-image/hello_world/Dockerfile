FROM ghcr.io/lambgeo/lambda-gdal:3.8-python3.11

ENV GDAL_DISABLE_READDIR_ON_OPEN=YES
ENV CPL_VSIL_CURL_ALLOWED_EXTENSIONS=.tif,.tiff,.ovr
ENV GDAL_NUM_THREADS=ALL_CPUS
ENV CPL_LOG=/dev/null

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py /var/task/app.py

CMD ["app.lambda_handler"]



#Delete Stack:

    #aws cloudformation delete-stack \
    #  --stack-name hello-image \
    #  --region ap-southeast-4

    #aws cloudformation wait stack-delete-complete \
    #  --stack-name hello-image \
    #  --region ap-southeast-4


#Build Docker:

    # sam build

#Deploy Docker:

    # sam deploy
