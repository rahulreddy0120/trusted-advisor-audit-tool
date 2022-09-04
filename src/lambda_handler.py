#!/usr/bin/env python3
"""
AWS Trusted Advisor Scanner - Lambda Handler
"""

import json
import boto3
import logging
from datetime import datetime
from scanners.lambda_scanner import LambdaScanner
from scanners.rds_scanner import RDSScanner
from scanners.es_scanner import ElasticSearchScanner
from scanners.eks_scanner import EKSScanner
from scanners.elb_scanner import ELBScanner
from scanners.trusted_advisor import TrustedAdvisorScanner
from notifier import Notifier
from utils import load_config, group_findings_by_owner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """Main Lambda handler"""
    logger.info("=" * 70)
    logger.info("AWS Trusted Advisor Scanner Started")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info("=" * 70)
    
    # Load configuration
    config = load_config()
    
    all_findings = []
    
    # Run enabled scanners
    enabled_scanners = config['scanning']['enabled_scanners']
    
    if 'lambda' in enabled_scanners:
        logger.info("\n🔍 Scanning Lambda Functions...")
        scanner = LambdaScanner(config)
        findings = scanner.scan()
        all_findings.extend(findings)
        logger.info(f"   Found {len(findings)} Lambda issues")
    
    if 'rds' in enabled_scanners:
        logger.info("\n🔍 Scanning RDS Databases...")
        scanner = RDSScanner(config)
        findings = scanner.scan()
        all_findings.extend(findings)
        logger.info(f"   Found {len(findings)} RDS issues")
    
    if 'elasticsearch' in enabled_scanners:
        logger.info("\n🔍 Scanning ElasticSearch/OpenSearch...")
        scanner = ElasticSearchScanner(config)
        findings = scanner.scan()
        all_findings.extend(findings)
        logger.info(f"   Found {len(findings)} ES/OS issues")
    
    if 'eks' in enabled_scanners:
        logger.info("\n🔍 Scanning EKS Clusters...")
        scanner = EKSScanner(config)
        findings = scanner.scan()
        all_findings.extend(findings)
        logger.info(f"   Found {len(findings)} EKS issues")
    
    if 'load_balancers' in enabled_scanners:
        logger.info("\n🔍 Scanning Load Balancers...")
        scanner = ELBScanner(config)
        findings = scanner.scan()
        all_findings.extend(findings)
        logger.info(f"   Found {len(findings)} ELB issues")
    
    if 'trusted_advisor' in enabled_scanners:
        logger.info("\n🔍 Scanning Trusted Advisor...")
        scanner = TrustedAdvisorScanner(config)
        findings = scanner.scan()
        all_findings.extend(findings)
        logger.info(f"   Found {len(findings)} Trusted Advisor issues")
    
    # Generate summary
    logger.info(f"\n📊 Total Findings: {len(all_findings)}")
    
    severity_counts = {}
    for finding in all_findings:
        severity = finding['severity']
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    for severity, count in severity_counts.items():
        logger.info(f"   {severity.upper()}: {count}")
    
    # Save results to S3
    save_results_to_s3(all_findings)
    
    # Group findings by owner and send notifications
    if all_findings:
        logger.info("\n📧 Sending Notifications...")
        findings_by_owner = group_findings_by_owner(all_findings, config)
        
        notifier = Notifier(config)
        for owner_email, findings in findings_by_owner.items():
            notifier.send_email(owner_email, findings)
            logger.info(f"   Sent email to {owner_email} ({len(findings)} findings)")
    
    logger.info("\n" + "=" * 70)
    logger.info("Scan Complete")
    logger.info("=" * 70)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'total_findings': len(all_findings),
            'by_severity': severity_counts
        })
    }

def save_results_to_s3(findings):
    """Save scan results to S3"""
    bucket_name = 'trusted-advisor-reports'
    date = datetime.utcnow()
    key = f"{date.year}/{date.month:02d}/{date.day:02d}/scan-results.json"
    
    report = {
        'scan_date': date.isoformat(),
        'findings': findings,
        'summary': {
            'total_findings': len(findings),
            'by_severity': {}
        }
    }
    
    for finding in findings:
        severity = finding['severity']
        report['summary']['by_severity'][severity] = \
            report['summary']['by_severity'].get(severity, 0) + 1
    
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json.dumps(report, indent=2),
            ContentType='application/json'
        )
        logger.info(f"   Saved results to s3://{bucket_name}/{key}")
    except Exception as e:
        logger.error(f"   Failed to save to S3: {e}")
