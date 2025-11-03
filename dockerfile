# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install OS-level deps
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose backend (Flask) and frontend (Streamlit) ports
EXPOSE 5000 8501

# Run both backend and frontend
CMD bash -c "python app.py & streamlit run frontend.py --server.port 8501 --server.address 0.0.0.0"
