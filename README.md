# Unique Name Generator API

A serverless API for generating a guaranteed unique word from a preset word list.

## Why?

It's useful for easily getting a unique name for something where the name itself isn't really important--only that it's unique. The default word list consists of animal names.

A common use case would be for disposable servers or deployments. **Without** an API like this, you might use:

* webserver1
* webserver2
* webserver3

Or (if you don't necessarily have an index counter):

* webserver-201608232045
* webserver-201608232145
* webserver-201608232245

Using this API, you can now have:
* webserver-flamingo
* webserver-arcticfox
* webserver-chimpanzee

Now your cluster of webservers has names that are unique, easy to remember, and easy to spell.

## Demo

There's no graphical user interface implemented, but I've deployed an API here:
* https://animals.bennlinger.com/v1/generate-name

Open it in your browser (or curl it from bash) for a unique animal. Try again. Another animal! You'll always get a unique animal (or an animal with a unique counter after it runs out of animals--e.g. kangaroo5).

## How to use

Click this button and follow the prompts to launch the stack.

[![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home#/stacks/new?stackName=unique-name-generator1&templateURL=https://s3.amazonaws.com/bennlinger-public-site/unique-name-generator-api/unique-name-api.json)

After the stack's status changes to CREATE_COMPLETE, select it and then click the Outputs tab. There's just one, and its value is the URL for your API. You can open this in a web browser or curl the result directly into your bash script like this:

```
#!/bin/bash
$ export NEW_ANIMAL=$(curl -s https://your-api-url-here)
$ echo "$NEW_ANIMAL"
```

## Design goals

I partially decided to do this as an exercise with AWS services, but also had these goals in mind.

* API should use a *serverless* infrastructure
  * No operating system maintenance, patching, firewall management
* API should have no strict scaling limits
  * Ideally, the limits should be whatever is the maximum the supporting services allow
* Minimal fixed costs
  * Utilizes only AWS services that fit entirely within the free tier perpetually when idle
* IAM permissions should be as restrictive as possible while allowing necessary functionality
* Design should follow AWS best practices when possible
* Per-usage costs minimized
* Deployable entirely from a **single CloudFormation template**
* Absolutely no possibility of duplicate names despite concurrent requests
* API should return appropriate status codes
* API should be reasonably fast (<500 ms on average)
* API should allow easy curling of resulting name from a shell script

The result is an API that:

* Can be deployed trivially
* Requires no maintenance
* Costs nothing to have
* Costs fractions of pennies to use
* Works reliably
* Scales (nearly) indefinitely

## Costs

Note that all prices were last updated at the time of writing: 2016-08-24.

### Initial Setup

Prices represent the cost of deploying the API via the CloudFormation template.

| Service / Operation                                  | Cost          | Free Tier Eligible            |
|------------------------------------------------------|---------------|-------------------------------|
| AWS Simple Queue Service                             | $0.0000875    | Yes - No expiration           |
| AWS Lambda                                           | $0.0001667    | Yes - No expiration           |
| AWS API Gateway                                      | $0.000175     | Yes - Expires after 12 months |
| **Total Per Deployment** (if free tier already used) | **$0.0004292**|                               |

Yes, it will cost less than a penny to deploy if your free tier allowance is already consumed. Otherwise, there are no costs.

### Operation

Now let's break down the per-request costs.

| Service / Operation                               | Cost             | Free Tier Eligible            |
|---------------------------------------------------|------------------|-------------------------------|
| AWS Simple Queue Service (3 requests)             | $0.0000015       | Yes - No expiration           |
| AWS Lambda (320MB / 400ms)                        | $0.000002084     | Yes - No expiration           |
| AWS API Gateway - Request                         | $0.0000035       | Yes - Expires after 12 months |
| AWS API Gateway - Data Out                        | $0.0000000495    | No                            |
| **Total Per Request** (if free tier already used) | **$0.0000071335**|                               |

That comes out to a little over 140,000 API requests before you owe your first dollar, assuming your free tier allowance was already used up.

### Monthly Static Costs

Note that your first 25 read and write capacity units are free each month.

| Service / Operation                                                | Cost             | Free Tier Eligible            |
|--------------------------------------------------------------------|------------------|-------------------------------|
| Amazon DynamoDB - Write Capacity Month (1)                         | $0.468           | Yes - No expiration           |
| Amazon DynamoDB - Read Capacity Month (1)                          | $0.0936          | Yes - No expiration           |
| **Total Per Request/Second Per Month** (if free tier already used) | **$0.5616**      |                               |

This represents the minimum / default throughput setting - 1 read/write per second. Each API request requires one of each and DynamoDB's perpetual free tier allows 25 of each. For every request per second you want the API to support beyond the free tier, the cost is $0.5616 per request per second if provisioned for the entire month.

## Known Issues

**API doesn't return appropriate error codes / messages.**  
Not yet implemented.

**No automated build method for rebuilding CloudFormation values from source scripts / values.**  
Not yet implemented.

## FAQ

**Can I use my own domain for the API?**  
Absolutely! See Amazon's documentation [here](http://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-custom-domains.html).

**What happens when it runs out of names?**  
It starts over and adds a counter after, so instead of "wallaby", you'd receive "wallaby2".

**What happens if I exceed the provisioned max requests per second I choose?**  
Requests will return more slowly, or return an error if they get too slow. This is based on DynamoDB's throttling behavior and the Python AWS SDK (boto3)'s retry behavior.

**If I choose not to shuffle the list, will I get the names in order?**  
Only approximately. This uses Amazon SQS on the backend so this is explained in the [FAQ](https://aws.amazon.com/sqs/faqs/) regarding first-in first-out (FIFO) of messages.

**Can I launch more than one API in the same AWS account?**  
Yes. It uses no unique account-specific resources. Just choose a different stack name when you deploy next time.

**How scalable is it?**  
It scales pretty well. The only limiting factor is the provisioned capacity for DynamoDB, but you can scale that up and down as necessary. Each of the services tend to have limits, too, so if you push it, you'll end up hitting the service limits of your AWS account. Those can usually be raised just by asking them.

## Roadmap

* Fix known issues
* Add basic web-based front end that shows usage examples
* Support multiple "unique namespaces" from a single API

## Contact

You can contact me at benn@linger.com.
