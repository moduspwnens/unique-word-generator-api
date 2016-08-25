"""
    This function is called by API Gateway to generate a new unique word.
"""
from __future__ import print_function
import json
import boto3

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    # Get reference to our SQS queue.
    queue = boto3.resource("sqs").Queue(event["wordlist-queue-url"])
    
    print("Pulling the next word from the word list queue.")
    
    sqs_message_list = queue.receive_messages()
    
    if len(sqs_message_list) == 0:
        raise Exception("No words available in queue.")
    
    sqs_message = sqs_message_list[0]
    
    message_body_object = json.loads(sqs_message.body)
    
    new_word = message_body_object["word"]
    times_returned = message_body_object["count"]
    
    print("Retrieved \"{}\". Previously returned {:d} time(s).".format(new_word, times_returned))
    
    print("Deleting message from the queue.")
    sqs_message.delete()
    
    print("Adding new message to queue with incremented count value.")
    queue.send_message(
        MessageBody = json.dumps({
            "word": new_word,
            "count": times_returned + 1
        })
    )
    
    final_word = None
    
    if times_returned == 1:
        # Return the word as-is, with no numeric increment.
        final_word = new_word
    else:
        # Append a number representing the number of times the word has been returned.
        final_word = "{}{:d}".format(new_word, times_returned)
    
    print("Returning word: \"{}\"".format(final_word))
    
    return final_word