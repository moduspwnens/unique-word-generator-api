"""
    This function is called by API Gateway to generate a new unique word.
"""
from __future__ import print_function
import json
import boto3, botocore

max_tries = 5

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    # Get reference to our SQS queue.
    queue = boto3.resource("sqs").Queue(event["wordlist-queue-url"])
    
    # Get reference to our used words table.
    used_words_table = boto3.resource("dynamodb").Table(event["used-words-table"])
    
    try_count = 0
    while try_count < max_tries:
        try_count += 1
        
        try:
            return reserve_next_word(queue, used_words_table)
        except Exception as e:
            print("Error: {}".format(e))
    
    raise Exception("Unable to generate unique word.")

def reserve_next_word(queue, used_words_table):
    
    print("Pulling the next word from the word list queue.")
    
    sqs_message_list = queue.receive_messages()
    
    if len(sqs_message_list) == 0:
        raise StopIteration("No words available in queue.")
    
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