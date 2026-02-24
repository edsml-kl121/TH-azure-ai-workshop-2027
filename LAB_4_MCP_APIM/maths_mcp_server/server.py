#!/usr/bin/env python3
# Copyright (c) Microsoft. All rights reserved.

"""
MCP Server: Math & Text Utilities
Contains only @mcp.tool() functions (no resources or prompts).
"""

import argparse
import base64
import json
import sys
from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP
mcp = FastMCP("Math & Text Utilities")


# ---------------------------------------------------------------------------
# Math Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def calculate(expression: str) -> str:
    """
    Evaluate a mathematical expression safely.
    
    Args:
        expression: A mathematical expression (e.g., "2 + 2", "10 * 5 - 3")
    
    Returns:
        The result of the calculation as a string
    """
    try:
        # Safe evaluation - only allow numbers and basic operators
        allowed_chars = set('0123456789+-*/(). ')
        if not all(c in allowed_chars for c in expression):
            return f"Error: Expression contains invalid characters. Only numbers and +, -, *, /, (), . allowed"
        
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"


@mcp.tool()
def fibonacci(n: int) -> str:
    """
    Generate the first N numbers in the Fibonacci sequence.
    
    Args:
        n: How many Fibonacci numbers to generate (max 50)
    
    Returns:
        JSON string containing the Fibonacci sequence
    """
    if n < 1 or n > 50:
        return json.dumps({"error": "n must be between 1 and 50"})
    
    if n == 1:
        sequence = [0]
    elif n == 2:
        sequence = [0, 1]
    else:
        sequence = [0, 1]
        for i in range(2, n):
            sequence.append(sequence[i-1] + sequence[i-2])
    
    return json.dumps({
        "count": n,
        "sequence": sequence,
        "last": sequence[-1]
    }, indent=2)


@mcp.tool()
def is_prime(number: int) -> str:
    """
    Check if a number is prime.
    
    Args:
        number: The number to check
    
    Returns:
        JSON string with the result and explanation
    """
    if number < 2:
        return json.dumps({
            "number": number,
            "is_prime": False,
            "reason": "Numbers less than 2 are not prime"
        }, indent=2)
    
    if number == 2:
        return json.dumps({
            "number": number,
            "is_prime": True,
            "reason": "2 is the only even prime number"
        }, indent=2)
    
    if number % 2 == 0:
        return json.dumps({
            "number": number,
            "is_prime": False,
            "reason": f"{number} is divisible by 2"
        }, indent=2)
    
    # Check odd divisors up to sqrt(number)
    i = 3
    while i * i <= number:
        if number % i == 0:
            return json.dumps({
                "number": number,
                "is_prime": False,
                "reason": f"{number} is divisible by {i}"
            }, indent=2)
        i += 2
    
    return json.dumps({
        "number": number,
        "is_prime": True,
        "reason": f"{number} has no divisors other than 1 and itself"
    }, indent=2)


# ---------------------------------------------------------------------------
# Text Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def text_transform(text: str, operation: str) -> str:
    """
    Transform text using various operations.
    
    Args:
        text: The input text to transform
        operation: One of: uppercase, lowercase, title, reverse, length
    
    Returns:
        The transformed text or error message
    """
    operations = {
        "uppercase": lambda t: t.upper(),
        "lowercase": lambda t: t.lower(),
        "title": lambda t: t.title(),
        "reverse": lambda t: t[::-1],
        "length": lambda t: f"Length: {len(t)} characters"
    }
    
    if operation not in operations:
        return f"Error: Unknown operation '{operation}'. Valid: {', '.join(operations.keys())}"
    
    return operations[operation](text)


@mcp.tool()
def word_count(text: str) -> str:
    """
    Count words, characters, lines, and sentences in text.
    
    Args:
        text: The text to analyze
    
    Returns:
        JSON string with statistics
    """
    lines = text.split('\n')
    words = text.split()
    sentences = text.replace('!', '.').replace('?', '.').split('.')
    sentences = [s for s in sentences if s.strip()]
    
    return json.dumps({
        "characters": len(text),
        "characters_no_spaces": len(text.replace(' ', '')),
        "words": len(words),
        "lines": len(lines),
        "sentences": len(sentences)
    }, indent=2)


@mcp.tool()
def encode_decode(text: str, operation: str, encoding: str = "base64") -> str:
    """
    Encode or decode text.
    
    Args:
        text: The text to encode/decode
        operation: Either "encode" or "decode"
        encoding: The encoding type (currently only "base64" supported)
    
    Returns:
        The encoded/decoded text or error message
    """
    if encoding != "base64":
        return f"Error: Only 'base64' encoding is currently supported"
    
    try:
        if operation == "encode":
            result = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            return f"Encoded (base64): {result}"
        elif operation == "decode":
            result = base64.b64decode(text.encode('utf-8')).decode('utf-8')
            return f"Decoded: {result}"
        else:
            return f"Error: operation must be 'encode' or 'decode'"
    except Exception as e:
        return f"Error: {str(e)}"


# ---------------------------------------------------------------------------
# Date/Time Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def current_time(timezone: str = "UTC", format: str = "iso") -> str:
    """
    Get the current date and time.
    
    Args:
        timezone: Currently only "UTC" supported
        format: Output format - "iso", "readable", or "unix"
    
    Returns:
        The current time in the specified format
    """
    now = datetime.utcnow()
    
    formats = {
        "iso": lambda: now.isoformat() + "Z",
        "readable": lambda: now.strftime("%B %d, %Y at %I:%M:%S %p UTC"),
        "unix": lambda: str(int(now.timestamp()))
    }
    
    if format not in formats:
        return f"Error: format must be one of: {', '.join(formats.keys())}"
    
    return json.dumps({
        "timezone": timezone,
        "format": format,
        "time": formats[format]()
    }, indent=2)


@mcp.tool()
def date_diff(date1: str, date2: str) -> str:
    """
    Calculate the difference between two dates.
    
    Args:
        date1: First date in ISO format (YYYY-MM-DD)
        date2: Second date in ISO format (YYYY-MM-DD)
    
    Returns:
        JSON with the difference in days
    """
    try:
        d1 = datetime.fromisoformat(date1)
        d2 = datetime.fromisoformat(date2)
        diff = abs((d2 - d1).days)
        
        return json.dumps({
            "date1": date1,
            "date2": date2,
            "difference_days": diff,
            "difference_weeks": round(diff / 7, 2),
            "difference_months": round(diff / 30.44, 2)
        }, indent=2)
    except Exception as e:
        return f"Error: {str(e)}. Please use ISO format: YYYY-MM-DD"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Math & Text Utilities MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="streamable-http",
        help="Transport mode (default: streamable-http)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for HTTP transports (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port for HTTP transports (default: 8001)",
    )
    args = parser.parse_args()

    if args.transport != "stdio":
        mcp.settings.host = args.host
        mcp.settings.port = args.port

        # When deployed behind a reverse proxy (e.g. Azure Container Apps),
        # the Host header won't match localhost. Disable DNS rebinding protection
        # so the server accepts requests from any host.
        from mcp.server.transport_security import TransportSecuritySettings
        mcp.settings.transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
        )

        print(
            f"▶️  Starting MCP server over {args.transport} at http://{args.host}:{args.port}/mcp",
            file=sys.stderr,
            flush=True,
        )
    else:
        print(
            "⚠️  Starting in stdio mode — waiting for MCP client connection...",
            file=sys.stderr,
            flush=True,
        )

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
