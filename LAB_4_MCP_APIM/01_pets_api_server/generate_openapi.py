"""
Generate OpenAPI JSON specification from FastAPI app
"""
import json
from app import app

if __name__ == "__main__":
    openapi_schema = app.openapi()
    
    # Write to file
    with open("openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print("✅ OpenAPI specification generated: openapi.json")
    print(f"   Title: {openapi_schema['info']['title']}")
    print(f"   Version: {openapi_schema['info']['version']}")
    print(f"   Endpoints: {len(openapi_schema['paths'])} paths")
