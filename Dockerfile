# Dockerfile

# 1. Use an official Python 3.13 runtime as a parent image
FROM python:3.13-slim

# 2. Set the working directory in the container
WORKDIR /app

# 3. Copy the requirements file into the container at /app
COPY requirements.txt .

# 4. Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application's code into the container at /app
COPY . .

# 6. Create a directory for the persistent data
RUN mkdir /app/data

# 7. Tell Docker that the container listens on port 8501
EXPOSE 8501

# 8. Define the command to run your app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]