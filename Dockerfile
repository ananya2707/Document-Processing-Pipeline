# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install netcat, which is used by our wait script
#RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y netcat-openbsd dos2unix && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /code

# Copy your application code into a subdirectory named 'app'
COPY ./app ./app

# Copy the requirements file first to leverage Docker build caching
COPY ./requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the wait script into the container
COPY ./wait-for-it.sh /wait-for-it.sh

# Copy the start script into the container
COPY ./start-api.sh /start-api.sh

# Fix line endings and make the scripts executable
RUN chmod +x /start-api.sh && dos2unix /wait-for-it.sh && chmod +x /wait-for-it.sh
# The command to run the app will be provided by docker-compose