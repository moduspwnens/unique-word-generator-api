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

## How to use

Click the "Launch Stack" button here (not yet implemented).

## Design goals

I partially decided to do this as an exercise with AWS services, but also had these goals in mind.

* API should use a *serverless* infrastructure
  * No operating system maintenance, patching, firewall management
* API should have no strict scaling limits
  * Ideally, the limits should be whatever is the maximum the supporting services allow.
* No fixed costs
  * Utilizes only AWS services that fit entirely within the free tier perpetually when idle
* IAM permissions should be as restrictive as possible while allowing necessary functionality
* Design should follow AWS best design practices when possible
* Per-usage costs minimized
* Deployable entirely from a **single CloudFormation template**
* Absolutely no possibility of duplicate names despite concurrent requests
* API should return appropriate status codes
* API should be reasonably fast (<400 ms on average)
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

| Service / Operation      | Cost          | Free Tier Eligible            |
|--------------------------|---------------|-------------------------------|
| AWS Simple Queue Service | $0.0000875    | Yes - No expiration           |
| AWS Lambda               | $0.0001667    | Yes - No expiration           |
| AWS API Gateway          | $0.000175     | Yes - Expires after 12 months |
| **TOTAL**                | **$0.0004292**|                               |

Yes, it will cost less than a penny to deploy if your free tier allowance is already consumed. Otherwise, there are no costs.

### Operation

Now let's break down the per-request costs.

| Service / Operation        | Cost             | Free Tier Eligible            |
|----------------------------|------------------|-------------------------------|
| AWS Simple Queue Service   | $0.0000015       | Yes - No expiration           |
| AWS Lambda                 | $0.000002084     | Yes - No expiration           |
| AWS API Gateway - Requests | $0.0000035       | Yes - Expires after 12 months |
| AWS API Gateway - Data Out | $0.0000000495    | No                            |
| **TOTAL**                  | **$0.0000071335**|                               |

That comes out to a little over 140,000 API requests before you owe your first dollar, assuming your free tier allowance was already used up.

### Monthly Static Costs

There are no static costs.

## Known Issues

**SQS doesn't guarantee a message is delivered only once.**  
This means by relying on SQS completely, it's possible a name might be returned more than once.

## FAQ

**Can I use my own domain for the API?**  
Absolutely! See Amazon's documentation [here](http://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-custom-domains.html).

**What happens when it runs out of names?**  
It starts over and adds a counter after, so instead of "wallaby", you'd receive "wallaby2".

**If I choose not to shuffle the list, will I get the names in order?**  
Only approximately. This uses Amazon SQS on the backend so this is explained in the [FAQ](https://aws.amazon.com/sqs/faqs/) regarding first-in first-out (FIFO) of messages.

**Can I launch more than one API in the same AWS account?**  
Yes. It uses no unique account-specific resources. Just choose a different stack name when you deploy next time.

**How scalable is it?**  
It scales pretty well.

