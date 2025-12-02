# ---- Build environment (Amazon Linux + GDAL) ----
FROM ghcr.io/lambgeo/lambda-gdal:3.8-python3.11

RUN yum install -y zip && yum clean all

# Lambda root
ENV PACKAGE_PREFIX=/var/task

# Optional GDAL runtime defaults (safe to bake in)
ENV GDAL_DISABLE_READDIR_ON_OPEN=YES
ENV CPL_VSIL_CURL_ALLOWED_EXTENSIONS=.tif,.tiff,.ovr
ENV GDAL_NUM_THREADS=ALL_CPUS
ENV CPL_LOG=/dev/null

# ---- Install Python dependencies into /var/task ----
# Copy requirements
COPY build/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt -t ${PACKAGE_PREFIX}

RUN pip install --no-cache-dir \
    GDAL==$(gdal-config --version) \
    -t ${PACKAGE_PREFIX}

# Copy all runtime code
COPY app/ ${PACKAGE_PREFIX}/app/

# ---- Create ZIP package ----
# 1. Python code + deps
RUN cd ${PACKAGE_PREFIX} && zip -r9 /tmp/package.zip .

# 2. GDAL shared libs + data
RUN cd $PREFIX && \
    zip -r9 --symlinks /tmp/package.zip \
        lib/*.so* \
        share \
        bin/gdal* \
        bin/ogr*

# ---- Output ZIP (for local extraction) ----
CMD ["bash", "-c", "cp /tmp/package.zip /out/package.zip"]
