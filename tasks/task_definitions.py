"""
Task definitions for structured output benchmark.

Each task has:
- name: task identifier
- prompt: the actual prompt to send to the model
- schema: the expected JSON schema for valid output
- evaluator: how to check correctness
"""

import json

# ============================================================
# TASK CATEGORY 1: Simple JSON Generation
# Generate a JSON object from a natural language description
# ============================================================

SIMPLE_JSON_TASKS = [
    {
        "id": "json_simple_person",
        "category": "json_generation",
        "difficulty": "easy",
        "prompt": "Generate a JSON object for a person with the following fields: name (string), age (number), email (string), and city (string). Use realistic values.",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
                "email": {"type": "string"},
                "city": {"type": "string"}
            },
            "required": ["name", "age", "email", "city"],
            "additionalProperties": False
        }
    },
    {
        "id": "json_simple_product",
        "category": "json_generation",
        "difficulty": "easy",
        "prompt": "Create a JSON object for a product listing with: product_name (string), price (number), in_stock (boolean), and category (string).",
        "schema": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string"},
                "price": {"type": "number"},
                "in_stock": {"type": "boolean"},
                "category": {"type": "string"}
            },
            "required": ["product_name", "price", "in_stock", "category"],
            "additionalProperties": False
        }
    },
    {
        "id": "json_nested_address",
        "category": "json_generation",
        "difficulty": "medium",
        "prompt": "Generate a JSON object for a user profile. It must have: name (string), age (number), and address (object with street, city, state, zip).",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                        "state": {"type": "string"},
                        "zip": {"type": "string"}
                    },
                    "required": ["street", "city", "state", "zip"],
                    "additionalProperties": False
                }
            },
            "required": ["name", "age", "address"],
            "additionalProperties": False
        }
    },
    {
        "id": "json_array_orders",
        "category": "json_generation",
        "difficulty": "medium",
        "prompt": "Create a JSON array containing 3 order objects. Each order should have: order_id (string), items (array of strings), total (number), and status (string that must be one of: pending, shipped, delivered).",
        "schema": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "total": {"type": "number"},
                    "status": {"type": "string", "enum": ["pending", "shipped", "delivered"]}
                },
                "required": ["order_id", "items", "total", "status"],
                "additionalProperties": False
            },
            "minItems": 3,
            "maxItems": 3
        }
    },
    {
        "id": "json_complex_api",
        "category": "json_generation",
        "difficulty": "hard",
        "prompt": "Generate a JSON object representing an API response. It should have: status (number), message (string), data (object with users array, where each user has id, name, email, role where role is one of admin/user/moderator), and metadata (object with total_count, page, per_page).",
        "schema": {
            "type": "object",
            "properties": {
                "status": {"type": "number"},
                "message": {"type": "string"},
                "data": {
                    "type": "object",
                    "properties": {
                        "users": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "number"},
                                    "name": {"type": "string"},
                                    "email": {"type": "string"},
                                    "role": {"type": "string", "enum": ["admin", "user", "moderator"]}
                                },
                                "required": ["id", "name", "email", "role"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["users"],
                    "additionalProperties": False
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "total_count": {"type": "number"},
                        "page": {"type": "number"},
                        "per_page": {"type": "number"}
                    },
                    "required": ["total_count", "page", "per_page"],
                    "additionalProperties": False
                }
            },
            "required": ["status", "message", "data", "metadata"],
            "additionalProperties": False
        }
    }
]

# ============================================================
# TASK CATEGORY 2: Schema Adherence
# Given a schema, generate output that matches it
# ============================================================

SCHEMA_ADHERENCE_TASKS = [
    {
        "id": "schema_weather",
        "category": "schema_adherence",
        "difficulty": "easy",
        "prompt": "Output a valid JSON object matching this exact schema. Generate realistic weather data:\n\nSchema:\n{\"type\":\"object\",\"properties\":{\"location\":{\"type\":\"string\"},\"temperature\":{\"type\":\"number\"},\"unit\":{\"type\":\"string\",\"enum\":[\"celsius\",\"fahrenheit\"]},\"conditions\":{\"type\":\"string\"},\"humidity\":{\"type\":\"number\",\"minimum\":0,\"maximum\":100}},\"required\":[\"location\",\"temperature\",\"unit\",\"conditions\",\"humidity\"],\"additionalProperties\":false}",
        "schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "temperature": {"type": "number"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                "conditions": {"type": "string"},
                "humidity": {"type": "number", "minimum": 0, "maximum": 100}
            },
            "required": ["location", "temperature", "unit", "conditions", "humidity"],
            "additionalProperties": False
        }
    },
    {
        "id": "schema_database_record",
        "category": "schema_adherence",
        "difficulty": "medium",
        "prompt": "Generate a JSON object matching this schema representing a database record. Fill in realistic values:\n\nSchema:\n{\"type\":\"object\",\"properties\":{\"id\":{\"type\":\"string\",\"pattern\":\"^[a-f0-9]{8}$\"},\"created_at\":{\"type\":\"string\",\"format\":\"date-time\"},\"type\":{\"type\":\"string\",\"enum\":[\"customer\",\"vendor\",\"employee\"]},\"active\":{\"type\":\"boolean\"},\"tags\":{\"type\":\"array\",\"items\":{\"type\":\"string\"},\"maxItems\":5}},\"required\":[\"id\",\"created_at\",\"type\",\"active\",\"tags\"],\"additionalProperties\":false}",
        "schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "pattern": "^[a-f0-9]{8}$"},
                "created_at": {"type": "string", "format": "date-time"},
                "type": {"type": "string", "enum": ["customer", "vendor", "employee"]},
                "active": {"type": "boolean"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 5
                }
            },
            "required": ["id", "created_at", "type", "active", "tags"],
            "additionalProperties": False
        }
    },
    {
        "id": "schema_config_file",
        "category": "schema_adherence",
        "difficulty": "hard",
        "prompt": "Generate a valid JSON configuration object matching this schema for a web server config:\n\nSchema:\n{\"type\":\"object\",\"properties\":{\"server\":{\"type\":\"object\",\"properties\":{\"host\":{\"type\":\"string\"},\"port\":{\"type\":\"integer\",\"minimum\":1,\"maximum\":65535},\"ssl\":{\"type\":\"object\",\"properties\":{\"enabled\":{\"type\":\"boolean\"},\"cert_path\":{\"type\":\"string\"},\"key_path\":{\"type\":\"string\"}},\"required\":[\"enabled\"]}},\"required\":[\"host\",\"port\",\"ssl\"]},\"logging\":{\"type\":\"object\",\"properties\":{\"level\":{\"type\":\"string\",\"enum\":[\"debug\",\"info\",\"warn\",\"error\"]},\"file\":{\"type\":\"string\"},\"rotate\":{\"type\":\"boolean\"}},\"required\":[\"level\"]},\"cors\":{\"type\":\"object\",\"properties\":{\"enabled\":{\"type\":\"boolean\"},\"origins\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}},\"methods\":{\"type\":\"array\",\"items\":{\"type\":\"string\",\"enum\":[\"GET\",\"POST\",\"PUT\",\"DELETE\",\"PATCH\"]}}},\"required\":[\"enabled\"]}},\"required\":[\"server\",\"logging\",\"cors\"],\"additionalProperties\":false}",
        "schema": {
            "type": "object",
            "properties": {
                "server": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "integer"},
                        "ssl": {
                            "type": "object",
                            "properties": {
                                "enabled": {"type": "boolean"},
                                "cert_path": {"type": "string"},
                                "key_path": {"type": "string"}
                            },
                            "required": ["enabled"],
                            "additionalProperties": False
                        }
                    },
                    "required": ["host", "port", "ssl"],
                    "additionalProperties": False
                },
                "logging": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string", "enum": ["debug", "info", "warn", "error"]},
                        "file": {"type": "string"},
                        "rotate": {"type": "boolean"}
                    },
                    "required": ["level"],
                    "additionalProperties": False
                },
                "cors": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "origins": {"type": "array", "items": {"type": "string"}},
                        "methods": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]}
                        }
                    },
                    "required": ["enabled"],
                    "additionalProperties": False
                }
            },
            "required": ["server", "logging", "cors"],
            "additionalProperties": False
        }
    }
]

# ============================================================
# TASK CATEGORY 3: Function Calling Format
# Generate tool/function call format (OpenAI-style)
# ============================================================

FUNCTION_CALLING_TASKS = [
    {
        "id": "funcall_get_weather",
        "category": "function_calling",
        "difficulty": "easy",
        "prompt": "You are a helpful assistant with access to the following function:\n\n{\"name\": \"get_weather\", \"description\": \"Get current weather for a location\", \"parameters\": {\"type\": \"object\", \"properties\": {\"location\": {\"type\": \"string\", \"description\": \"City name\"}, \"unit\": {\"type\": \"string\", \"enum\": [\"celsius\", \"fahrenheit\"]}}, \"required\": [\"location\"]}}\n\nThe user asks: \"What's the weather like in San Francisco?\"\n\nRespond with a function call in JSON format using: {\"name\": \"...\", \"arguments\": {...}}",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "arguments": {"type": "object", "additionalProperties": True}
            },
            "required": ["name", "arguments"],
            "additionalProperties": False
        },
        "expected_function": "get_weather",
        "expected_params_keys": ["location"]
    },
    {
        "id": "funcall_search_multi",
        "category": "function_calling",
        "difficulty": "medium",
        "prompt": "You are a helpful assistant with access to the following functions:\n\n1. {\"name\": \"search_web\", \"description\": \"Search the web for information\", \"parameters\": {\"type\": \"object\", \"properties\": {\"query\": {\"type\": \"string\"}, \"num_results\": {\"type\": \"integer\", \"default\": 10}}, \"required\": [\"query\"]}}\n\n2. {\"name\": \"send_email\", \"description\": \"Send an email\", \"parameters\": {\"type\": \"object\", \"properties\": {\"to\": {\"type\": \"string\"}, \"subject\": {\"type\": \"string\"}, \"body\": {\"type\": \"string\"}}, \"required\": [\"to\", \"subject\", \"body\"]}}\n\nThe user asks: \"Search for the best restaurants in NYC and email the results to john@example.com\"\n\nRespond with the appropriate function call(s) in JSON format. If multiple calls are needed, use an array. Use the format: {\"name\": \"...\", \"arguments\": {...}}",
        "schema": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "arguments": {"type": "object", "additionalProperties": True}
                },
                "required": ["name", "arguments"],
                "additionalProperties": False
            },
            "minItems": 1,
            "maxItems": 2
        },
        "expected_functions": ["search_web", "send_email"],
        "expected_params_keys": [["query", "num_results"], ["to", "subject", "body"]]
    },
    {
        "id": "funcall_database_query",
        "category": "function_calling",
        "difficulty": "hard",
        "prompt": "You are a helpful assistant with access to the following function:\n\n{\"name\": \"query_database\", \"description\": \"Execute a SQL query on the database\", \"parameters\": {\"type\": \"object\", \"properties\": {\"query\": {\"type\": \"string\", \"description\": \"SQL query to execute\"}, \"database\": {\"type\": \"string\", \"enum\": [\"production\", \"staging\", \"analytics\"]}, \"limit\": {\"type\": \"integer\", \"default\": 100, \"maximum\": 1000}, \"format\": {\"type\": \"string\", \"enum\": [\"json\", \"csv\"], \"default\": \"json\"}}, \"required\": [\"query\", \"database\"]}}\n\nThe user asks: \"Get me the top 50 customers by revenue from the production database in CSV format\"\n\nRespond with a function call in JSON format using: {\"name\": \"...\", \"arguments\": {...}}",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "arguments": {"type": "object", "additionalProperties": True}
            },
            "required": ["name", "arguments"],
            "additionalProperties": False
        },
        "expected_function": "query_database",
        "expected_params_keys": ["query", "database", "limit", "format"]
    }
]

# ============================================================
# TASK CATEGORY 4: Key-Value Extraction
# Extract structured info from unstructured text
# ============================================================

EXTRACTION_TASKS = [
    {
        "id": "extract_business_card",
        "category": "extraction",
        "difficulty": "easy",
        "prompt": "Extract the contact information from the following text into a JSON object with fields: name, phone, email, company, title.\n\nText: \"John Smith is a Senior Software Engineer at TechCorp Inc. You can reach him at john.smith@techcorp.com or call (555) 123-4567.\"",
        "expected_values": {
            "name": "John Smith",
            "phone": "(555) 123-4567",
            "email": "john.smith@techcorp.com",
            "company": "TechCorp Inc",
            "title": "Senior Software Engineer"
        },
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "phone": {"type": "string"},
                "email": {"type": "string"},
                "company": {"type": "string"},
                "title": {"type": "string"}
            },
            "required": ["name", "phone", "email", "company", "title"],
            "additionalProperties": False
        }
    },
    {
        "id": "extract_receipt",
        "category": "extraction",
        "difficulty": "medium",
        "prompt": "Extract receipt information from the following text into a JSON object with: store_name, date, items (array of objects with name and price), subtotal, tax, total.\n\nText: \"WALMART SUPERCENTER\nDate: 03/15/2026\nMilk 2% 1gal ........... $4.98\nSourdough Bread ........ $3.49\nOrganic Eggs 12ct ...... $5.99\nAvocados 3ct ........... $4.47\nSubtotal: $18.93\nTax (8.25%): $1.56\nTOTAL: $20.49\"",
        "expected_values": {
            "store_name": "WALMART SUPERCENTER",
            "date": "03/15/2026",
            "items": [
                {"name": "Milk 2% 1gal", "price": 4.98},
                {"name": "Sourdough Bread", "price": 3.49},
                {"name": "Organic Eggs 12ct", "price": 5.99},
                {"name": "Avocados 3ct", "price": 4.47}
            ],
            "subtotal": 18.93,
            "tax": 1.56,
            "total": 20.49
        },
        "schema": {
            "type": "object",
            "properties": {
                "store_name": {"type": "string"},
                "date": {"type": "string"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "price": {"type": "number"}
                        },
                        "required": ["name", "price"],
                        "additionalProperties": False
                    }
                },
                "subtotal": {"type": "number"},
                "tax": {"type": "number"},
                "total": {"type": "number"}
            },
            "required": ["store_name", "date", "items", "subtotal", "tax", "total"]
        }
    },
    {
        "id": "extract_api_log",
        "category": "extraction",
        "difficulty": "hard",
        "prompt": "Extract structured data from the following API log entry into JSON with: timestamp, method, path, status_code, response_time_ms, error (null if no error), and headers (object with content-type, x-request-id, user-agent).\n\nText: '[2026-05-05T10:23:45.678Z] POST /api/v2/users/authenticate -> 401 (145.3ms) | Headers: {\"content-type\": \"application/json\", \"x-request-id\": \"req-abc123def456\", \"user-agent\": \"MobileApp/3.2.1 (iOS 17.4)\"} | Error: Invalid credentials - email not verified'",
        "schema": {
            "type": "object",
            "properties": {
                "timestamp": {"type": "string"},
                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                "path": {"type": "string"},
                "status_code": {"type": "number"},
                "response_time_ms": {"type": "number"},
                "error": {"oneOf": [{"type": "string"}, {"type": "null"}]},
                "headers": {
                    "type": "object",
                    "properties": {
                        "content-type": {"type": "string"},
                        "x-request-id": {"type": "string"},
                        "user-agent": {"type": "string"}
                    },
                    "required": ["content-type", "x-request-id", "user-agent"],
                    "additionalProperties": False
                }
            },
            "required": ["timestamp", "method", "path", "status_code", "response_time_ms", "error", "headers"]
        }
    }
]

# ============================================================
# SYSTEM PROMPTS for different conditions
# ============================================================

SYSTEM_PROMPTS = {
    "basic": "You are a helpful assistant. Always respond with valid JSON. Do not include any text outside the JSON.",
    
    "structured": "You are a helpful assistant. When asked to generate structured output, you MUST respond with ONLY valid JSON. No markdown, no code blocks, no explanation - just the raw JSON. Ensure all required fields are present and types are correct.",
    
    "schema_given": "You are a helpful assistant. You will be given a JSON schema. Generate output that EXACTLY matches the schema. Respond with ONLY the JSON, nothing else. No markdown code fences. Validate your output mentally before responding."
}


def get_all_tasks():
    """Return all tasks combined."""
    return SIMPLE_JSON_TASKS + SCHEMA_ADHERENCE_TASKS + FUNCTION_CALLING_TASKS + EXTRACTION_TASKS


def get_tasks_by_category(category):
    """Return tasks filtered by category."""
    all_tasks = get_all_tasks()
    return [t for t in all_tasks if t["category"] == category]


def get_tasks_by_difficulty(difficulty):
    """Return tasks filtered by difficulty."""
    all_tasks = get_all_tasks()
    return [t for t in all_tasks if t.get("difficulty") == difficulty]
