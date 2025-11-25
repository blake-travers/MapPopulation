FROM osgeo/gdal:ubuntu-full-3.7.1

# Install Python3 + pip
RUN apt-get update && apt-get install -y python3 python3-pip

# Set working directory
WORKDIR /app

# Copy backend code
COPY . .

# Upgrade pip to avoid old package issues
RUN pip3 install --upgrade pip

# Install Python dependencies
RUN pip3 install -r requirements.txt

EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
