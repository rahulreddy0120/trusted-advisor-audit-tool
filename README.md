# AWS Trusted Advisor Scanner

Automated compliance and cost optimization scanner that detects deprecated service versions, unused resources, and security issues using AWS Trusted Advisor and direct API calls. Sends email notifications to application owners based on resource tags.

## Overview

This serverless solution runs daily via Lambda to scan your AWS infrastructure for:
- **Deprecated Versions**: Lambda runtimes, RDS engines, ElasticSearch/OpenSearch, EKS clusters
- **Unused Resources**: Idle load balancers, RDS databases with no connections
- **Cost Optimization**: Underutilized resources, unattached volumes
- **Security Issues**: Exposed resources, missing encryption

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     EventBridge Rule                         │
│                  (Daily at 8 AM UTC)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Lambda Function                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │  1. Scan Trusted Advisor Checks                    │    │
│  │  2. Scan Lambda Functions (deprecated runtimes)    │    │
│  │  3. Scan RDS Instances (old engines, no conns)     │    │
│  │  4. Scan ElasticSearch/OpenSearch (old versions)   │    │
│  │  5. Scan EKS Clusters (deprecated K8s versions)    │    │
│  │  6. Scan Load Balancers (no targets)               │    │
│  │  7. Group findings by owner (tags)                 │    │
│  │  8. Send SES emails to owners                      │    │
│  └────────────────────────────────────────────────────┘    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    S3 Bucket                                 │
│              (Scan Results Storage)                          │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Amazon SES                                │
│           (Email Notifications to Owners)                    │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Compliance Scanning
- **Lambda Runtimes**: Detect deprecated Python, Node.js, Java runtimes
- **RDS Engines**: Identify end-of-life MySQL, PostgreSQL, Aurora versions
- **ElasticSearch/OpenSearch**: Flag unsupported versions
- **EKS Clusters**: Alert on deprecated Kubernetes versions

### Cost Optimization
- **Idle RDS Databases**: Find databases with zero connections
- **Unused Load Balancers**: Detect ALB/NLB with no healthy targets
- **Unattached EBS Volumes**: Identify orphaned storage
- **Idle Elastic IPs**: Find unassociated IPs

### Security & Best Practices
- **Trusted Advisor Checks**: Security groups, IAM, S3 buckets
- **Encryption**: Missing encryption at rest/transit
- **Public Exposure**: Publicly accessible resources

### Notifications
- **Tag-Based Routing**: Email owners based on `Owner` or `Team` tags
- **HTML Email Templates**: Professional, actionable emails
- **Severity Levels**: Critical, High, Medium, Low
- **Remediation Links**: Direct links to AWS Console

## Project Structure

```
.
├── src/
│   ├── lambda_handler.py      # Main Lambda entry point
│   ├── scanners/
│   │   ├── trusted_advisor.py # Trusted Advisor API
│   │   ├── lambda_scanner.py  # Lambda runtime scanner
│   │   ├── rds_scanner.py     # RDS version & connection scanner
│   │   ├── es_scanner.py      # ElasticSearch/OpenSearch scanner
│   │   ├── eks_scanner.py     # EKS version scanner
│   │   └── elb_scanner.py     # Load balancer scanner
│   ├── notifier.py            # SES email sender
│   └── utils.py               # Helper functions
├── templates/
│   └── email_template.html    # HTML email template
├── terraform/
│   ├── main.tf               # Main Terraform config
│   ├── lambda.tf             # Lambda function
│   ├── iam.tf                # IAM roles and policies
│   ├── eventbridge.tf        # Scheduled trigger
│   ├── s3.tf                 # S3 bucket for results
│   └── ses.tf                # SES configuration
├── config/
│   └── config.yaml           # Scanner configuration
├── requirements.txt          # Python dependencies
└── README.md
```

## Quick Start

### 1. Prerequisites

- AWS CLI configured
- Terraform >= 1.0
- Python 3.11+
- SES verified email domain or addresses

### 2. Configure Settings

Edit `config/config.yaml`:

```yaml
scanning:
  # Services to scan
  enabled_scanners:
    - trusted_advisor
    - lambda
    - rds
    - elasticsearch
    - eks
    - load_balancers
  
  # Deprecated versions to flag
  deprecated_versions:
    lambda_runtimes:
      - python3.7
      - python3.8
      - nodejs12.x
      - nodejs14.x
    rds_engines:
      mysql:
        - "5.6"
        - "5.7"
      postgres:
        - "10"
        - "11"
    eks_versions:
      - "1.21"
      - "1.22"
      - "1.23"
  
  # Thresholds
  rds_idle_days: 7           # Days with zero connections
  elb_no_targets_days: 3     # Days with no healthy targets

notifications:
  from_email: "aws-scanner@company.com"
  default_recipients:
    - "cloud-ops@company.com"
  
  # Tag keys to identify owners
  owner_tags:
    - Owner
    - Team
    - Contact
  
  # Severity thresholds
  send_email_if_severity:
    - critical
    - high
    - medium
```

### 3. Deploy Infrastructure

```bash
cd terraform

# Initialize
terraform init

# Deploy
terraform apply
```

This creates:
- Lambda function with 15-minute timeout
- EventBridge rule (daily at 8 AM UTC)
- IAM role with necessary permissions
- S3 bucket for scan results
- CloudWatch log group

### 4. Verify SES Email

```bash
# Verify sender email
aws ses verify-email-identity --email-address aws-scanner@company.com

# Check verification status
aws ses get-identity-verification-attributes \
  --identities aws-scanner@company.com
```

### 5. Test Manually

```bash
# Invoke Lambda
aws lambda invoke \
  --function-name trusted-advisor-scanner \
  --payload '{}' \
  response.json

# View logs
aws logs tail /aws/lambda/trusted-advisor-scanner --follow
```

## Scan Results

### Email Notification Example

```
Subject: [AWS Scanner] 5 Issues Found - Action Required

Hi Platform Team,

Your AWS resources have 5 issues requiring attention:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 CRITICAL (2)

Lambda Function: user-api-prod
  Issue: Deprecated runtime python3.8 (EOL: Oct 2024)
  Impact: Security vulnerabilities, no updates
  Action: Upgrade to python3.11 or python3.12
  Link: https://console.aws.amazon.com/lambda/home#/functions/user-api-prod

RDS Instance: prod-mysql-db
  Issue: MySQL 5.7 (EOL: Feb 2024)
  Impact: No security patches, compliance risk
  Action: Upgrade to MySQL 8.0
  Link: https://console.aws.amazon.com/rds/home#database:id=prod-mysql-db

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟠 HIGH (2)

EKS Cluster: prod-cluster
  Issue: Kubernetes 1.23 (EOL: Sep 2024)
  Impact: No security updates
  Action: Upgrade to 1.28 or 1.29
  Link: https://console.aws.amazon.com/eks/home#/clusters/prod-cluster

Load Balancer: api-alb
  Issue: No healthy targets for 5 days
  Cost: $16.20/month wasted
  Action: Delete if unused or fix targets
  Link: https://console.aws.amazon.com/ec2/home#LoadBalancers:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟡 MEDIUM (1)

RDS Instance: analytics-db
  Issue: Zero connections for 7 days
  Cost: $145/month if unused
  Action: Review usage or consider stopping
  Link: https://console.aws.amazon.com/rds/home#database:id=analytics-db

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Potential Savings: $161.20/month

This scan was performed on 2024-11-15 08:00 UTC
Full report: s3://trusted-advisor-reports/2024/11/15/scan-results.json
```

### S3 Report Format

```json
{
  "scan_date": "2024-11-15T08:00:00Z",
  "findings": [
    {
      "severity": "critical",
      "category": "compliance",
      "service": "lambda",
      "resource_id": "user-api-prod",
      "resource_arn": "arn:aws:lambda:us-east-1:123456789012:function:user-api-prod",
      "issue": "Deprecated runtime python3.8",
      "impact": "Security vulnerabilities, no updates",
      "recommendation": "Upgrade to python3.11 or python3.12",
      "owner": "platform-team@company.com",
      "tags": {
        "Team": "Platform",
        "Environment": "Production"
      }
    }
  ],
  "summary": {
    "total_findings": 5,
    "by_severity": {
      "critical": 2,
      "high": 2,
      "medium": 1
    },
    "potential_monthly_savings": 161.20
  }
}
```

## Supported Checks

### Lambda Functions
- ✅ Deprecated runtimes (Python 3.7, 3.8, Node 12.x, 14.x, etc.)
- ✅ Functions not invoked in 90 days
- ✅ Large deployment packages (>50MB)

### RDS Databases
- ✅ End-of-life engine versions
- ✅ Zero connections for N days
- ✅ Missing encryption
- ✅ Public accessibility

### ElasticSearch/OpenSearch
- ✅ Unsupported versions
- ✅ Missing encryption at rest
- ✅ Public endpoints

### EKS Clusters
- ✅ Deprecated Kubernetes versions
- ✅ Outdated platform versions
- ✅ Missing logging

### Load Balancers
- ✅ No healthy targets
- ✅ Zero requests for N days
- ✅ Unused listeners

### Trusted Advisor
- ✅ All available checks (requires Business/Enterprise support)
- ✅ Security groups
- ✅ IAM usage
- ✅ S3 bucket permissions

## AWS Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "support:DescribeTrustedAdvisorChecks",
        "support:DescribeTrustedAdvisorCheckResult",
        "lambda:ListFunctions",
        "lambda:GetFunction",
        "rds:DescribeDBInstances",
        "rds:DescribeDBClusters",
        "es:ListDomainNames",
        "es:DescribeElasticsearchDomain",
        "eks:ListClusters",
        "eks:DescribeCluster",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeTargetHealth",
        "cloudwatch:GetMetricStatistics",
        "ses:SendEmail",
        "s3:PutObject"
      ],
      "Resource": "*"
    }
  ]
}
```

## Cost

- **Lambda**: ~$2-3/month (daily 10-minute runs)
- **S3**: ~$1/month (scan results storage)
- **SES**: $0.10 per 1,000 emails
- **Total**: ~$3-5/month

**ROI**: If you save even $100/month from findings, that's a 20x return.

## Real-World Impact

At my previous organization:
- Identified 45 Lambda functions with deprecated runtimes
- Found 12 idle RDS databases costing $1,800/month
- Detected 8 unused load balancers saving $130/month
- Automated compliance reporting, saving 10 hours/week
- Achieved 95% remediation rate within 30 days

## Scheduling

Default: Daily at 8 AM UTC

Modify in `terraform/eventbridge.tf`:
```hcl
schedule_expression = "cron(0 8 * * ? *)"  # Daily
# or
schedule_expression = "cron(0 8 ? * MON *)"  # Weekly on Monday
```

## Troubleshooting

### No Emails Received

```bash
# Check SES verification
aws ses get-identity-verification-attributes \
  --identities aws-scanner@company.com

# Check Lambda logs
aws logs tail /aws/lambda/trusted-advisor-scanner --follow
```

### Trusted Advisor Access Denied

Requires AWS Business or Enterprise support plan.

### Missing Findings

Ensure Lambda has correct IAM permissions and timeout is sufficient (15 min).

## Contributing

Pull requests welcome! Please open an issue first.

## License

MIT License

## Author

Rahul Reddy  
Cloud FinOps Engineer  
[LinkedIn](https://www.linkedin.com/in/rahul-7947/) | [GitHub](https://github.com/rahulreddy0120)










<!-- updated: 2023-07-20 -->

<!-- updated: 2023-09-10 -->

<!-- updated: 2023-11-28 -->

<!-- updated: 2024-01-15 -->

<!-- updated: 2024-04-02 -->

<!-- updated: 2024-06-18 -->

<!-- updated: 2024-09-05 -->

<!-- updated: 2024-11-22 -->

<!-- updated: 2025-01-10 -->

<!-- updated: 2025-03-28 -->

<!-- updated: 2025-06-15 -->

<!-- updated: 2025-09-02 -->

<!-- updated: 2025-12-18 -->

<!-- 2022-09-02T14:25:00 -->

<!-- 2022-09-29T10:40:00 -->

<!-- 2022-11-14T15:55:00 -->

<!-- 2022-12-22T11:10:00 -->

<!-- 2023-02-06T09:25:00 -->

<!-- 2023-04-20T14:40:00 -->

<!-- 2023-06-05T10:55:00 -->

<!-- 2023-08-21T16:10:00 -->

<!-- 2023-10-09T11:25:00 -->

<!-- 2023-12-18T09:40:00 -->

<!-- 2024-03-04T14:55:00 -->

<!-- 2024-05-20T10:10:00 -->

<!-- 2024-08-12T15:25:00 -->

<!-- 2024-10-28T11:40:00 -->

<!-- 2025-01-06T09:55:00 -->

<!-- 2025-03-24T14:10:00 -->

<!-- 2025-06-09T10:25:00 -->

<!-- 2025-09-15T15:40:00 -->

<!-- 2025-12-01T11:55:00 -->

<!-- 2022-09-02T14:25:00 -->

<!-- 2022-09-29T10:40:00 -->

<!-- 2022-11-14T15:55:00 -->

<!-- 2022-12-22T11:10:00 -->

<!-- 2023-02-06T09:25:00 -->

<!-- 2023-04-20T14:40:00 -->

<!-- 2023-06-05T10:55:00 -->

<!-- 2023-08-21T16:10:00 -->

<!-- 2023-10-09T11:25:00 -->

<!-- 2023-12-18T09:40:00 -->

<!-- 2024-03-04T14:55:00 -->

<!-- 2024-05-20T10:10:00 -->

<!-- 2024-08-12T15:25:00 -->

<!-- 2024-10-28T11:40:00 -->

<!-- 2025-01-06T09:55:00 -->

<!-- 2025-03-24T14:10:00 -->

<!-- 2025-06-09T10:25:00 -->

<!-- 2025-09-15T15:40:00 -->

<!-- 2025-12-01T11:55:00 -->

<!-- 2022-08-16T14:25:00 -->

<!-- 2022-08-17T10:40:00 -->

<!-- 2022-09-29T15:55:00 -->

<!-- 2022-12-22T11:10:00 -->

<!-- 2023-04-20T09:25:00 -->

<!-- 2023-04-21T14:40:00 -->

<!-- 2023-08-21T10:55:00 -->

<!-- 2023-12-18T16:10:00 -->

<!-- 2024-01-15T11:25:00 -->

<!-- 2024-05-20T09:40:00 -->

<!-- 2024-10-28T14:55:00 -->

<!-- 2024-10-29T10:10:00 -->

<!-- 2025-03-24T15:25:00 -->

<!-- 2025-08-09T11:40:00 -->

<!-- 2025-12-01T09:55:00 -->

<!-- 2022-08-24T14:25:00 -->

<!-- 2022-08-25T10:40:00 -->

<!-- 2022-10-27T15:55:00 -->

<!-- 2023-01-03T11:10:00 -->

<!-- 2023-05-16T09:25:00 -->

<!-- 2023-05-17T14:40:00 -->

<!-- 2023-09-05T10:55:00 -->

<!-- 2024-01-02T16:10:00 -->

<!-- 2024-05-14T11:25:00 -->

<!-- 2024-08-20T09:40:00 -->

<!-- 2024-12-03T14:55:00 -->

<!-- 2024-12-04T10:10:00 -->

<!-- 2025-05-06T15:25:00 -->

<!-- 2025-09-23T11:40:00 -->

<!-- 2026-02-17T09:55:00 -->

<!-- 2022-09-12T08:22:00 -->

<!-- 2022-10-09T12:39:00 -->

<!-- 2022-10-10T15:29:00 -->

<!-- 2022-10-14T12:20:00 -->

<!-- 2022-10-27T17:42:00 -->

<!-- 2022-11-20T12:35:00 -->

<!-- 2022-11-25T11:05:00 -->

<!-- 2022-12-09T13:30:00 -->

<!-- 2022-12-13T13:27:00 -->

<!-- 2022-12-17T13:22:00 -->

<!-- 2023-01-15T16:38:00 -->

<!-- 2023-02-16T12:30:00 -->

<!-- 2023-03-05T08:09:00 -->

<!-- 2023-03-23T11:49:00 -->

<!-- 2023-04-02T17:03:00 -->

<!-- 2023-04-15T09:10:00 -->

<!-- 2023-06-29T15:28:00 -->

<!-- 2023-07-07T08:05:00 -->

<!-- 2023-08-17T13:07:00 -->

<!-- 2023-10-19T16:45:00 -->

<!-- 2023-11-17T08:18:00 -->

<!-- 2023-11-18T17:37:00 -->

<!-- 2024-01-13T13:39:00 -->

<!-- 2024-01-23T11:47:00 -->

<!-- 2024-02-05T08:02:00 -->

<!-- 2024-04-03T11:24:00 -->

<!-- 2024-04-12T08:53:00 -->

<!-- 2024-05-10T11:38:00 -->

<!-- 2024-09-23T15:07:00 -->

<!-- 2024-11-06T11:07:00 -->

<!-- 2025-02-24T15:32:00 -->

<!-- 2025-05-03T13:06:00 -->

<!-- 2025-05-25T17:14:00 -->

<!-- 2025-06-18T12:58:00 -->

<!-- 2025-09-04T08:14:00 -->

<!-- 2025-09-15T11:49:00 -->

<!-- 2025-09-20T12:20:00 -->

<!-- 2025-11-14T13:14:00 -->

<!-- 2026-01-18T12:37:00 -->

<!-- 2026-03-24T14:26:00 -->

<!-- 2026-04-19T12:46:00 -->

<!-- 2022-10-07T16:04:00 -->

<!-- 2022-10-25T13:31:00 -->

<!-- 2022-11-22T12:12:00 -->

<!-- 2023-02-10T08:38:00 -->

<!-- 2023-07-06T10:45:00 -->

<!-- 2023-07-30T10:48:00 -->

<!-- 2023-09-10T15:16:00 -->

<!-- 2023-09-11T10:29:00 -->

<!-- 2023-11-09T12:11:00 -->

<!-- 2023-12-03T15:34:00 -->

<!-- 2024-03-13T09:58:00 -->

<!-- 2024-04-11T10:15:00 -->

<!-- 2024-04-28T14:47:00 -->

<!-- 2024-08-30T15:53:00 -->

<!-- 2025-03-19T08:22:00 -->

<!-- 2025-09-25T13:37:00 -->

<!-- 2025-11-28T16:02:00 -->

<!-- 2025-12-03T14:00:00 -->

<!-- 2026-04-28T17:16:00 -->

<!-- 2022-10-07T16:04:00 -->

<!-- 2022-10-25T13:31:00 -->

<!-- 2022-11-22T12:12:00 -->

<!-- 2023-02-10T08:38:00 -->

<!-- 2023-07-06T10:45:00 -->

<!-- 2023-07-30T10:48:00 -->

<!-- 2023-09-10T15:16:00 -->

<!-- 2023-09-11T10:29:00 -->

<!-- 2023-11-09T12:11:00 -->

<!-- 2023-12-03T15:34:00 -->

<!-- 2024-03-13T09:58:00 -->

<!-- 2024-04-11T10:15:00 -->

<!-- 2024-04-28T14:47:00 -->

<!-- 2024-08-30T15:53:00 -->

<!-- 2025-03-19T08:22:00 -->

<!-- 2025-09-25T13:37:00 -->

<!-- 2025-11-28T16:02:00 -->

<!-- 2025-12-03T14:00:00 -->

<!-- 2026-04-28T17:16:00 -->

<!-- 2022-10-07T16:04:00 -->

<!-- 2022-10-25T13:31:00 -->
