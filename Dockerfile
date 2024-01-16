# Use the official Python image as the base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .
COPY . .
# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the application files into the container
COPY . .

# Expose the necessary port for the Flask app
EXPOSE 80

# Command to run the application
CMD ["python", "app.py"]