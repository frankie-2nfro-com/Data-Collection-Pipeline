import boto3
from botocore.exceptions import ClientError
import io
import os

class AwsGateway:
    """AwsGateway is class to handle connectivity with AWS

    Notes:
    This class is with account information. So it is important to add file name to .gitignore to prevent security issue

    Attributes:
        access_key (str): AWS access key
        secret_access_key (str): AWS secret access key
        region_name (str): AWS region name
    """
    
    s3_client = None
    
    def __init__(self):
        """Constructor of AwsGateway
        """
        self.access_key = os.getenv('SCRAPER_AWS_ACCESS_KEY')
        self.secret_access_key = os.getenv('SCRAPER_AWS_SECRET_ACCESS_KEY')
        self.region_name = os.getenv('SCRAPER_AWS_REGION')
        self.storage_name = os.getenv('SCRAPER_AWS_STORAGE_NAME')
        self.directory_name = os.getenv('SCRAPER_AWS_DIRECTORY_NAME')

        self.s3_client = boto3.client('s3', 
            region_name=self.region_name, 
            aws_access_key_id=self.access_key, 
            aws_secret_access_key=self.secret_access_key)


    def upload_file(self, bucket, folder, file_as_binary, file_name):
        """Function to upload local file to s3 storage

        Note:
        Storage and directory need to setup before calling this function

        Returns:
        Success will return True; Unsuccess will return False
        """
        file_as_binary = io.BytesIO(file_as_binary)
        key = folder + "/" + file_name
        try:
            self.s3_client.upload_fileobj(file_as_binary, bucket, key)
        except ClientError as e:
            print(e)
            return False
        return True