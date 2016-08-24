"""
    initial_configuration.py
    
    This Lambda function is run during the CloudFormation stack creation to 
    load the word lists into DynamoDB.
"""
from __future__ import print_function
import urllib2, json, traceback
from random import shuffle
import boto3, botocore

def save_wordlist(configuration_table_name, word_list_string):
    
    word_list_config_item = {
        "WordListName": "Default"
    }
    
    word_list = word_list_string.strip().split("\n")
    print("Found {:d} words in word list from CloudFormation template.".format(len(word_list)))
    shuffle(word_list)
    
    word_list_config_item["List"] = word_list
    
    
    configuration_table = boto3.resource("dynamodb").Table(configuration_table_name)
    
    try:
        response = configuration_table.put_item(
            Item = word_list_config_item,
            ConditionExpression = boto3.dynamodb.conditions.Attr("WordListName").not_exists(),
            ReturnConsumedCapacity = "TOTAL"
        )
        
        consumed_capacity_units = response["ConsumedCapacity"]["CapacityUnits"]
    
        print("Consumed {} write capacity units.".format(consumed_capacity_units))
        
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print("Word list already saved.")
        else:
            raise
    
    

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    status_string = "SUCCESS"
    
    if event["RequestType"] == "Create":
    
        try:
            save_wordlist(
                event["ResourceProperties"]["ConfigurationTable"],
                event["ResourceProperties"]["WordList"]
            )
            wordlist_saved = True
    
        except Exception as e:
            print(traceback.format_exc())
            status_string = "FAILED"
    
    response_object = {
        "Status": status_string,
        "Reason": "See the details in CloudWatch Log Stream: " + context.log_stream_name,
        "PhysicalResourceId": context.log_stream_name,
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "Data": {}
    }
    
    print("Response: {}".format(json.dumps(response_object)))
    
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    request = urllib2.Request(event["ResponseURL"], data=json.dumps(response_object))
    request.add_header("Content-Type", "")
    request.get_method = lambda: "PUT"
    opener.open(request)
    
    return {}