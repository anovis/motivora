#!/bin/bash

# Prepare data files
rm -rf data_to_upload
mkdir data_to_upload
node --max-old-space-size=4096 prepare_json_data.js

# Iterate through all data files and upload each
# This loop ended up not working because AWS errored on some of the uploads.
# Ended up just manually running the command for reach json file. Feel free
# to try and get this loop running in the future if need be.
# EXAMPLE: aws dynamodb batch-write-item --request-items "file://data-11.json" --region us-east-1 --profile chalice

for filename in ./data_to_upload/*.json; do
  sleep 1
  echo $filename
  aws dynamodb batch-write-item --request-items "file:/${filename:1}" --region us-east-1 --profile chalice
done
