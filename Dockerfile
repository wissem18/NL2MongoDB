# Use the official Python image as the base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port Streamlit runs on (default: 8501)
EXPOSE 8501

# Set the command to run the Streamlit app
CMD ["streamlit", "run", "nl2mongo/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
