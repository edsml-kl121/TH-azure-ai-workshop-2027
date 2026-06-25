# Math & Text Utilities MCP Server

MCP server providing mathematical calculations and text processing utilities.

## Features

### Math Tools
- `calculate(expression)` - Evaluate mathematical expressions safely
- `fibonacci(n)` - Generate Fibonacci sequence (up to 50 numbers)
- `is_prime(number)` - Check if a number is prime

### Text Tools
- `text_transform(text, operation)` - Transform text (uppercase, lowercase, title, reverse, length)
- `word_count(text)` - Count words, characters, lines, and sentences
- `encode_decode(text, operation, encoding)` - Encode/decode text (base64)

### Date/Time Tools
- `current_time(timezone, format)` - Get current time in various formats
- `date_diff(date1, date2)` - Calculate difference between two dates

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Local Development
```bash
# HTTP mode (recommended for testing)
python server.py --transport streamable-http --host 127.0.0.1 --port 8001

# stdio mode (for MCP client integration)
python server.py --transport stdio
```

### Docker

Build the image:
```bash
docker build -t math-text-mcp-server .
```

Run the container:
```bash
docker run -p 8001:8001 math-text-mcp-server
```

## API Endpoint

When running in HTTP mode, the server is available at:
```
http://127.0.0.1:8001/mcp
```

## Examples

### Calculate
```python
calculate("2 + 2")  # Returns: "2 + 2 = 4"
```

### Fibonacci
```python
fibonacci(10)  # Returns JSON with first 10 Fibonacci numbers
```

### Is Prime
```python
is_prime(17)  # Returns JSON with prime check result
```

### Text Transform
```python
text_transform("hello world", "uppercase")  # Returns: "HELLO WORLD"
```

### Word Count
```python
word_count("The quick brown fox")  # Returns JSON with statistics
```
