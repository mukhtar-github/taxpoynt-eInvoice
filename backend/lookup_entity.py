#!/usr/bin/env python3
"""
Standalone script for entity lookup using TaxPoynt's FIRS service.

This script demonstrates proper authentication and entity lookup using
the TaxPoynt FIRS service implementation.
"""
import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FIRS service from the TaxPoynt application
from app.services.firs_service import FIRSService
from app.core.config import settings

async def lookup_entity_by_tin(tin: str) -> Dict[str, Any]:
    """
    Look up an entity by TIN using proper authentication.
    
    Args:
        tin: The Tax Identification Number (TIN) to look up
        
    Returns:
        Dictionary with lookup results
    """
    # Create a FIRS service instance
    # Use sandbox mode for testing
    firs_service = FIRSService(use_sandbox=True)
    
    # Try direct lookup with TIN (which may fail due to UUID requirements)
    try:
        print(f"Attempting direct lookup with TIN: {tin}")
        entity = await firs_service.get_entity(tin)
        print(f"Entity found: {json.dumps(entity, indent=2)}")
        return {"success": True, "entity": entity}
    except Exception as e:
        print(f"Direct lookup failed: {str(e)}")

    # If direct lookup fails, try search by reference parameter
    try:
        print(f"Searching for entity with reference: {tin}")
        search_params = {"reference": tin}
        search_results = await firs_service.search_entities(search_params)
        
        # Check if we have results
        items = search_results.get("data", {}).get("items", [])
        if items and len(items) > 0:
            # Found at least one match
            entity = items[0]  # Get the first match
            print(f"Entity found by search: {json.dumps(entity, indent=2)}")
            return {"success": True, "entity": entity}
        else:
            print(f"No entities found with reference: {tin}")
    except Exception as e:
        print(f"Entity search failed: {str(e)}")
    
    # If we get here, both approaches failed
    return {
        "success": False,
        "error": f"Could not find entity with TIN: {tin}"
    }

async def main():
    """Main execution function."""
    # Get TIN from command line argument or use default
    tin = sys.argv[1] if len(sys.argv) > 1 else "31569955-0001"
    
    print(f"Looking up entity with TIN: {tin}")
    result = await lookup_entity_by_tin(tin)
    
    if result["success"]:
        print("\n✅ Entity lookup successful!")
        if "entity" in result:
            print("\nEntity Details:")
            print(json.dumps(result["entity"], indent=2))
    else:
        print("\n❌ Entity lookup failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())
