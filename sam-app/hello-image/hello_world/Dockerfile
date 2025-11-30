FROM ghcr.io/lambgeo/lambda-gdal:3.8-python3.11

#COPY requirements.txt ./
#RUN python3.11 -m pip install -r requirements.txt -t .

ENV GDAL_DATA=/opt/share/gdal
ENV PROJ_LIB=/opt/share/proj

COPY app.py ./

# Command can be overwritten by providing a different command in the template directly.
CMD ["app.lambda_handler"]
