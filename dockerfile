# Use official Python image as base
FROM python:latest

# Set the working directory
WORKDIR /code

# Copy the requirements file to the container
COPY requirements.txt /code/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the application code to the container
COPY . /code/app

# Command to run the FastAPI app
CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port", "8000"]