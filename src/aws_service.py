import boto3
import io


class AwsService:
    def __init__(self):
        self.dynamo_db = boto3.resource('dynamodb')
        self.sqs = boto3.client('sqs')
        self.s3 = boto3.client('s3')

    def put_item(self, table_name, lead_info):
        table = self.dynamo_db.Table(table_name)
        table.put_item(Item=lead_info)

    def item_exist(self, table_name, key):
        table = self.dynamo_db.Table(table_name)
        response = table.get_item(Key=key)
        return response.get('Item', None) is not None

    def get_item(self, table_name, key):
        table = self.dynamo_db.Table(table_name)
        response = table.get_item(Key=key)
        return response.get('Item')

    def scan(self, table_name, expression):
        table = self.dynamo_db.Table(table_name)
        return table.scan(FilterExpression=expression)['Items']

    def send_message(self, queue_name, message_body, delay=0):
        queue = self.sqs.get_queue_url(QueueName=queue_name)['QueueUrl']
        self.sqs.send_message(
            QueueUrl=queue,
            MessageBody=message_body,
            DelaySeconds=delay)

    def upload_screenshot(self, image_name, image_obj):
        with io.BytesIO(image_obj) as f:
            self.s3.upload_fileobj(f, 'leadgen-error-screenshots', image_name)