FROM osgeo/gdal:ubuntu-full-3.8.0

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip

WORKDIR /app

# Copy backend files
COPY . .

# Install Python dependencies
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
