import boto3
import pytest
from botocore.exceptions import ClientError

# This test assumes you have AWS Credentials loaded (e.g. in CI environment)
# It validates the DEPLOYED infrastructure, not just the code.

@pytest.mark.integration
def test_rds_encrypted_at_rest():
    client = boto3.client('rds', region_name='us-east-1')
    
    # Filter for our production instances
    response = client.describe_db_instances(
        Filters=[{'Name': 'db-instance-id', 'Values': ['dtp-postgres-production']}]
    )
    
    for db in response['DBInstances']:
        # FAIL if storage is not encrypted
        assert db['StorageEncrypted'] is True, f"DB {db['DBInstanceIdentifier']} is NOT encrypted!"
        # FAIL if Multi-AZ is disabled
        assert db['MultiAZ'] is True, f"DB {db['DBInstanceIdentifier']} is NOT Multi-AZ!"

@pytest.mark.integration
def test_s3_public_access_block():
    s3 = boto3.client('s3')
    # List buckets with our project tag
    # (Mock logic: in real life, you'd iterate your actual buckets)
    buckets = ["dtp-terraform-state-prod"] 
    
    for bucket in buckets:
        try:
            status = s3.get_public_access_block(Bucket=bucket)
            conf = status['PublicAccessBlockConfiguration']
            assert conf['BlockPublicAcls'] is True
            assert conf['BlockPublicPolicy'] is True
        except ClientError:
            pytest.fail(f"Bucket {bucket} has no Public Access Block configured!")