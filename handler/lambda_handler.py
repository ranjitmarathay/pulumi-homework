import json
import boto3

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    s3 = boto3.client('s3')
    
    dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table('pulumi-homework-table')

    response = s3.get_object(Bucket=bucket, Key=key)

    # print(response)
    
    last_modified = response['LastModified']
    last_modified_str = last_modified.strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        table.put_item(Item={'timestamp': last_modified_str, 'key': key})
    
        return {
            'statusCode': 200,
            'body': json.dumps(f"[SUCCESS] timestamp: {last_modified_str} key: {key}")
        }   
    except Exception as e:
        print(f"Error: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps(f"[FAIL] Error uploading files: {str(e)}")
        }
