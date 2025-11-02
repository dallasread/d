# Testing Guide for D DNS Debugger

This document provides comprehensive information about the test suite for the D DNS Debugger application, covering both the Rust backend and Vue/TypeScript frontend.

## Table of Contents

- [Overview](#overview)
- [Rust Backend Tests](#rust-backend-tests)
- [Frontend Tests](#frontend-tests)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Writing New Tests](#writing-new-tests)
- [CI/CD Integration](#cicd-integration)

## Overview

The D DNS Debugger uses a comprehensive testing strategy that includes:

- **Rust Backend**: Unit tests and integration tests for adapters and commands
- **Frontend**: Unit tests for Pinia stores and Vue components using Vitest

### Test Structure

```
d/
├── src-tauri/
│   ├── src/
│   │   ├── adapters/
│   │   │   ├── dns.rs
│   │   │   ├── dns_test.rs         # Unit tests for DNS adapter
│   │   │   ├── whois.rs
│   │   │   ├── whois_test.rs       # Unit tests for WHOIS adapter
│   │   │   ├── certificate.rs
│   │   │   └── certificate_test.rs # Unit tests for Certificate adapter
│   │   └── ...
│   └── tests/
│       └── integration_test.rs     # Integration tests
├── src/
│   ├── components/
│   │   ├── DNS.vue
│   │   └── DNS.spec.ts             # Component tests
│   ├── stores/
│   │   ├── dns.ts
│   │   ├── dns.spec.ts             # Store tests
│   │   ├── whois.spec.ts
│   │   └── certificate.spec.ts
│   └── test/
│       └── setup.ts                # Vitest setup
└── vitest.config.ts
```

## Rust Backend Tests

### Unit Tests

Unit tests are located alongside the source files they test, using the `#[cfg(test)]` attribute.

#### DNS Adapter Tests (`src-tauri/src/adapters/dns_test.rs`)

Tests the DNS query adapter including:
- Parsing dig output for various record types (A, AAAA, MX, TXT, NS, CNAME, SOA)
- DNSSEC record parsing (DNSKEY, DS, RRSIG)
- Multi-line record handling
- Error handling for malformed data

**Example:**
```rust
#[test]
fn test_parse_dig_output_single_a_record() {
    let adapter = DnsAdapter::new();
    let output = "example.com.		3600	IN	A	93.184.216.34";
    let result = adapter.parse_dig_output(output, "A");
    assert!(result.is_ok());
    // ...
}
```

#### WHOIS Adapter Tests (`src-tauri/src/adapters/whois_test.rs`)

Tests the WHOIS lookup adapter including:
- WHOIS server selection for different TLDs
- Parsing WHOIS output fields
- Nameserver extraction
- Status field parsing
- International TLD support

#### Certificate Adapter Tests (`src-tauri/src/adapters/certificate_test.rs`)

Tests the TLS certificate adapter including:
- Parsing certificate subject fields
- Extracting validity dates (old and new OpenSSL formats)
- Certificate chain parsing
- Wildcard certificate handling

### Integration Tests

Integration tests are in `src-tauri/tests/integration_test.rs` and test:
- Command layer integration with adapters
- Data model serialization/deserialization
- End-to-end functionality (marked with `#[ignore]` for optional running)

### Running Rust Tests

```bash
# Run all tests
cd src-tauri
cargo test

# Run tests with output
cargo test -- --nocapture

# Run ignored integration tests (requires dig, whois, openssl)
cargo test -- --ignored

# Run specific test module
cargo test dns_adapter

# Run with coverage (requires cargo-tarpaulin)
cargo tarpaulin --out Html
```

### Test Dependencies

The following dev dependencies are used for Rust tests:
- `mockall`: For creating mock objects
- `tokio-test`: For testing async code
- `assert_matches`: For pattern matching assertions

## Frontend Tests

### Test Framework

The frontend uses **Vitest** as the test runner with:
- `@vue/test-utils`: For mounting and testing Vue components
- `jsdom`: For DOM simulation
- Pinia: For state management testing

### Store Tests

#### DNS Store (`src/stores/dns.spec.ts`)

Tests:
- Initial state
- Fetching DNS records
- Caching mechanism
- Error handling
- Setting and clearing data

#### WHOIS Store (`src/stores/whois.spec.ts`)

Tests:
- WHOIS information fetching
- Caching behavior
- Error states

#### Certificate Store (`src/stores/certificate.spec.ts`)

Tests:
- Certificate fetching
- Custom port handling
- Cache management

### Component Tests

#### DNS Component (`src/components/DNS.spec.ts`)

Tests:
- Empty state rendering
- Loading state
- Record display
- Diagnostic insights (health checks)
- Error display
- Multiple record types
- Priority handling for MX records

**Example:**
```typescript
it('displays DNS records when available', async () => {
  const wrapper = mount(DNS, {
    global: { plugins: [createPinia()] }
  });
  
  const dnsStore = useDNSStore();
  dnsStore.aRecords = { /* mock data */ };
  
  await wrapper.vm.$nextTick();
  expect(wrapper.text()).toContain('93.184.216.34');
});
```

### Running Frontend Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test dns.spec.ts
```

### Test Configuration

The Vitest configuration is in `vitest.config.ts`:

```typescript
export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
});
```

## Test Coverage

### Current Coverage Goals

- **Rust Backend**: Aim for 80%+ coverage on critical paths
  - Adapters: High coverage on parsing logic
  - Commands: Integration test coverage
  - Models: Serialization tests

- **Frontend**: Aim for 70%+ coverage
  - Stores: Complete coverage of actions and state changes
  - Components: Coverage of key user interactions and states

### Generating Coverage Reports

**Rust:**
```bash
cd src-tauri
cargo tarpaulin --out Html --output-dir coverage
# Open coverage/index.html
```

**Frontend:**
```bash
npm run test:coverage
# Open coverage/index.html
```

## Writing New Tests

### Rust Test Template

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_function_name() {
        // Arrange
        let input = "test data";
        
        // Act
        let result = function_under_test(input);
        
        // Assert
        assert_eq!(result, expected_value);
    }

    #[tokio::test]
    async fn test_async_function() {
        let result = async_function().await;
        assert!(result.is_ok());
    }
}
```

### Frontend Test Template

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia } from 'pinia';
import Component from './Component.vue';

describe('Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly', () => {
    const wrapper = mount(Component, {
      global: { plugins: [createPinia()] }
    });
    
    expect(wrapper.text()).toContain('Expected text');
  });
});
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  rust-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Rust
        uses: actions-rs/toolchain@v1
      - name: Run tests
        run: cd src-tauri && cargo test

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node
        uses: actions/setup-node@v3
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm test
```

## Mocking Tauri APIs

The frontend tests mock Tauri APIs in `src/test/setup.ts`:

```typescript
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}));
```

When testing components or stores that use `invoke`, mock the response:

```typescript
import { invoke } from '@tauri-apps/api/core';

vi.mocked(invoke).mockResolvedValue(mockData);
```

## Best Practices

1. **Rust Tests**
   - Test parsing logic thoroughly with real-world examples
   - Use `#[ignore]` for tests requiring external dependencies
   - Test both success and error paths
   - Keep tests fast by avoiding real network calls

2. **Frontend Tests**
   - Mock Tauri API calls
   - Test component states (loading, error, success)
   - Test user interactions
   - Use `beforeEach` to reset state between tests

3. **General**
   - Write descriptive test names
   - One assertion per test when possible
   - Test edge cases and error conditions
   - Keep tests independent and isolated

## Troubleshooting

### Common Issues

**Rust: "dig command not found"**
- Integration tests require `dig`, `whois`, and `openssl`
- Run with `--ignored` flag to skip these tests

**Frontend: "Cannot find module '@tauri-apps/api/core'"**
- Ensure mocks are properly set up in `src/test/setup.ts`

**Frontend: "TypeError: Cannot read properties of undefined"**
- Check that Pinia is properly initialized in test setup
- Ensure stores are created with `setActivePinia(createPinia())`

## Additional Resources

- [Vitest Documentation](https://vitest.dev/)
- [Vue Test Utils](https://test-utils.vuejs.org/)
- [Rust Testing Guide](https://doc.rust-lang.org/book/ch11-00-testing.html)
- [Tauri Testing](https://tauri.app/v1/guides/testing/)
