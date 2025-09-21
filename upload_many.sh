#!/bin/bash

# Directory containing the files to upload
FILES_DIR="test_files"

# Your API's upload endpoint
UPLOAD_URL="http://localhost:3000/upload/"

# Loop through all files in the directory
for file in "$FILES_DIR"/*
do
  if [ -f "$file" ]; then
    echo "-------------------------------------"
    echo "Uploading $file..."
    curl -X POST \
      -F "file=@$file" \
      "$UPLOAD_URL"
    echo ""
    echo "Upload command sent for $file."
    # Optional: wait for 1 second between uploads
    sleep 1
  fi
done

echo "-------------------------------------"
echo "All files have been sent for upload."