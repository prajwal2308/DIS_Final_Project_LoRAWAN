# Use small Python base image
FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1


# Set working directory inside the container
WORKDIR /app

# Copy your node script into the container
COPY node.py .

# Run the script
#CMD ["python", "node.py"]
CMD ["python", "-u", "node.py"]
