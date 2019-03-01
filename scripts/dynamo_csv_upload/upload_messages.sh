#!/bin/bash

node prepare_json_data.js
aws dynamodb batch-write-item --request-items file://data.json --region us-east-1 --profile chalice
