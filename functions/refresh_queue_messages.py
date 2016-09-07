"""
    This function pulls each message from an SQS queue, replaces it, then
    deletes the original message.
    
    SQS has a maximum retention period for messages, so this is important 
    to avoid the messages expiring unexpectedly.
"""
from __future__ import print_function
import json, hashlib
import boto3, botocore

messages_to_receive_at_once = 10

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    # Get reference to our SQS queue.
    queue = boto3.resource("sqs").Queue(event["queue-url"])
    
    first_message_hash = ""
    queue_replacement_complete = False
    message_replacement_count = 0
    
    while True:
        
        print("Pulling the next {} words from the word list queue ({} processed so far).".format(
            messages_to_receive_at_once,
            message_replacement_count
        ))
        sqs_message_list = queue.receive_messages(
            MaxNumberOfMessages = messages_to_receive_at_once
        )
        
        for each_sqs_message in sqs_message_list:
            each_message_hash = hashlib.md5(each_sqs_message.body).hexdigest()
            
            # Make sure we haven't already finished looping through the queue.
            if first_message_hash == "":
                first_message_hash = each_message_hash
            elif first_message_hash == each_message_hash:
                queue_replacement_complete = True
                break
            
            # Delete the message.
            each_sqs_message.delete()
            
            # Re-send the message.
            queue.send_message(
                MessageBody = each_sqs_message.body
            )
            
            #print("Replaced message: %s" % each_sqs_message.body)
            message_replacement_count += 1
        
        if queue_replacement_complete:
            break
    
    print("Queue replacement complete. {} messages replaced.".format(message_replacement_count))
    