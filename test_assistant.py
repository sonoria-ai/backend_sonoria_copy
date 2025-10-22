#!/usr/bin/env python
"""
Test script for the assistant app
Run with: python test_assistant.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sonoria_backend.settings')
django.setup()

from assistant.prompt_builder import build_system_prompt
from gabby_booking.models import Organization

def test_prompt_builder():
    print("Testing prompt builder...\n")

    # Get first organization
    org = Organization.objects.first()

    if not org:
        print("No organization found. Please create one in the dashboard first.")
        return

    print(f"Building prompt for: {org.name} (ID: {org.id})\n")

    prompt = build_system_prompt(org.id)

    if prompt:
        print("=" * 80)
        print("GENERATED SYSTEM PROMPT")
        print("=" * 80)
        print(prompt)
        print("=" * 80)
        print(f"\nPrompt length: {len(prompt)} characters")
        print("✅ Prompt generated successfully!")
    else:
        print("❌ Failed to generate prompt")

if __name__ == "__main__":
    test_prompt_builder()
