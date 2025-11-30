FROM ghcr.io/lambgeo/lambda-gdal:3.8-python3.11

ENV GDAL_DATA=/opt/share/gdal
ENV PROJ_LIB=/opt/share/proj

COPY app.py ./

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
