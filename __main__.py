# Option 1: Serverless Application 
import pulumi
import pulumi_aws as aws
import json

# (1) Provision an S3 bucket
s3_bucket = aws.s3.Bucket('pulumi-homework-bucket')

# (2) Provision a DyanmoDB Table
dynamodb_table = aws.dynamodb.Table("pulumi-homework-table",
    name="pulumi-homework-table",
    billing_mode="PAY_PER_REQUEST",
    hash_key = "timestamp",
    attributes=[
        aws.dynamodb.TableAttributeArgs(
            name='timestamp',
            type='S',
        ),
    ],
)

# (4) This lambda role allows my lambda function to access S3 as read only and read/write access to DynamoDB
lambda_role = aws.iam.Role("pulumi-homework-lambda-role", 
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com",
            },
        }],
    }),
    managed_policy_arns=[aws.iam.ManagedPolicy.AWS_LAMBDA_BASIC_EXECUTION_ROLE]
)

# s3_policy = aws.iam.Policy("s3-policy",
#     policy=json.dumps({
#         "Version": "2012-10-17",
#         "Statement": [{
#             "Effect": "Allow",
#             "Action": "s3:GetObject",
#             "Resource": [f"{s3_bucket.arn}/*"]
#         }]
#     })    
# )

# (4a) S3 Read Only Access
lambda_s3_access = aws.iam.RolePolicyAttachment("lambda-s3-access",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
)

# (4b) S3 Read Only Access
lambda_dynamodb_access = aws.iam.RolePolicyAttachment("lambda-dynamodb-access",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
)

# aws.iam.RolePolicyAttachment("lambda-s3-get-object",
#     role=lambda_role.name,
#     policy_arn=s3_policy.arn
# )

# (3) Provision a Lambda Function
# When an object is uploaded to S3, the lambda function sees that a new object was created and writes 
# the object key and the timestamp to the DynamoDB table
lambda_function = aws.lambda_.Function("pulumi-homework-lambda-function",
    runtime="python3.9",
    handler="lambda_handler.lambda_handler",
    role=lambda_role.arn,
    code=pulumi.AssetArchive({'.': pulumi.FileArchive('handler')}),
    environment={
        'variables':{
            'DYNAMO_TABLE_NAME': dynamodb_table.name
        }
    },
    timeout=10,
    opts=pulumi.ResourceOptions(depends_on=[lambda_s3_access, lambda_dynamodb_access])
)

# (6) Configuring lambda to have permission to invoke itself based on the S3 bucket notification
lambda_permission = aws.lambda_.Permission("lambda-permission",
    action="lambda:InvokeFunction",
    function=lambda_function.name,
    principal="s3.amazonaws.com",
    source_arn=s3_bucket.arn
)

# (5) Created an S3 bucket notification which is attached to my lambda function provisioned above.
s3_bucket_notification = aws.s3.BucketNotification('pulumi-homework-bucket-notification',
    bucket=s3_bucket.id,
    lambda_functions=[
        aws.s3.BucketNotificationLambdaFunctionArgs(
            lambda_function_arn=lambda_function.arn,
            events=['s3:ObjectCreated:*'], #, 's3:ObjectDeleted:*'],
            filter_prefix="",
            filter_suffix="",
        )
    ],
    opts=pulumi.ResourceOptions(depends_on=[lambda_permission])
)

# Export core resource names
pulumi.export('s3_bucket_name', s3_bucket.id)

pulumi.export('dynamo_table_name', dynamodb_table.name)

pulumi.export('lambda_function_arn', lambda_function.arn)
