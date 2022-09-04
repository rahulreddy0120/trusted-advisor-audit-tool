"""Lambda function scanner for deprecated runtimes"""
import boto3

class LambdaScanner:
    def __init__(self, config):
        self.config = config
        self.lambda_client = boto3.client('lambda')
    
    def scan(self):
        findings = []
        deprecated_runtimes = self.config['scanning']['deprecated_versions']['lambda_runtimes']
        
        paginator = self.lambda_client.get_paginator('list_functions')
        for page in paginator.paginate():
            for function in page['Functions']:
                runtime = function.get('Runtime', '')
                if runtime in deprecated_runtimes:
                    findings.append({
                        'severity': 'critical',
                        'category': 'compliance',
                        'service': 'lambda',
                        'resource_id': function['FunctionName'],
                        'resource_arn': function['FunctionArn'],
                        'issue': f"Deprecated runtime {runtime}",
                        'impact': "Security vulnerabilities, no updates",
                        'recommendation': "Upgrade to latest runtime version",
                        'tags': function.get('Tags', {})
                    })
        
        return findings
