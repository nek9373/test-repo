# Documentation Guide

## Overview
This guide provides detailed instructions and templates for documenting different types of code structures, programming languages, and frameworks.

## Table of Contents
- [General Principles](#general-principles)
- [Language-Specific Documentation](#language-specific-documentation)
- [Framework-Specific Documentation](#framework-specific-documentation)
- [API Documentation](#api-documentation)
- [Component Documentation](#component-documentation)
- [Function Documentation](#function-documentation)
- [Class Documentation](#class-documentation)
- [Module Documentation](#module-documentation)
- [Testing Documentation](#testing-documentation)
- [Configuration Documentation](#configuration-documentation)

## General Principles

### Documentation Standards
1. **Clarity**: Use clear, concise language
2. **Completeness**: Cover all public interfaces
3. **Consistency**: Follow established patterns
4. **Currency**: Keep documentation up-to-date
5. **Examples**: Include practical examples

### Structure Template
```markdown
## [Function/Class/Component Name]

### Description
Brief description of what it does

### Parameters/Props
- `param1` (type, required/optional): Description
- `param2` (type, required/optional): Description

### Returns/Output
Description of what is returned

### Examples
```language
// Example usage
```

### Notes
Any additional notes or considerations
```

## Language-Specific Documentation

### JavaScript/TypeScript

#### Function Documentation
```javascript
/**
 * Calculates the total price including tax
 * 
 * @param {number} price - The base price
 * @param {number} taxRate - The tax rate (0.1 for 10%)
 * @param {Object} options - Additional options
 * @param {boolean} options.round - Whether to round the result
 * @returns {number} The total price including tax
 * 
 * @example
 * const total = calculateTotal(100, 0.1);
 * console.log(total); // 110
 * 
 * @example
 * const total = calculateTotal(99.99, 0.08, { round: true });
 * console.log(total); // 108
 */
function calculateTotal(price, taxRate, options = {}) {
  const total = price * (1 + taxRate);
  return options.round ? Math.round(total) : total;
}
```

#### Class Documentation
```javascript
/**
 * Represents a user account
 * 
 * @class
 * @param {string} username - The username
 * @param {string} email - The user's email
 * 
 * @example
 * const user = new User('john_doe', 'john@example.com');
 * user.login('password123');
 */
class User {
  /**
   * Create a new user
   * @param {string} username - The username
   * @param {string} email - The user's email
   */
  constructor(username, email) {
    this.username = username;
    this.email = email;
    this.isLoggedIn = false;
  }

  /**
   * Log in the user
   * @param {string} password - The user's password
   * @returns {boolean} Whether login was successful
   */
  login(password) {
    // Login logic
    this.isLoggedIn = true;
    return true;
  }
}
```

### Python

#### Function Documentation
```python
def process_data(data, format_type='json', validate=True):
    """
    Process raw data and return in specified format.
    
    Args:
        data (list): Raw data to process
        format_type (str, optional): Output format. Defaults to 'json'.
            Options: 'json', 'csv', 'xml'
        validate (bool, optional): Whether to validate data. Defaults to True.
    
    Returns:
        dict: Processed data in specified format
        
    Raises:
        ValueError: If data is invalid
        TypeError: If format_type is not supported
        
    Examples:
        >>> raw_data = [{'name': 'John', 'age': 30}]
        >>> result = process_data(raw_data, format_type='json')
        >>> print(result)
        {'data': [{'name': 'John', 'age': 30}], 'format': 'json'}
        
        >>> result = process_data(raw_data, format_type='csv', validate=False)
        >>> print(result)
        {'data': 'name,age\\nJohn,30', 'format': 'csv'}
    """
    # Implementation
    pass
```

#### Class Documentation
```python
class DataProcessor:
    """
    A class for processing various data formats.
    
    This class provides methods for processing, validating, and converting
    data between different formats.
    
    Attributes:
        default_format (str): Default output format
        validator (Validator): Data validation instance
        
    Example:
        >>> processor = DataProcessor(default_format='json')
        >>> result = processor.process([{'name': 'John'}])
        >>> print(result)
        {'data': [{'name': 'John'}], 'format': 'json'}
    """
    
    def __init__(self, default_format='json'):
        """
        Initialize the DataProcessor.
        
        Args:
            default_format (str): Default format for output
        """
        self.default_format = default_format
        self.validator = Validator()
    
    def process(self, data, format_type=None):
        """
        Process data in specified format.
        
        Args:
            data (list): Data to process
            format_type (str, optional): Output format. Uses default if None.
            
        Returns:
            dict: Processed data
        """
        # Implementation
        pass
```

### Java

#### Method Documentation
```java
/**
 * Calculates the compound interest on a principal amount.
 * 
 * @param principal The initial amount of money
 * @param rate The annual interest rate (as a decimal)
 * @param time The time period in years
 * @param compoundFrequency The number of times interest is compounded per year
 * @return The compound interest amount
 * @throws IllegalArgumentException if any parameter is negative
 * 
 * @example
 * double interest = calculateCompoundInterest(1000.0, 0.05, 2, 4);
 * System.out.println(interest); // 104.49
 */
public double calculateCompoundInterest(double principal, double rate, 
                                       int time, int compoundFrequency) {
    if (principal < 0 || rate < 0 || time < 0 || compoundFrequency < 0) {
        throw new IllegalArgumentException("All parameters must be non-negative");
    }
    
    double amount = principal * Math.pow(1 + rate / compoundFrequency, 
                                        compoundFrequency * time);
    return amount - principal;
}
```

#### Class Documentation
```java
/**
 * Represents a bank account with basic operations.
 * 
 * This class provides functionality for depositing, withdrawing,
 * and checking the balance of a bank account.
 * 
 * @author Your Name
 * @version 1.0
 * @since 2023-01-01
 */
public class BankAccount {
    private double balance;
    private String accountNumber;
    
    /**
     * Creates a new bank account with the specified account number.
     * 
     * @param accountNumber The unique account number
     * @throws IllegalArgumentException if account number is null or empty
     */
    public BankAccount(String accountNumber) {
        if (accountNumber == null || accountNumber.trim().isEmpty()) {
            throw new IllegalArgumentException("Account number cannot be null or empty");
        }
        this.accountNumber = accountNumber;
        this.balance = 0.0;
    }
    
    /**
     * Deposits money into the account.
     * 
     * @param amount The amount to deposit
     * @return The new balance after deposit
     * @throws IllegalArgumentException if amount is negative or zero
     */
    public double deposit(double amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("Deposit amount must be positive");
        }
        this.balance += amount;
        return this.balance;
    }
}
```

## Framework-Specific Documentation

### React Components

#### Functional Component
```jsx
import React, { useState } from 'react';
import PropTypes from 'prop-types';

/**
 * A reusable button component with loading state and multiple variants.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {string} props.variant - Button style variant
 * @param {string} props.size - Button size
 * @param {boolean} props.disabled - Whether button is disabled
 * @param {boolean} props.loading - Whether button is in loading state
 * @param {Function} props.onClick - Click handler
 * @param {React.ReactNode} props.children - Button content
 * 
 * @example
 * // Basic usage
 * <Button variant="primary" onClick={handleClick}>
 *   Click me
 * </Button>
 * 
 * @example
 * // With loading state
 * <Button variant="secondary" size="large" loading={isLoading}>
 *   Save Changes
 * </Button>
 * 
 * @example
 * // Disabled button
 * <Button variant="danger" disabled>
 *   Delete
 * </Button>
 */
const Button = ({ 
  variant = 'primary', 
  size = 'medium', 
  disabled = false, 
  loading = false, 
  onClick, 
  children 
}) => {
  const handleClick = (e) => {
    if (!disabled && !loading && onClick) {
      onClick(e);
    }
  };

  const buttonClasses = `btn btn-${variant} btn-${size} ${disabled ? 'btn-disabled' : ''} ${loading ? 'btn-loading' : ''}`;

  return (
    <button 
      className={buttonClasses}
      onClick={handleClick}
      disabled={disabled || loading}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
};

Button.propTypes = {
  variant: PropTypes.oneOf(['primary', 'secondary', 'danger']),
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  disabled: PropTypes.bool,
  loading: PropTypes.bool,
  onClick: PropTypes.func,
  children: PropTypes.node.isRequired
};

export default Button;
```

#### Class Component
```jsx
import React, { Component } from 'react';
import PropTypes from 'prop-types';

/**
 * A data table component with sorting, filtering, and pagination.
 * 
 * @class DataTable
 * @extends {Component}
 * 
 * @param {Object} props - Component props
 * @param {Array} props.data - Array of data objects
 * @param {Array} props.columns - Column configuration
 * @param {boolean} props.sortable - Enable sorting
 * @param {boolean} props.filterable - Enable filtering
 * @param {number} props.pageSize - Number of items per page
 * @param {Function} props.onRowClick - Row click handler
 * 
 * @example
 * const columns = [
 *   { key: 'name', label: 'Name', sortable: true },
 *   { key: 'email', label: 'Email', sortable: true },
 *   { key: 'role', label: 'Role', sortable: false }
 * ];
 * 
 * const data = [
 *   { name: 'John Doe', email: 'john@example.com', role: 'Admin' },
 *   { name: 'Jane Smith', email: 'jane@example.com', role: 'User' }
 * ];
 * 
 * <DataTable 
 *   data={data}
 *   columns={columns}
 *   sortable={true}
 *   filterable={true}
 *   pageSize={10}
 *   onRowClick={(row) => console.log('Clicked:', row)}
 * />
 */
class DataTable extends Component {
  constructor(props) {
    super(props);
    this.state = {
      sortColumn: null,
      sortDirection: 'asc',
      filterText: '',
      currentPage: 1
    };
  }

  /**
   * Handles column sorting
   * @param {string} columnKey - The key of the column to sort
   */
  handleSort = (columnKey) => {
    // Implementation
  }

  /**
   * Handles filtering of data
   * @param {string} filterText - The filter text
   */
  handleFilter = (filterText) => {
    // Implementation
  }

  render() {
    // Implementation
  }
}

DataTable.propTypes = {
  data: PropTypes.array.isRequired,
  columns: PropTypes.array.isRequired,
  sortable: PropTypes.bool,
  filterable: PropTypes.bool,
  pageSize: PropTypes.number,
  onRowClick: PropTypes.func
};

DataTable.defaultProps = {
  sortable: false,
  filterable: false,
  pageSize: 10
};

export default DataTable;
```

### Vue Components

#### Vue 3 Composition API
```vue
<template>
  <div class="search-input">
    <input 
      v-model="inputValue"
      :placeholder="placeholder"
      :disabled="disabled"
      @input="handleInput"
      @keyup.enter="handleEnter"
    />
    <button v-if="clearable && inputValue" @click="clear">Clear</button>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue';

/**
 * A search input component with debounced search functionality.
 * 
 * @component SearchInput
 * @param {Object} props - Component props
 * @param {string} props.modelValue - The input value (v-model)
 * @param {string} props.placeholder - Placeholder text
 * @param {boolean} props.disabled - Whether input is disabled
 * @param {boolean} props.clearable - Whether to show clear button
 * @param {number} props.debounce - Debounce delay in milliseconds
 * 
 * @emits {string} update:modelValue - Emitted when value changes
 * @emits {string} search - Emitted when search is performed
 * @emits {void} clear - Emitted when input is cleared
 * 
 * @example
 * <SearchInput 
 *   v-model="searchQuery"
 *   placeholder="Search users..."
 *   :debounce="500"
 *   clearable
 *   @search="performSearch"
 * />
 */
export default {
  name: 'SearchInput',
  props: {
    modelValue: {
      type: String,
      default: ''
    },
    placeholder: {
      type: String,
      default: 'Search...'
    },
    disabled: {
      type: Boolean,
      default: false
    },
    clearable: {
      type: Boolean,
      default: false
    },
    debounce: {
      type: Number,
      default: 300
    }
  },
  emits: ['update:modelValue', 'search', 'clear'],
  setup(props, { emit }) {
    const inputValue = ref(props.modelValue);
    
    // Watch for external value changes
    watch(() => props.modelValue, (newValue) => {
      inputValue.value = newValue;
    });
    
    // Handle input changes
    const handleInput = (event) => {
      const value = event.target.value;
      inputValue.value = value;
      emit('update:modelValue', value);
      
      // Debounced search
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        emit('search', value);
      }, props.debounce);
    };
    
    // Handle enter key
    const handleEnter = () => {
      emit('search', inputValue.value);
    };
    
    // Clear input
    const clear = () => {
      inputValue.value = '';
      emit('update:modelValue', '');
      emit('clear');
    };
    
    let searchTimeout;
    
    return {
      inputValue,
      handleInput,
      handleEnter,
      clear
    };
  }
};
</script>
```

## API Documentation

### REST API Endpoints

#### GET Endpoint
```markdown
### GET /api/users

Retrieves a list of users with optional filtering and pagination.

**Parameters:**
- `page` (number, optional): Page number for pagination (default: 1)
- `limit` (number, optional): Number of items per page (default: 10, max: 100)
- `search` (string, optional): Search term for filtering users
- `role` (string, optional): Filter by user role ('admin', 'user', 'moderator')
- `active` (boolean, optional): Filter by active status

**Response:**
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "role": "admin",
        "active": true,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 50,
      "pages": 5
    }
  }
}
```

**Example Usage:**
```javascript
// Fetch all users
fetch('/api/users')
  .then(response => response.json())
  .then(data => console.log(data));

// Fetch users with filtering
fetch('/api/users?search=john&role=admin&page=2&limit=20')
  .then(response => response.json())
  .then(data => console.log(data));
```

**Error Responses:**
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `500 Internal Server Error`: Server error

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid page parameter",
    "details": {
      "parameter": "page",
      "value": "invalid",
      "expected": "number"
    }
  }
}
```
```

#### POST Endpoint
```markdown
### POST /api/users

Creates a new user account.

**Request Body:**
```json
{
  "username": "string (required, 3-50 characters)",
  "email": "string (required, valid email)",
  "password": "string (required, min 8 characters)",
  "role": "string (optional, default: 'user')",
  "profile": {
    "firstName": "string (optional)",
    "lastName": "string (optional)",
    "bio": "string (optional, max 500 characters)"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 123,
      "username": "new_user",
      "email": "new@example.com",
      "role": "user",
      "active": true,
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  }
}
```

**Example Usage:**
```javascript
const userData = {
  username: 'new_user',
  email: 'new@example.com',
  password: 'secure_password',
  profile: {
    firstName: 'John',
    lastName: 'Doe'
  }
};

fetch('/api/users', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your_token'
  },
  body: JSON.stringify(userData)
})
.then(response => response.json())
.then(data => console.log(data));
```
```

## Testing Documentation

### Unit Tests
```javascript
/**
 * Tests for the calculateTotal function
 * 
 * @group unit/calculations
 */
describe('calculateTotal', () => {
  /**
   * Test basic calculation without options
   */
  test('should calculate total price with tax', () => {
    const result = calculateTotal(100, 0.1);
    expect(result).toBe(110);
  });

  /**
   * Test calculation with rounding option
   */
  test('should round result when round option is true', () => {
    const result = calculateTotal(99.99, 0.08, { round: true });
    expect(result).toBe(108);
  });

  /**
   * Test edge cases
   */
  test('should handle zero price', () => {
    const result = calculateTotal(0, 0.1);
    expect(result).toBe(0);
  });

  test('should handle zero tax rate', () => {
    const result = calculateTotal(100, 0);
    expect(result).toBe(100);
  });
});
```

### Integration Tests
```javascript
/**
 * Integration tests for user authentication flow
 * 
 * @group integration/auth
 */
describe('User Authentication', () => {
  let server;
  let testUser;

  beforeAll(async () => {
    server = await startTestServer();
    testUser = await createTestUser();
  });

  afterAll(async () => {
    await cleanupTestData();
    await server.close();
  });

  /**
   * Test successful login flow
   */
  test('should authenticate user with valid credentials', async () => {
    const response = await request(server)
      .post('/api/auth/login')
      .send({
        username: testUser.username,
        password: testUser.password
      });

    expect(response.status).toBe(200);
    expect(response.body.success).toBe(true);
    expect(response.body.data.token).toBeDefined();
  });

  /**
   * Test failed login with invalid credentials
   */
  test('should reject login with invalid credentials', async () => {
    const response = await request(server)
      .post('/api/auth/login')
      .send({
        username: testUser.username,
        password: 'wrong_password'
      });

    expect(response.status).toBe(401);
    expect(response.body.success).toBe(false);
    expect(response.body.error.code).toBe('INVALID_CREDENTIALS');
  });
});
```

## Configuration Documentation

### Environment Variables
```markdown
# Environment Configuration

## Required Variables

### Database Configuration
- `DB_HOST` (string): Database host address
- `DB_PORT` (number): Database port (default: 5432)
- `DB_NAME` (string): Database name
- `DB_USER` (string): Database username
- `DB_PASSWORD` (string): Database password

### Authentication
- `JWT_SECRET` (string): Secret key for JWT tokens
- `JWT_EXPIRY` (string): Token expiry time (e.g., '24h', '7d')

### API Configuration
- `API_PORT` (number): Port for API server (default: 3000)
- `API_HOST` (string): Host for API server (default: 'localhost')
- `CORS_ORIGIN` (string): Allowed CORS origins (comma-separated)

## Optional Variables

### Logging
- `LOG_LEVEL` (string): Logging level ('debug', 'info', 'warn', 'error')
- `LOG_FORMAT` (string): Log format ('json', 'text')

### External Services
- `REDIS_URL` (string): Redis connection URL
- `SMTP_HOST` (string): SMTP server host
- `SMTP_PORT` (number): SMTP server port
- `SMTP_USER` (string): SMTP username
- `SMTP_PASSWORD` (string): SMTP password

## Example Configuration

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
DB_USER=postgres
DB_PASSWORD=secret

# Authentication
JWT_SECRET=your-super-secret-jwt-key
JWT_EXPIRY=24h

# API
API_PORT=3000
API_HOST=0.0.0.0
CORS_ORIGIN=http://localhost:3000,https://myapp.com

# Logging
LOG_LEVEL=info
LOG_FORMAT=json

# External Services
REDIS_URL=redis://localhost:6379
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```
```

## Documentation Maintenance

### Automated Documentation
```javascript
/**
 * Script to generate API documentation from JSDoc comments
 * 
 * Usage: node generate-docs.js
 */
const jsdoc = require('jsdoc-api');
const fs = require('fs');
const path = require('path');

/**
 * Generate documentation for all JavaScript files
 */
async function generateDocs() {
  const files = await getJavaScriptFiles('./src');
  const docs = await jsdoc.explain({ files });
  
  const apiDocs = docs
    .filter(item => item.kind === 'function' && !item.undocumented)
    .map(formatDocumentation);
  
  const markdownDocs = generateMarkdown(apiDocs);
  fs.writeFileSync('./docs/API.md', markdownDocs);
  
  console.log('Documentation generated successfully!');
}

generateDocs().catch(console.error);
```

### Documentation Review Checklist
```markdown
## Documentation Review Checklist

### Content Review
- [ ] All public APIs are documented
- [ ] Examples are provided for all functions
- [ ] Parameter types and descriptions are accurate
- [ ] Return values are documented
- [ ] Error conditions are documented
- [ ] Examples are tested and working

### Format Review
- [ ] Consistent formatting throughout
- [ ] Proper markdown syntax
- [ ] Code blocks are properly formatted
- [ ] Links are working
- [ ] Table of contents is accurate

### Accessibility Review
- [ ] Clear and concise language
- [ ] Proper heading hierarchy
- [ ] Alternative text for images
- [ ] Consistent terminology
- [ ] Examples are realistic and helpful

### Maintenance Review
- [ ] Documentation matches current code
- [ ] Deprecated features are marked
- [ ] Version information is current
- [ ] Changelog is updated
- [ ] Documentation build process works
```

---

This documentation guide provides comprehensive templates and examples for documenting various types of code structures across different programming languages and frameworks. Use these templates as a starting point and adapt them to your specific project needs.