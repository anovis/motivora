#!/bin/bash

# Prepare data files
node prepare_json_data.js

# Iterate through all data files and upload each
# Ended up having to manually upload each one
for filename in ./data_to_upload/*.json; do
  sleep 1
  echo $filename
  aws dynamodb batch-write-item --request-items "file:/${filename:1}" --region us-east-1 --profile chalice
done
