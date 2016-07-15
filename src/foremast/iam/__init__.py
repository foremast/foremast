"""Package for managing IAM policies in AWS. Spinnaker does not
directly interfact with IAM so this package mostly uses Boto3
"""
from .create_iam import *
from .destroy_iam import *
