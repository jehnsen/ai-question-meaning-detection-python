"""
Abbreviation handler for expanding common acronyms before AI search
"""

# Common abbreviations in compliance/security domain
ABBREVIATIONS = {
    "MFA": "Multi-Factor Authentication",
    "2FA": "Two-Factor Authentication",
    "SSO": "Single Sign-On",
    "GDPR": "General Data Protection Regulation",
    "PCI DSS": "Payment Card Industry Data Security Standard",
    "SOC 2": "Service Organization Control 2",
    "ISO": "International Organization for Standardization",
    "NIST": "National Institute of Standards and Technology",
    "RBAC": "Role-Based Access Control",
    "IAM": "Identity and Access Management",
    "VPN": "Virtual Private Network",
    "API": "Application Programming Interface",
    "SQL": "Structured Query Language",
    "XSS": "Cross-Site Scripting",
    "CSRF": "Cross-Site Request Forgery",
    "DDoS": "Distributed Denial of Service",
    "WAF": "Web Application Firewall",
    "IDS": "Intrusion Detection System",
    "IPS": "Intrusion Prevention System",
    "SIEM": "Security Information and Event Management",
    "PKI": "Public Key Infrastructure",
    "CA": "Certificate Authority",
    "TLS": "Transport Layer Security",
    "SSL": "Secure Sockets Layer",
    "HTTPS": "Hypertext Transfer Protocol Secure",
    "DNS": "Domain Name System",
    "DNSSEC": "Domain Name System Security Extensions",
    "DLP": "Data Loss Prevention",
    "EDR": "Endpoint Detection and Response",
    "MDM": "Mobile Device Management",
    "BYOD": "Bring Your Own Device",
    "RTO": "Recovery Time Objective",
    "RPO": "Recovery Point Objective",
    "BCP": "Business Continuity Plan",
    "DR": "Disaster Recovery",
    "ISMS": "Information Security Management System",
    "DPIA": "Data Protection Impact Assessment",
    "DPO": "Data Protection Officer",
    "PII": "Personally Identifiable Information",
    "PHI": "Protected Health Information",
    "HIPAA": "Health Insurance Portability and Accountability Act",
    "SOX": "Sarbanes-Oxley Act",
    "FERPA": "Family Educational Rights and Privacy Act",
    "CCPA": "California Consumer Privacy Act",
    "AES": "Advanced Encryption Standard",
    "RSA": "Rivest-Shamir-Adleman",
    "SHA": "Secure Hash Algorithm",
    "OWASP": "Open Web Application Security Project",
    "CVE": "Common Vulnerabilities and Exposures",
    "CVSS": "Common Vulnerability Scoring System",
}


def expand_abbreviations(text: str) -> str:
    """
    Expand known abbreviations in the text.

    Args:
        text: Input text that may contain abbreviations

    Returns:
        Text with abbreviations expanded

    Examples:
        >>> expand_abbreviations("What is MFA?")
        "What is Multi-Factor Authentication (MFA)?"

        >>> expand_abbreviations("Why is 2FA important?")
        "Why is Two-Factor Authentication (2FA) important?"
    """
    expanded_text = text

    # Replace each abbreviation with "expanded (abbr)" format
    for abbr, full_form in ABBREVIATIONS.items():
        # Case-insensitive matching but preserve original case
        import re

        # Match whole word abbreviations
        pattern = r'\b' + re.escape(abbr) + r'\b'

        # Check if abbreviation exists in text
        if re.search(pattern, text, re.IGNORECASE):
            # Replace with expanded form + abbreviation in parentheses
            replacement = f"{full_form} ({abbr})"
            expanded_text = re.sub(pattern, replacement, expanded_text, flags=re.IGNORECASE)

    return expanded_text


def should_expand(text: str) -> bool:
    """
    Check if the text contains any known abbreviations.

    Args:
        text: Input text to check

    Returns:
        True if text contains abbreviations, False otherwise
    """
    import re

    for abbr in ABBREVIATIONS.keys():
        pattern = r'\b' + re.escape(abbr) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


# Example usage
if __name__ == "__main__":
    test_cases = [
        "What is MFA?",
        "Why is 2FA important?",
        "Tell me about GDPR requirements",
        "What is the difference between ISO 27001 and ISO 27002?",
        "How does SSO work?",
        "What are PCI DSS requirements?",
        "Explain RBAC",
        "What is a normal question without abbreviations?",
    ]

    print("Testing Abbreviation Expansion:\n")

    for test in test_cases:
        expanded = expand_abbreviations(test)
        if test != expanded:
            print(f"Original:  {test}")
            print(f"Expanded:  {expanded}")
            print()
        else:
            print(f"No change: {test}\n")
