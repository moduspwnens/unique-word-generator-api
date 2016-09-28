"""
    This function is run during the CloudFormation stack creation to 
    load the word lists into DynamoDB.
"""
from __future__ import print_function
import urllib2, json, traceback, time
from random import shuffle
import boto3
import cfnresponse

sqs_send_batch_size_max = 10
queue_purge_delay_seconds = 60
max_sqs_tries = 5

def save_word_list(word_list_queue_url, word_list_string, shuffle_word_list):
    
    word_list = word_list_string.strip().split("\n")
    print("Found {:d} words in word list from CloudFormation template.".format(len(word_list)))
    
    if shuffle_word_list:
        print("Shuffling word list.")
        shuffle(word_list)
    else:
        print("Sorting word list.")
        word_list.sort()
    
    print("Word List SQS Queue URL: {}".format(word_list_queue_url))
    
    # Get reference to our SQS queue.
    queue = boto3.resource("sqs").Queue(word_list_queue_url)
    
    # Purge the queue if it already has messages.
    if int(queue.attributes["ApproximateNumberOfMessages"]) > 0:
        print("Queue already contains messages. Purging them.")
        queue.purge()
        time.sleep(queue_purge_delay_seconds)
    
    remaining_words_to_add = word_list
    
    sqs_attempt_count = 0
    while sqs_attempt_count < max_sqs_tries:
        
        # Try to add the words. Keep list of words that failed to add (for whatever reason).
        remaining_words_to_add = add_words_to_queue(queue, remaining_words_to_add)
        
        sqs_attempt_count += 1
    
    if len(remaining_words_to_add) > 0:
        raise Exception("After {:d} attempt(s), {:d} words still not added to queue.".format(max_sqs_tries, len(remaining_words_to_add)))
    
    

def add_words_to_queue(queue, word_list):
    
    # Split the word list into batches to maximize efficiency.
    word_list_batches = []
    
    new_word_list_batch = []
    for i, each_word in enumerate(word_list):
        new_word_list_batch.append(each_word)
        
        if i % sqs_send_batch_size_max == sqs_send_batch_size_max - 1:
            
            # This batch is full. Add it to the list and reset the current batch.
            word_list_batches.append(new_word_list_batch)
            new_word_list_batch = []
    
    # Add last batch (if not empty).
    if len(new_word_list_batch):
        word_list_batches.append(new_word_list_batch)
    
    failed_words = []
    
    # Add the words in each batch to the word list queue.
    for i, each_word_batch in enumerate(word_list_batches):
        
        new_entries_list = []
        
        for j, each_word in enumerate(each_word_batch):
            new_entries_list.append({
                "Id": "{:d}".format(j),
                "MessageBody": json.dumps({
                    "word": each_word,
                    "count": 1
                })
            })
        
        print("Adding word batch {:d}/{:d} to word list queue.".format(i+1, len(word_list_batches)))
        
        response = queue.send_messages(
            Entries = new_entries_list
        )
        
        request_fail_count = 0
        
        for each_record in response.get("Failed", []):
            request_fail_count += 1
            failed_word_index = int(each_record["Id"])
            failed_words.append(each_word_batch[failed_word_index])
    
    # Return words that were unable to be added.
    return failed_words
    

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    cfn_response_type = cfnresponse.SUCCESS
    
    if event["RequestType"] == "Create":
    
        try:
            save_word_list(
                event["ResourceProperties"]["WordListQueueUrl"],
                event["ResourceProperties"]["WordList"],
                "{}".format(event["ResourceProperties"]["ShuffleWordList"]).lower() not in ["no", "false"]
            )
    
        except Exception as e:
            print(traceback.format_exc())
            cfn_response_type = cfnresponse.FAILED
    
    cfnresponse.send(
        event,
        context,
        cfn_response_type,
        {}
    )