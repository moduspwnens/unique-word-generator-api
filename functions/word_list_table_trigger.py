"""
    This function receives events from the word list DynamoDB table 
    stream.
"""
from __future__ import print_function
import json
import boto3, botocore

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    for each_record in event["Records"]:
        handle_dynamodb_stream_record(each_record)

def handle_dynamodb_stream_record(record):
    print("Record: {}".format(json.dumps(record)))