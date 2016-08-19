"""
    initial_configuration.py
    
    This Lambda function is run during the CloudFormation stack creation to 
    load the word lists into DynamoDB.
"""
from __future__ import print_function
import urllib2, json
from random import shuffle
import boto3, botocore

word_list_url_base = "https://raw.githubusercontent.com/moduspwnens/unique-name-generator-api/master/"

word_lists = {
    "adjectives": "{}adjectives.txt".format(word_list_url_base),
    "animals": "{}animals.txt".format(word_list_url_base)
}

def lambda_handler(event, context):
    print(event)
    
    configuration_table_name = event["ResourceProperties"]["ConfigurationTable"]
    
    word_list_config_item = {
        "PartitionKey": "WordLists"
    }
    
    for each_word_list_name in word_lists.keys():
        each_word_list_url = word_lists[each_word_list_name]
        
        each_word_list_string = urllib2.urlopen(each_word_list_url).read()
        each_word_list = each_word_list_string.strip().split("\n")
        shuffle(each_word_list)
        
        word_list_config_item[each_word_list_name] = each_word_list
    
    
    configuration_table = boto3.resource("dynamodb").Table(configuration_table_name)
    
    try:
        response = configuration_table.put_item(
            Item = word_list_config_item,
            ConditionExpression = boto3.dynamodb.conditions.Attr("PartitionKey").not_exists(),
            ReturnConsumedCapacity = "TOTAL"
        )
        
        consumed_capacity_units = response["ConsumedCapacity"]["CapacityUnits"]
    
        print("Consumed {} capacity units.".format(consumed_capacity_units))
        
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print("Word lists already saved.")
        else:
            raise
    
    response_object = {
        "Status": "SUCCESS",
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
    
    return response_object