

"""
DynamoDB Manager
Handles DynamoDB operations for the migration tool
"""

import boto3
import time
from botocore.exceptions import ClientError, BotoCoreError


class DynamoDBManager:
    """Manages DynamoDB operations"""
    
    def __init__(self, region='us-east-1', table_configs=None):
        self.region = region
        self.table_configs = table_configs or {}
        
        try:
            self.dynamodb = boto3.client('dynamodb', region_name=region)
        except Exception as e:
            raise Exception(f"Failed to initialize DynamoDB client: {str(e)}")
    
    def create_table(self, table_name, schema, force=False):
        """Create a DynamoDB table"""
        try:
            # Check if table exists
            if self.table_exists(table_name):
                if not force:
                    return False  # Table exists, not created
                else:
                    # Delete existing table
                    self.delete_table(table_name)
                    self.wait_for_table_deletion(table_name)
            
            # Create table definition
            table_definition = {
                'TableName': table_name,
                'BillingMode': schema.get('billing_mode', 'ON_DEMAND'),
                'KeySchema': [
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'}
                ]
            }
            
            # Add Global Secondary Indexes if specified
            gsi_list = []
            for gsi in schema.get('global_secondary_indexes', []):
                gsi_definition = {
                    'IndexName': gsi['index_name'],
                    'KeySchema': [],
                    'Projection': {'ProjectionType': 'ALL'}
                }
                
                # Add GSI attributes to attribute definitions
                for key in gsi['keys']:
                    if len(gsi['keys']) == 1:  # Hash key only
                        gsi_definition['KeySchema'].append({
                            'AttributeName': key,
                            'KeyType': 'HASH'
                        })
                    elif len(gsi['keys']) == 2:  # Hash and range key
                        key_type = 'HASH' if gsi['keys'].index(key) == 0 else 'RANGE'
                        gsi_definition['KeySchema'].append({
                            'AttributeName': key,
                            'KeyType': key_type
                        })
                    
                    # Add to attribute definitions if not already present
                    attr_exists = any(
                        attr['AttributeName'] == key 
                        for attr in table_definition['AttributeDefinitions']
                    )
                    if not attr_exists:
                        table_definition['AttributeDefinitions'].append({
                            'AttributeName': key,
                            'AttributeType': 'S'
                        })
                
                # Set billing mode for GSI
                if table_definition['BillingMode'] == 'ON_DEMAND':
                    gsi_definition['BillingMode'] = 'ON_DEMAND'
                else:
                    gsi_definition['ProvisionedThroughput'] = {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                
                gsi_list.append(gsi_definition)
            
            if gsi_list:
                table_definition['GlobalSecondaryIndexes'] = gsi_list
            
            # Set provisioned throughput if not on-demand
            if table_definition['BillingMode'] != 'ON_DEMAND':
                table_definition['ProvisionedThroughput'] = {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            
            # Create the table
            response = self.dynamodb.create_table(**table_definition)
            
            # Wait for table to be active
            self.wait_for_table_active(table_name)
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceInUseException':
                return False  # Table already exists
            else:
                raise Exception(f"Failed to create table {table_name}: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to create table {table_name}: {str(e)}")
    
    def table_exists(self, table_name):
        """Check if a table exists"""
        try:
            self.dynamodb.describe_table(TableName=table_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            else:
                raise
    
    def delete_table(self, table_name):
        """Delete a table"""
        try:
            self.dynamodb.delete_table(TableName=table_name)
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
    
    def wait_for_table_active(self, table_name, timeout=300):
        """Wait for table to become active"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.dynamodb.describe_table(TableName=table_name)
                status = response['Table']['TableStatus']
                
                if status == 'ACTIVE':
                    return True
                elif status in ['CREATING', 'UPDATING']:
                    time.sleep(5)
                    continue
                else:
                    raise Exception(f"Table {table_name} is in unexpected state: {status}")
                    
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    time.sleep(5)
                    continue
                else:
                    raise
        
        raise Exception(f"Timeout waiting for table {table_name} to become active")
    
    def wait_for_table_deletion(self, table_name, timeout=300):
        """Wait for table to be deleted"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                self.dynamodb.describe_table(TableName=table_name)
                time.sleep(5)
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    return True
                else:
                    raise
        
        raise Exception(f"Timeout waiting for table {table_name} to be deleted")
    
    def batch_write_items(self, table_name, items, max_retries=3):
        """Batch write items to DynamoDB"""
        if not items:
            return True
        
        # Split items into batches of 25 (DynamoDB limit)
        batch_size = 25
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Prepare batch write request
            request_items = {
                table_name: [
                    {'PutRequest': {'Item': item}}
                    for item in batch
                ]
            }
            
            # Execute batch write with retries
            retries = 0
            while retries < max_retries:
                try:
                    response = self.dynamodb.batch_write_item(RequestItems=request_items)
                    
                    # Handle unprocessed items
                    unprocessed_items = response.get('UnprocessedItems', {})
                    if unprocessed_items:
                        # Retry unprocessed items
                        request_items = unprocessed_items
                        retries += 1
                        time.sleep(2 ** retries)  # Exponential backoff
                        continue
                    else:
                        break  # Success
                        
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code in ['ProvisionedThroughputExceededException', 'ThrottlingException']:
                        retries += 1
                        if retries < max_retries:
                            time.sleep(2 ** retries)
                            continue
                        else:
                            raise Exception(f"Max retries exceeded for batch write: {str(e)}")
                    else:
                        raise Exception(f"Batch write failed: {str(e)}")
                except Exception as e:
                    raise Exception(f"Batch write failed: {str(e)}")
            
            if retries >= max_retries:
                raise Exception("Max retries exceeded for batch write")
        
        return True
    
    def get_table_item_count(self, table_name):
        """Get approximate item count for a table"""
        try:
            response = self.dynamodb.describe_table(TableName=table_name)
            return response['Table']['ItemCount']
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return 0
            else:
                raise Exception(f"Failed to get item count for {table_name}: {str(e)}")
    
    def scan_table(self, table_name, filter_expression=None, expression_attribute_values=None):
        """Scan a table and return all items"""
        items = []
        
        scan_kwargs = {'TableName': table_name}
        if filter_expression:
            scan_kwargs['FilterExpression'] = filter_expression
        if expression_attribute_values:
            scan_kwargs['ExpressionAttributeValues'] = expression_attribute_values
        
        try:
            while True:
                response = self.dynamodb.scan(**scan_kwargs)
                items.extend(response.get('Items', []))
                
                # Check for more items
                if 'LastEvaluatedKey' not in response:
                    break
                
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
            
            return items
            
        except ClientError as e:
            raise Exception(f"Failed to scan table {table_name}: {str(e)}")
    
    def query_table(self, table_name, key_condition_expression, expression_attribute_values, 
                   index_name=None, limit=None):
        """Query a table"""
        query_kwargs = {
            'TableName': table_name,
            'KeyConditionExpression': key_condition_expression,
            'ExpressionAttributeValues': expression_attribute_values
        }
        
        if index_name:
            query_kwargs['IndexName'] = index_name
        
        if limit:
            query_kwargs['Limit'] = limit
        
        try:
            response = self.dynamodb.query(**query_kwargs)
            return response.get('Items', [])
        except ClientError as e:
            raise Exception(f"Failed to query table {table_name}: {str(e)}")
    
    def get_item(self, table_name, key):
        """Get a single item from table"""
        try:
            response = self.dynamodb.get_item(
                TableName=table_name,
                Key=key
            )
            return response.get('Item')
        except ClientError as e:
            raise Exception(f"Failed to get item from {table_name}: {str(e)}")
    
    def put_item(self, table_name, item):
        """Put a single item to table"""
        try:
            self.dynamodb.put_item(
                TableName=table_name,
                Item=item
            )
            return True
        except ClientError as e:
            raise Exception(f"Failed to put item to {table_name}: {str(e)}")


