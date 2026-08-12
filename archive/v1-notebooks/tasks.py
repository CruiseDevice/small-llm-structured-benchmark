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
