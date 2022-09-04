"""Utility functions"""
import yaml

def load_config():
    with open('config/config.yaml', 'r') as f:
        return yaml.safe_load(f)

def group_findings_by_owner(findings, config):
    grouped = {}
    owner_tags = config['notifications']['owner_tags']
    default_recipients = config['notifications']['default_recipients']
    
    for finding in findings:
        owner = None
        tags = finding.get('tags', {})
        
        for tag_key in owner_tags:
            if tag_key in tags:
                owner = tags[tag_key]
                break
        
        if not owner:
            owner = default_recipients[0]
        
        if owner not in grouped:
            grouped[owner] = []
        grouped[owner].append(finding)
    
    return grouped
