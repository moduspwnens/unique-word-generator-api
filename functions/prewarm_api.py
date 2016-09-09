"""
    This function pre-warms the API by making calls to keep the various
    resources (Lambda function, DynamoDB, API Gateway) ready even if 
    it hasn't received any requests in a while.
"""
from __future__ import print_function
import json, urllib2

def lambda_handler(event, context):
    print("Event: {}".format(json.dumps(event)))
    
    
    api_url_base = event["api-url-base"]
    
    urls_to_request = []
    
    # Request the home page.
    urls_to_request.append("{}/".format(api_url_base))
    
    # Request the primary "word generator" function.
    urls_to_request.append("{}/{}?warming=true".format(
        api_url_base,
        event["generate-word-path-part"]
    ))
    
    for each_url in urls_to_request:
        print("Requesting {}".format(each_url))
        r = urllib2.urlopen(each_url)
        print("Received status code: {}. Response length: {}".format(
            r.getcode(),
            len(r.read())
        ))
    