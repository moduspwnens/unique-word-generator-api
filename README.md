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

Not yet implemented. When ready, the steps will be:
* [Sign up for an AWS account](https://aws.amazon.com/console/) (if you don't already have one).
* [Log in to your AWS account](https://aws.amazon.com/console/).
* Click the "Launch Stack" button above (not yet implemented).
* On the **Select Template** page, you should already see "Specify an Amazon S3 template URL" selected. Click **Next**.
* On the **Specify Details** page, enter a name for the stack. It's not utilized internally, so whatever you'd like. Perhaps *unique-name-api1*. Click **Next**.
* On the **Options** page, just click **Next**.
* On the **Review** page, under **Capabilities**, check the box acknowledging that IAM roles will be created. They're used by the Lambda functions. Click **Create**.
* The API is now being created. After a few minutes, the stack's status on the [CloudFormation home page](https://console.aws.amazon.com/cloudformation/home) should change to **CREATE_COMPLETE**. Select it, then choose the **Outputs** tab.
* You should see an output with a key of **NameGeneratorApiEndPoint** and a value with the URL of your name generator API endpoint. Click the URL.
* Congratulations! You've successfully generated your first unique name. You won't see that one again.

This will consist of clicking a "Launch Stack" button.

## Design goals

I partially decided to do this as an exercise with AWS services, but also had these goals in mind.

* API should use a *serverless* infrastructure
  * No operating system maintenance, patching, firewall management
* No fixed costs
  * Utilizes only AWS services that fit entirely within the free tier perpetually when idle
* IAM permissions should be as restrictive as possible while allowing necessary functionality
* Design should follow AWS best design practices when possible
* Per-usage costs minimized
* Deployable entirely from a **single CloudFormation template**
* Absolutely no possibility of duplicate names despite concurrent requests
* API should return appropriate status codes
* API should be reasonably fast (<500 ms)
* API should allow easy curling of resulting name from a shell script

The result is an API that:

* Can be deployed trivially
* Requires no maintenance
* Costs nothing to have
* Costs fractions of pennies to use
* Works reliably

## Costs

Note that all prices were last updated at the time of writing: 2016-08-23.

**AWS Lambda**  
Each REST API invocation results in one Lambda function invocation. This will fit into the perpetual AWS free tier for Lambda, but if you've already used yours for other projects, this will cost you around $0.00000104 per invocation (500ms with 128MB memory).

**AWS DynamoDB**  
DynamoDB charges for provisioned throughput and data stored. The data stored by this API will be far less than 1GB, and the API uses two DynamoDB tables, each with just one Read Capacity Unit and one Write Capacity Unit. Both of these are within the perpetual AWS free tier limits, but if you've already used yours for other projects, you're looking at a cost of about $0.00156 per month for the provisioned throughput and less than a penny for the stored data.

**AWS CloudFormation**  
CloudFormation has no costs of its own.

**AWS API Gateway**  
The pricing for API Gateway is (at the time of writing) $3.50 per million requests. That's $0.0000035 per request. It also charges $0.09/GB (for the first 10TB) for data out, and each response is estimated to be around 16 bytes. There is no free tier or static cost for API Gateway.

## FAQ

**Can I use my own domain for the API?**  
Absolutely! See Amazon's documentation [here](http://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-custom-domains.html).

**Can I launch more than one API in the same AWS account?**  
Yes. It uses no unique account-specific resources. Just choose a different stack name when you deploy next time.

**How scalable is it?**  
Not particularly. The algorithm it's using basically consists of:

1. Determine the index of the next item in the list by counting the number of reserved names.
2. Try to reserve the next name in the list.
3. If failed due to it already being reserved, increment the index and go to step 2.

As a result, it'll work fine for small numbers of concurrent requests and will never return duplicate names, but with a large number of requests, many of them will time out.

The default word list doesn't provide enough entropy to be able to reliably result in a random name being unique, so this is the best algorithm I could come up with quickly. It fits my use case, but let me know (or submit a pull request) if you think of something better.

