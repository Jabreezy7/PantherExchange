FROM ubuntu:latest

# Install Python and PIP
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    && apt-get clean

# Set the working directory to be /app
WORKDIR /app

# Copy the requirements list over and install 
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy over contents of /backend to /app
COPY . .

CMD ["python3", "app.py"]

