# Semantic Failure Catalog — For Taxonomy Tagging

**Instructions:** Read each failure. For each one, assign ONE label:
- `type_coercion` — wrong JSON type (number stored as string, missing `$`, etc.)
- `comprehension` — model didn't understand what the task was asking
- `generation` — model understood the task but couldn't produce the content

Write your label in the `YOUR LABEL:` line under each failure.
There are no wrong answers. Trust your judgment.

---

## Failure #1 — Qwen-0.6B / native / `extract_business_card`
`content_accuracy: 0.9` | `difficulty: easy`

**TASK:** Extract the contact information from the following text into a JSON object with fields: name, phone, email, company, title.

Text: "John Smith is a Senior Software Engineer at TechCorp Inc. You can reach him at john.smith@techcorp.com or call (555) 123-4567."

**EXPECTED:**
```
{
  "name": "John Smith",
  "phone": "(555) 123-4567",
  "email": "john.smith@techcorp.com",
  "company": "TechCorp Inc",
  "title": "Senior Software Engineer"
}
```

**MODEL OUTPUT:**
```
{'name': 'John Smith', 'phone': '(555) 123-4567', 'email': 'john.smith@techcorp.com', 'company': 'TechCorp Inc.', 'title': 'Senior Software Engineer'}
```

**YOUR LABEL:** `generation`

**Why (one sentence):**
I think the model is supposed to use double quotes for key and value pair in the JSON object, but it used single quote
---

## Failure #2 — Qwen-0.6B / outlines / `extract_business_card`
`content_accuracy: 0.7` | `difficulty: easy`

**TASK:** Extract the contact information from the following text into a JSON object with fields: name, phone, email, company, title.

Text: "John Smith is a Senior Software Engineer at TechCorp Inc. You can reach him at john.smith@techcorp.com or call (555) 123-4567."

**EXPECTED:**
```
{
  "name": "John Smith",
  "phone": "(555) 123-4567",
  "email": "john.smith@techcorp.com",
  "company": "TechCorp Inc",
  "title": "Senior Software Engineer"
}
```

**MODEL OUTPUT:**
```
{'name': 'John Smith', 'phone': '555-123-4567', 'email': 'john.smith@techcorp.com', 'company': 'TechCorp Inc.', 'title': 'Senior Software Engineer'}
```

**YOUR LABEL:** `generation`

**Why (one sentence):**
the model used single quotes instead of double quotes in JSON object. Also for key phone, it did produce the output in the expected format.
---

## Failure #3 — Qwen-0.6B / xgrammar / `extract_business_card`
`content_accuracy: 0.9` | `difficulty: easy`

**TASK:** Extract the contact information from the following text into a JSON object with fields: name, phone, email, company, title.

Text: "John Smith is a Senior Software Engineer at TechCorp Inc. You can reach him at john.smith@techcorp.com or call (555) 123-4567."

**EXPECTED:**
```
{
  "name": "John Smith",
  "phone": "(555) 123-4567",
  "email": "john.smith@techcorp.com",
  "company": "TechCorp Inc",
  "title": "Senior Software Engineer"
}
```

**MODEL OUTPUT:**
```
{'name': 'John Smith', 'phone': '(555) 123-4567', 'email': 'john.smith@techcorp.com', 'company': 'TechCorp Inc.', 'title': 'Senior Software Engineer'}
```

**YOUR LABEL:** `generation`

**Why (one sentence):**
Because the model didn't generate the output in the expected format. The model outputted single quotes instead of double quotes in the JSON object.
---

## Failure #4 — Qwen-0.6B / native / `funcall_search_multi`
`content_accuracy: 0.2` | `difficulty: medium`

**TASK:** The user asks: "Search for the best restaurants in NYC and email the results to john@example.com"

Respond with the appropriate function call(s) in JSON format. If multiple calls are needed, use an array. Use the format: {"name": "...", "arguments": {...}}

**EXPECTED:**
```
[
  "search_web",
  "send_email"
]
```

**MODEL OUTPUT:**
```
[{'name': 'search_web', 'arguments': {'query': 'best restaurants in NYC', 'num_results': 10}}]
```

**YOUR LABEL:** `comprehension`

**Why (one sentence):**
Instead of two calls, model only emits one call
---

## Failure #5 — Qwen-0.6B / outlines / `funcall_search_multi`
`content_accuracy: 0.2` | `difficulty: medium`

**TASK:** The user asks: "Search for the best restaurants in NYC and email the results to john@example.com"

Respond with the appropriate function call(s) in JSON format. If multiple calls are needed, use an array. Use the format: {"name": "...", "arguments": {...}}

**EXPECTED:**
```
[
  "search_web",
  "send_email"
]
```

**MODEL OUTPUT:**
```
[{'name': 'search_web', 'arguments': {'query': 'best restaurants in NYC', 'num_results': 10}}]
```

**YOUR LABEL:** `comprehension`

**Why (one sentence):**
Instead of two calls, model only emits one call
---

## Failure #6 — Qwen-0.6B / xgrammar / `funcall_search_multi`
`content_accuracy: 0.2` | `difficulty: medium`

**TASK:** The user asks: "Search for the best restaurants in NYC and email the results to john@example.com"

Respond with the appropriate function call(s) in JSON format. If multiple calls are needed, use an array. Use the format: {"name": "...", "arguments": {...}}

**EXPECTED:**
```
[
  "search_web",
  "send_email"
]
```

**MODEL OUTPUT:**
```
[{'name': 'search_web', 'arguments': {'query': 'best restaurants in NYC', 'num_results': 5}}]
```

**YOUR LABEL:** `comprehension`

**Why (one sentence):**
Instead of two calls, model only emits one call
---

## Failure #7 — Llama-1B / native / `extract_business_card`
`content_accuracy: 0.7` | `difficulty: easy`

**TASK:** Extract the contact information from the following text into a JSON object with fields: name, phone, email, company, title.

Text: "John Smith is a Senior Software Engineer at TechCorp Inc. You can reach him at john.smith@techcorp.com or call (555) 123-4567."

**EXPECTED:**
```
{
  "name": "John Smith",
  "phone": "(555) 123-4567",
  "email": "john.smith@techcorp.com",
  "company": "TechCorp Inc",
  "title": "Senior Software Engineer"
}
```

**MODEL OUTPUT:**
```
{'name': 'John Smith', 'phone': '555 123 4567', 'email': 'john.smith@techcorp.com', 'company': 'TechCorp Inc.', 'title': 'Senior Software Engineer'}
```

**YOUR LABEL:** `generation`

**Why (one sentence):**
Phone number not correctly formatted as per expected json object
---

## Failure #8 — Llama-1B / outlines / `extract_business_card`
`content_accuracy: 0.7` | `difficulty: easy`

**TASK:** Extract the contact information from the following text into a JSON object with fields: name, phone, email, company, title.

Text: "John Smith is a Senior Software Engineer at TechCorp Inc. You can reach him at john.smith@techcorp.com or call (555) 123-4567."

**EXPECTED:**
```
{
  "name": "John Smith",
  "phone": "(555) 123-4567",
  "email": "john.smith@techcorp.com",
  "company": "TechCorp Inc",
  "title": "Senior Software Engineer"
}
```

**MODEL OUTPUT:**
```
{'name': 'John Smith', 'phone': '555-123-4567', 'email': 'john.smith@techcorp.com', 'company': 'TechCorp Inc.', 'title': 'Senior Software Engineer'}
```

**YOUR LABEL:** `generation`

**Why (one sentence):**
Phone number not correctly formatted as per expected json object
---

## Failure #9 — Llama-1B / xgrammar / `extract_business_card`
`content_accuracy: 0.7` | `difficulty: easy`

**TASK:** Extract the contact information from the following text into a JSON object with fields: name, phone, email, company, title.

Text: "John Smith is a Senior Software Engineer at TechCorp Inc. You can reach him at john.smith@techcorp.com or call (555) 123-4567."

**EXPECTED:**
```
{
  "name": "John Smith",
  "phone": "(555) 123-4567",
  "email": "john.smith@techcorp.com",
  "company": "TechCorp Inc",
  "title": "Senior Software Engineer"
}
```

**MODEL OUTPUT:**
```
{'name': 'John Smith', 'phone': '555 123 4567', 'email': 'john.smith@techcorp.com', 'company': 'TechCorp Inc.', 'title': 'Senior Software Engineer'}
```

**YOUR LABEL:** `generation`

**Why (one sentence):**
Phone number not correctly formatted as per expected json object
---

## Failure #10 — Llama-1B / outlines / `funcall_search_multi`
`content_accuracy: 0.2` | `difficulty: medium`

**TASK:** The user asks: "Search for the best restaurants in NYC and email the results to john@example.com"

Respond with the appropriate function call(s) in JSON format. If multiple calls are needed, use an array. Use the format: {"name": "...", "arguments": {...}}

**EXPECTED:**
```
[
  "search_web",
  "send_email"
]
```

**MODEL OUTPUT:**
```
[{'name': 'search_web', 'arguments': {'query': 'restaurants in NYC', 'num_results': 10}}]
```

**YOUR LABEL:** `comprehension`

**Why (one sentence):**
Model emit only one tool call instead of two
---

## Failure #11 — Llama-3B / native / `extract_business_card`
`content_accuracy: 0.9` | `difficulty: easy`

**TASK:** Extract the contact information from the following text into a JSON object with fields: name, phone, email, company, title.

Text: "John Smith is a Senior Software Engineer at TechCorp Inc. You can reach him at john.smith@techcorp.com or call (555) 123-4567."

**EXPECTED:**
```
{
  "name": "John Smith",
  "phone": "(555) 123-4567",
  "email": "john.smith@techcorp.com",
  "company": "TechCorp Inc",
  "title": "Senior Software Engineer"
}
```

**MODEL OUTPUT:**
```
{'name': 'John Smith', 'phone': '(555) 123-4567', 'email': 'john.smith@techcorp.com', 'company': 'TechCorp Inc.', 'title': 'Senior Software Engineer'}
```

**YOUR LABEL:** `generation`

**Why (one sentence):**
single quote in json object instead of double quote
---

## Failure #12 — Llama-3B / xgrammar / `extract_business_card`
`content_accuracy: 0.9` | `difficulty: easy`

**TASK:** Extract the contact information from the following text into a JSON object with fields: name, phone, email, company, title.

Text: "John Smith is a Senior Software Engineer at TechCorp Inc. You can reach him at john.smith@techcorp.com or call (555) 123-4567."

**EXPECTED:**
```
{
  "name": "John Smith",
  "phone": "(555) 123-4567",
  "email": "john.smith@techcorp.com",
  "company": "TechCorp Inc",
  "title": "Senior Software Engineer"
}
```

**MODEL OUTPUT:**
```
{'name': 'John Smith', 'phone': '(555) 123-4567', 'email': 'john.smith@techcorp.com', 'company': 'TechCorp Inc.', 'title': 'Senior Software Engineer'}
```

**YOUR LABEL:** `generation`

**Why (one sentence):**
single quote in json object instead of double quote
---

## Failure #13 — Llama-3B / native / `funcall_database_query`
`content_accuracy: 0.875` | `difficulty: hard`

**TASK:** The user asks: "Get me the top 50 customers by revenue from the production database in CSV format"

Respond with a function call in JSON format using: {"name": "...", "arguments": {...}}

**EXPECTED:**
```
[
  "query",
  "database",
  "limit",
  "format"
]
```

**MODEL OUTPUT:**
```
{'name': 'query_database', 'arguments': {'query': 'SELECT customer_id, revenue FROM customers ORDER BY revenue DESC LIMIT 50', 'database': 'production', 'format': 'csv'}}
```

**YOUR LABEL:** `comprehension`

**Why (one sentence):**
missing limit in the model output
---

## Failure #14 — Llama-3B / outlines / `funcall_database_query`
`content_accuracy: 0.875` | `difficulty: hard`

**TASK:** The user asks: "Get me the top 50 customers by revenue from the production database in CSV format"

Respond with a function call in JSON format using: {"name": "...", "arguments": {...}}

**EXPECTED:**
```
[
  "query",
  "database",
  "limit",
  "format"
]
```

**MODEL OUTPUT:**
```
{'name': 'query_database', 'arguments': {'query': 'SELECT customer_id, revenue FROM customers ORDER BY revenue DESC LIMIT 50', 'database': 'production', 'format': 'csv'}}
```

**YOUR LABEL:** `comprehension`

**Why (one sentence):**
missing limit in the model output
---

## Failure #15 — Llama-3B / xgrammar / `funcall_database_query`
`content_accuracy: 0.875` | `difficulty: hard`

**TASK:** The user asks: "Get me the top 50 customers by revenue from the production database in CSV format"

Respond with a function call in JSON format using: {"name": "...", "arguments": {...}}

**EXPECTED:**
```
[
  "query",
  "database",
  "limit",
  "format"
]
```

**MODEL OUTPUT:**
```
{'name': 'query_database', 'arguments': {'query': 'SELECT customer_id, revenue FROM customers ORDER BY revenue DESC LIMIT 50', 'database': 'production', 'format': 'csv'}}
```

**YOUR LABEL:** `comprehension`

**Why (one sentence):**
missing limit
---

## Failure #16 — Phi-4-mini / native / `extract_business_card`
`content_accuracy: 0.9` | `difficulty: easy`

**TASK:** Extract the contact information from the following text into a JSON object with fields: name, phone, email, company, title.

Text: "John Smith is a Senior Software Engineer at TechCorp Inc. You can reach him at john.smith@techcorp.com or call (555) 123-4567."

**EXPECTED:**
```
{
  "name": "John Smith",
  "phone": "(555) 123-4567",
  "email": "john.smith@techcorp.com",
  "company": "TechCorp Inc",
  "title": "Senior Software Engineer"
}
```

**MODEL OUTPUT:**
```
{'name': 'John Smith', 'phone': '(555) 123-4567', 'email': 'john.smith@techcorp.com', 'company': 'TechCorp Inc.', 'title': 'Senior Software Engineer'}
```

**YOUR LABEL:** `generation`

**Why (one sentence):**
single quotes instead of double quotes
---

## Failure #17 — Phi-4-mini / outlines / `extract_business_card`
`content_accuracy: 0.9` | `difficulty: easy`

**TASK:** Extract the contact information from the following text into a JSON object with fields: name, phone, email, company, title.

Text: "John Smith is a Senior Software Engineer at TechCorp Inc. You can reach him at john.smith@techcorp.com or call (555) 123-4567."

**EXPECTED:**
```
{
  "name": "John Smith",
  "phone": "(555) 123-4567",
  "email": "john.smith@techcorp.com",
  "company": "TechCorp Inc",
  "title": "Senior Software Engineer"
}
```

**MODEL OUTPUT:**
```
{'name': 'John Smith', 'phone': '(555) 123-4567', 'email': 'john.smith@techcorp.com', 'company': 'TechCorp Inc.', 'title': 'Senior Software Engineer'}
```

**YOUR LABEL:** `generation`

**Why (one sentence):**
single quotes instead of double quotes
---

## Failure #18 — Phi-4-mini / xgrammar / `extract_business_card`
`content_accuracy: 0.9` | `difficulty: easy`

**TASK:** Extract the contact information from the following text into a JSON object with fields: name, phone, email, company, title.

Text: "John Smith is a Senior Software Engineer at TechCorp Inc. You can reach him at john.smith@techcorp.com or call (555) 123-4567."

**EXPECTED:**
```
{
  "name": "John Smith",
  "phone": "(555) 123-4567",
  "email": "john.smith@techcorp.com",
  "company": "TechCorp Inc",
  "title": "Senior Software Engineer"
}
```

**MODEL OUTPUT:**
```
{'name': 'John Smith', 'phone': '(555) 123-4567', 'email': 'john.smith@techcorp.com', 'company': 'TechCorp Inc.', 'title': 'Senior Software Engineer'}
```

**YOUR LABEL:** `generation`

**Why (one sentence):**
single quotes instead of double quotes
---

## Failure #19 — Phi-4-mini / outlines / `extract_receipt`
`content_accuracy: 0.99` | `difficulty: medium`

**TASK:** Extract receipt information from the following text into a JSON object with: store_name, date, items (array of objects with name and price), subtotal, tax, total.

Text: "WALMART SUPERCENTER
Date: 03/15/2026
Milk 2% 1gal ........... $4.98
Sourdough Bread ........ $3.49
Organic Eggs 12ct ...... $5.99
Avocados 3ct ........... $4.47
Subtotal: $18.93
Tax (8.25%): $1.56
TOTAL: $20.49"

**EXPECTED:**
```
{
  "store_name": "WALMART SUPERCENTER",
  "date": "03/15/2026",
  "items": [
    {
      "name": "Milk 2% 1gal",
      "price": 4.98
    },
    {
      "name": "Sourdough Bread",
      "price": 3.49
    },
    {
      "name": "Organic Eggs 12ct",
      "price": 5.99
    },
    {
      "name": "Avocados 3ct",
      "price": 4.47
    }
  ],
  "subtotal": 18.93,
  "tax": 1.56,
  "total": 20.49
}
```

**MODEL OUTPUT:**
```
{'store_name': 'WALMART SUPERCENTER', 'date': '03/15/2026', 'items': [{'name': 'Milk 2%', 'price': 4.98}, {'name': 'Sourdough Bread', 'price': 3.49}, {'name': 'Organic Eggs 12ct', 'price': 5.99}, {'name': 'Avocados 3ct', 'price': 4.47}], 'subtotal': 18.93, 'tax': 1.56, 'total': 20.49}
```

**YOUR LABEL:** `generation`

**Why (one sentence):**
Truncated Milk 2%
---

## Failure #20 — Qwen-4B / native / `extract_business_card`
`content_accuracy: 0.9` | `difficulty: easy`

**TASK:** Extract the contact information from the following text into a JSON object with fields: name, phone, email, company, title.

Text: "John Smith is a Senior Software Engineer at TechCorp Inc. You can reach him at john.smith@techcorp.com or call (555) 123-4567."

**EXPECTED:**
```
{
  "name": "John Smith",
  "phone": "(555) 123-4567",
  "email": "john.smith@techcorp.com",
  "company": "TechCorp Inc",
  "title": "Senior Software Engineer"
}
```

**MODEL OUTPUT:**
```
{'name': 'John Smith', 'phone': '(555) 123-4567', 'email': 'john.smith@techcorp.com', 'company': 'TechCorp Inc.', 'title': 'Senior Software Engineer'}
```

**YOUR LABEL:** `generation`

**Why (one sentence):**

---

## Failure #21 — Qwen-4B / outlines / `extract_business_card`
`content_accuracy: 0.9` | `difficulty: easy`

**TASK:** Extract the contact information from the following text into a JSON object with fields: name, phone, email, company, title.

Text: "John Smith is a Senior Software Engineer at TechCorp Inc. You can reach him at john.smith@techcorp.com or call (555) 123-4567."

**EXPECTED:**
```
{
  "name": "John Smith",
  "phone": "(555) 123-4567",
  "email": "john.smith@techcorp.com",
  "company": "TechCorp Inc",
  "title": "Senior Software Engineer"
}
```

**MODEL OUTPUT:**
```
{'name': 'John Smith', 'phone': '(555) 123-4567', 'email': 'john.smith@techcorp.com', 'company': 'TechCorp Inc.', 'title': 'Senior Software Engineer'}
```

**YOUR LABEL:** `_________________`

**Why (one sentence):**

---

## Failure #22 — Qwen-4B / xgrammar / `extract_business_card`
`content_accuracy: 0.9` | `difficulty: easy`

**TASK:** Extract the contact information from the following text into a JSON object with fields: name, phone, email, company, title.

Text: "John Smith is a Senior Software Engineer at TechCorp Inc. You can reach him at john.smith@techcorp.com or call (555) 123-4567."

**EXPECTED:**
```
{
  "name": "John Smith",
  "phone": "(555) 123-4567",
  "email": "john.smith@techcorp.com",
  "company": "TechCorp Inc",
  "title": "Senior Software Engineer"
}
```

**MODEL OUTPUT:**
```
{'name': 'John Smith', 'phone': '(555) 123-4567', 'email': 'john.smith@techcorp.com', 'company': 'TechCorp Inc.', 'title': 'Senior Software Engineer'}
```

**YOUR LABEL:** `_________________`

**Why (one sentence):**

---

## Failure #23 — Qwen-4B / outlines / `extract_receipt`
`content_accuracy: 0.99` | `difficulty: medium`

**TASK:** Extract receipt information from the following text into a JSON object with: store_name, date, items (array of objects with name and price), subtotal, tax, total.

Text: "WALMART SUPERCENTER
Date: 03/15/2026
Milk 2% 1gal ........... $4.98
Sourdough Bread ........ $3.49
Organic Eggs 12ct ...... $5.99
Avocados 3ct ........... $4.47
Subtotal: $18.93
Tax (8.25%): $1.56
TOTAL: $20.49"

**EXPECTED:**
```
{
  "store_name": "WALMART SUPERCENTER",
  "date": "03/15/2026",
  "items": [
    {
      "name": "Milk 2% 1gal",
      "price": 4.98
    },
    {
      "name": "Sourdough Bread",
      "price": 3.49
    },
    {
      "name": "Organic Eggs 12ct",
      "price": 5.99
    },
    {
      "name": "Avocados 3ct",
      "price": 4.47
    }
  ],
  "subtotal": 18.93,
  "tax": 1.56,
  "total": 20.49
}
```

**MODEL OUTPUT:**
```
{'store_name': 'WALMART SUPERCENTER', 'date': '03/15/2026', 'items': [{'name': 'Milk 2%', 'price': 4.98}, {'name': 'Sourdough Bread', 'price': 3.49}, {'name': 'Organic Eggs 12ct', 'price': 5.99}, {'name': 'Avocados 3ct', 'price': 4.47}], 'subtotal': 18.93, 'tax': 1.56, 'total': 20.49}
```

**YOUR LABEL:** `_________________`

**Why (one sentence):**

---
