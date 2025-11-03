"""
Smart Abbreviation Handler - Hybrid Approach
Combines static dictionary with automatic abbreviation detection
"""

import re
from typing import Dict, Set, Tuple
from abbreviations import schwartz_hearst


class SmartAbbreviationHandler:
    """
    Intelligent abbreviation handler that:
    1. Uses a curated dictionary for common terms
    2. Auto-detects abbreviations from your knowledge base
    3. Learns from user interactions
    """

    def __init__(self):
        # Curated dictionary for common abbreviations
        self.static_abbreviations = {
            "MFA": "Multi-Factor Authentication",
            "2FA": "Two-Factor Authentication",
            "SSO": "Single Sign-On",
            "GDPR": "General Data Protection Regulation",
            "PCI DSS": "Payment Card Industry Data Security Standard",
            "SOC 2": "Service Organization Control 2",
            "ISO": "International Organization for Standardization",
            "NIST": "National Institute of Standards and Technology",
            # Add more as needed
        }

        # Dynamically learned abbreviations
        self.learned_abbreviations: Dict[str, str] = {}

    def extract_abbreviations_from_text(self, text: str) -> Dict[str, str]:
        """
        Automatically extract abbreviations from text using Schwartz-Hearst algorithm.

        Example: "Multi-Factor Authentication (MFA)" -> {"MFA": "Multi-Factor Authentication"}
        """
        try:
            pairs = schwartz_hearst.extract_abbreviation_definition_pairs(doc_text=text)
            return {abbr: definition for abbr, definition in pairs.items()}
        except Exception:
            return {}

    def learn_from_knowledge_base(self, questions_and_answers: list):
        """
        Learn abbreviations from your existing knowledge base.

        Args:
            questions_and_answers: List of (question, answer) tuples
        """
        for question, answer in questions_and_answers:
            # Extract from both question and answer
            abbrs_q = self.extract_abbreviations_from_text(question)
            abbrs_a = self.extract_abbreviations_from_text(answer)

            # Merge learned abbreviations
            self.learned_abbreviations.update(abbrs_q)
            self.learned_abbreviations.update(abbrs_a)

        print(f"Learned {len(self.learned_abbreviations)} abbreviations from knowledge base")

    def get_all_abbreviations(self) -> Dict[str, str]:
        """Get combined dictionary of static + learned abbreviations."""
        combined = self.static_abbreviations.copy()
        combined.update(self.learned_abbreviations)
        return combined

    def expand_abbreviations(self, text: str) -> str:
        """
        Expand known abbreviations in text.

        Args:
            text: Input text that may contain abbreviations

        Returns:
            Text with abbreviations expanded
        """
        expanded_text = text
        all_abbrs = self.get_all_abbreviations()

        for abbr, full_form in all_abbrs.items():
            pattern = r'\b' + re.escape(abbr) + r'\b'

            if re.search(pattern, text, re.IGNORECASE):
                replacement = f"{full_form} ({abbr})"
                expanded_text = re.sub(
                    pattern, replacement, expanded_text, flags=re.IGNORECASE
                )

        return expanded_text

    def add_abbreviation(self, abbr: str, full_form: str):
        """Manually add a new abbreviation."""
        self.learned_abbreviations[abbr] = full_form

    def save_learned_abbreviations(self, filepath: str):
        """Save learned abbreviations to file."""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.learned_abbreviations, f, indent=2)

    def load_learned_abbreviations(self, filepath: str):
        """Load previously learned abbreviations."""
        import json
        try:
            with open(filepath, 'r') as f:
                self.learned_abbreviations = json.load(f)
        except FileNotFoundError:
            pass


# Example usage
if __name__ == "__main__":
    handler = SmartAbbreviationHandler()

    # Simulate knowledge base
    knowledge_base = [
        (
            "What is multi-factor authentication and why is it important?",
            "Multi-factor authentication (MFA) requires users to provide two or more verification factors."
        ),
        (
            "What are GDPR requirements?",
            "The General Data Protection Regulation (GDPR) is a regulation in EU law."
        ),
        (
            "Explain ISO 27001",
            "The International Organization for Standardization (ISO) 27001 is a standard for ISMS."
        ),
    ]

    # Learn abbreviations from knowledge base
    handler.learn_from_knowledge_base(knowledge_base)

    # Test expansion
    test_questions = [
        "Why is MFA important?",
        "Tell me about GDPR",
        "What is ISO 27001?",
    ]

    print("\nTesting Smart Abbreviation Expansion:\n")
    for q in test_questions:
        expanded = handler.expand_abbreviations(q)
        print(f"Original:  {q}")
        print(f"Expanded:  {expanded}")
        print()

    # Save learned abbreviations
    handler.save_learned_abbreviations("learned_abbreviations.json")
    print("Saved learned abbreviations to learned_abbreviations.json")
