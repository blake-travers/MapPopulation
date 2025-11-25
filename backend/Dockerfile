FROM osgeo/gdal:ubuntu-full-latest

# Install Python3 + pip
RUN apt-get update && apt-get install -y python3 python3-pip

WORKDIR /app

COPY . .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
