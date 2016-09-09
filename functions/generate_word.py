"""
    This function is called by API Gateway to generate a new unique word.
"""
from __future__ import print_function
import json
import boto3, botocore

max_tries = 5

class CriticalLocalException(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    # Get reference to our used words table.
    used_words_table = boto3.resource("dynamodb").Table(event["used-words-table"])
    
    if "warming" in event and "{}".format(event["warming"]).lower() == "true":
        prewarm_event_received(used_words_table, context.log_stream_name)
        return
    
    # Get reference to our SQS queue.
    queue = boto3.resource("sqs").Queue(event["wordlist-queue-url"])
    
    try_count = 0
    while try_count < max_tries:
        try_count += 1
        
        try:
            return reserve_next_word(queue, used_words_table)
        except CriticalLocalException:
            raise
        except Exception as e:
            print("Error: {}".format(e))
    
    raise_error_for_api_gateway(
        500,
        "InternalError",
        "Unable to generate a unique word after {} tries.".format(max_tries)
    )

def reserve_next_word(queue, used_words_table):
    
    print("Pulling the next word from the word list queue.")
    
    sqs_message_list = queue.receive_messages()
    
    if len(sqs_message_list) == 0:
        raise_error_for_api_gateway(
            500,
            "InternalError",
            "No words available in queue."
        )
    
    sqs_message = sqs_message_list[0]
    
    message_body_object = json.loads(sqs_message.body)
    
    new_word = message_body_object["word"]
    times_returned = message_body_object["count"]
    
    print("Retrieved \"{}\". Previously returned {:d} time(s).".format(new_word, times_returned))
    
    print("Deleting message from the queue.")
    sqs_message.delete()
    
    final_word = None
    
    if times_returned == 1:
        # Return the word as-is, with no numeric increment.
        final_word = new_word
    else:
        # Append a number representing the number of times the word has been returned.
        final_word = "{}{:d}".format(new_word, times_returned)
    
    
    # Ensure word hasn't already been reserved.
    try:
        used_words_table.put_item(
            Item = {
                "PartitionKey": final_word
            },
            ConditionExpression=boto3.dynamodb.conditions.Attr("PartitionKey").not_exists()
        )
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise AttributeError("Word pulled from queue ({}) already taken.".format(final_word))
        else:
            raise
    
    print("Adding new message to queue with incremented count value.")
    queue.send_message(
        MessageBody = json.dumps({
            "word": new_word,
            "count": times_returned + 1
        })
    )
    
    print("Returning word: \"{}\"".format(final_word))
    
    return final_word

def prewarm_event_received(used_words_table, unique_context_id):
    
    # Send a PutItem request for an item unique to this Lambda deployment.
    used_words_table.put_item(
        Item = {
            "PartitionKey": unique_context_id
        }
    )
    
    print("Lambda function and DynamoDB table have been warmed.")

def raise_error_for_api_gateway(status_code, error_type, error_message):
    # Raising the error this way allows for it to be recognized and formatted 
    # by API Gateway to return the correct status code and message.
    
    raise CriticalLocalException(json.dumps({
        "errorType": error_type,
        "httpStatus": status_code,
        "message": error_message
    }, separators=(',', ':')))

