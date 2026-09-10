# CloudBase NoSQL Database Security Rules

This document covers how to configure security rules for CloudBase NoSQL database collections to control read/write permissions.

## Overview

**Important:** To control database permissions, you **MUST** use `managePermissions(action="updateResourcePermission")` to configure security rules. Security rule changes take effect after a few minutes due to caching.

**General Rule:** In most cases, use **simple permissions** (READONLY, PRIVATE, ADMINWRITE, ADMINONLY). Only use CUSTOM rules when you need fine-grained control.

**Scope note:** The detailed semantics in this document apply only to CloudBase **NoSQL database collections** with `resourceType: "noSqlDatabase"`. Examples such as `doc._openid`, `auth.openid`, query-condition subset validation, and `create` / `update` / `delete` JSON rule templates are **not** generic rules for `function`, `storage`, or `sqlDatabase` resources.

**Official references:**
- General security rules overview: `https://cloud.tencent.com/document/product/876/41802`
- NoSQL database security rules: `https://docs.cloudbase.net/database/security-rules`
- Cloud function security rules: `https://docs.cloudbase.net/cloud-function/security-rules`
- Storage security rules: `https://docs.cloudbase.net/storage/security-rules`

### Critical Understanding: Query Condition Requirements

**Security rules are validation-based, NOT filter-based.**

For query or update operations, the **input query conditions must be a subset of the security rules**. The system does **not** actually fetch data from the database. Instead, it validates whether the input query conditions form a subset of the security rules. If the query conditions are not a subset of the rules, it indicates an attempt to access data without permission, and the operation will be **directly rejected**.

**Example:**
- If you define a read/write rule: `auth.openid == doc._openid`
- This means the query condition's `_openid` must equal the current user's `openid` (provided by the system-assigned, non-tamperable `auth.openid`)
- If the query condition doesn't include this constraint, it indicates an attempt to access records where `_openid` is not equal to the user's own, which will be rejected by the backend

**Key Points:**
- Security rules **validate** queries, they don't **filter** results
- The system performs **rule matching** before any database access
- Query conditions must match or be more restrictive than the security rule
- Missing required conditions in queries will result in permission denied errors
- For **create** operations, the system validates the **written data** against the security rules, not query conditions

## Data Permission Management System

CloudBase provides a multi-layered data permission management mechanism that ensures data security while meeting different business scenario permission control requirements.

### Permission Management Hierarchy

CloudBase data permission management includes two levels:

| Permission Type | Control Granularity | Applicable Scenarios | Configuration Complexity |
|----------------|---------------------|----------------------|--------------------------|
| **Basic Permission Control** | Collection level | Simple permission needs | Low |
| **Security Rules** | Document level | Complex business logic | High |

### Basic Permission Control

**Configuration Method:**
Configure permissions for each collection in the [CloudBase Platform](https://tcb.cloud.tencent.com/dev) collection management page.

**Permission Options:**

| Permission Type | Applicable Scenarios | Usage Recommendation |
|----------------|----------------------|----------------------|
| **Read all data, modify own data** | Public content, such as articles, products | Suitable for content display applications |
| **Read and modify own data** | Private data, such as user profiles | Suitable for personal information management |
| **Read all data, cannot modify** | Configuration data, such as system settings | Suitable for read-only configuration and reference data |
| **No permission** | Sensitive data, such as financial information | Suitable for sensitive data requiring server-side processing |

### Security Rules (CUSTOM)

**Function Overview:**

Security rules provide more flexible, extensible, and fine-grained permission control capabilities, supporting dynamic permission judgment based on document content.

**Core Features:**
- **Document-level control**: Can decide access permissions based on specific document content
- **Expression-driven**: Uses programming-like expressions to define permission logic
- **Dynamic permissions**: Supports dynamic permission judgment based on user identity, time, and data content
- **Client-only restriction**: Only restricts client user access, does not affect server-side (cloud function) operations

**Configuration Entry:**
Configure security rules in the [CloudBase Platform/Database](https://tcb.cloud.tencent.com/dev#/db/doc/model) collection management page.

## Permission Categories

CloudBase provides two types of permissions:

### 1. Simple Permissions (Recommended for Most Cases)

These are pre-configured permission templates that cover most common scenarios:

- **READONLY**: All users can read, only creator and admin can write
- **PRIVATE**: Only creator and admin can read/write
- **ADMINWRITE**: All users can read, only admin can write
- **ADMINONLY**: Only admin can read/write

### 2. Custom Security Rules (CUSTOM)

Use CUSTOM when you need fine-grained control based on document data, user identity, or complex conditions.

## Configuring Security Rules

### Using MCP Tool `managePermissions`

**Important:** When developing applications that need permission control, you **MUST** call `managePermissions(action="updateResourcePermission")` to configure database security rules. Do not assume permissions are already configured.

Compatibility note:
- Canonical plugin name: `permissions`
- Legacy plugin aliases `security-rule`, `security-rules`, `secret-rule`, `secret-rules`, and `access-control` still resolve to the `permissions` plugin
- Legacy tools `readSecurityRule` and `writeSecurityRule` are removed; use `queryPermissions` and `managePermissions`

**Scope reminder:** The examples below are for `resourceType: "noSqlDatabase"` only. Do not reuse NoSQL-only expressions such as `doc._openid`, `auth.openid`, query-subset validation, or `create` / `update` / `delete` rule templates as generic guidance for `function`, `storage`, or `sqlDatabase` permissions.

**Basic Usage:**

```javascript
// Example: Set simple permission (PRIVATE)
await managePermissions({
  action: "updateResourcePermission",
  resourceType: "noSqlDatabase",
  resourceId: "collectionName",  // Collection name
  permission: "PRIVATE",
  // securityRule parameter not needed for simple permissions
});
```

**Cache Notice:** After configuring security rules, changes take effect after a few minutes (typically 2-5 minutes) due to caching. Wait a few minutes before testing the new rules.

### Simple Permission Examples

```javascript
// Example 1: Public read, creator-only write
await managePermissions({
  action: "updateResourcePermission",
  resourceType: "noSqlDatabase",
  resourceId: "posts",
  permission: "READONLY"
});

// Example 2: Private collection (only creator and admin)
await managePermissions({
  action: "updateResourcePermission",
  resourceType: "noSqlDatabase",
  resourceId: "userSettings",
  permission: "PRIVATE"
});

// Example 3: Public read, admin-only write
await managePermissions({
  action: "updateResourcePermission",
  resourceType: "noSqlDatabase",
  resourceId: "announcements",
  permission: "ADMINWRITE"
});

// Example 4: Admin-only access
await managePermissions({
  action: "updateResourcePermission",
  resourceType: "noSqlDatabase",
  resourceId: "adminLogs",
  permission: "ADMINONLY"
});
```

## Custom Security Rules (CUSTOM)

### When to Use CUSTOM

Use CUSTOM rules when you need:
- User-specific data access (e.g., users can only read/write their own documents)
- Complex conditions based on document fields
- Time-based access control
- Role-based permissions

### Custom Rule Format

Custom security rules use JSON structure with operation types as keys and conditions as values:

```json
{
  "read": "<condition>",
  "write": "<condition>",
  "create": "<condition>",
  "update": "<condition>",
  "delete": "<condition>"
}
```

**Operation Types:**

| Operation Type | Description | Default Value | Example Scenarios |
|----------------|-------------|---------------|-------------------|
| **read** | Read documents | `false` | Query, get documents |
| **write** | Write documents (general) | `false` | Default rule when specific write operations are not specified |
| **create** | Create documents | Inherits `write` | Add new data |
| **update** | Update documents | Inherits `write` | Modify existing data |
| **delete** | Delete documents | Inherits `write` | Delete data |

> 💡 Note: If specific write operation rules (create/update/delete) are not specified, the `write` rule will be automatically used.

**Condition Values:**
- `true` or `false`: Simple boolean permission
- Expression string: JavaScript-like expression that evaluates to true/false

### Predefined Variables (Global Variables)

Custom rules can use these predefined variables:

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `auth` | Object | User authentication info (null if not logged in) | `auth.openid`, `auth.uid` |
| `doc` | Object | Document data or query conditions | `doc.userId`, `doc.status` |
| `request` | Object | Request information | `request.data` |
| `now` | Number | Current timestamp in milliseconds | `now > doc.expireTime` |

**User Identity Information (auth):**

| Field | Type | Description | Applicable Scenarios |
|-------|------|-------------|---------------------|
| **openid** | String | WeChat user OpenID | WeChat Mini Program login |
| **uid** | String | User unique ID | Web login |
| **loginType** | String | Login method | Distinguish different login channels |

**LoginType Values:**
- `WECHAT_PUBLIC`: WeChat Official Account
- `WECHAT_OPEN`: WeChat Open Platform
- `ANONYMOUS`: Anonymous login (disabled by default for new environments)
- `EMAIL`: Email login
- `CUSTOM`: Custom login

**Request Object:**
- `request.data`: Data object passed in the request (only available for create/update operations)

**Doc Object:**
- Contains all fields of the current document being accessed
- For queries, `doc` represents the query conditions

**Important: `_openid` Field Management**

The `_openid` field is **automatically managed by the CloudBase SDK** and should **never** be included in write operations:

- **Automatic Assignment**: When performing create, update, or set operations through the SDK, the system automatically writes the `_openid` field based on the current authenticated user's identity
- **Do Not Include**: The `_openid` field should **not** appear in any `data` parameter for write operations (`.add()`, `.update()`, `.set()`)
- **Error on Manual Setting**: If you manually include or modify `_openid` in write operations, the operation will **fail with an error**
- **Security Rules Usage**: In security rules, you can reference `doc._openid` to check the document's owner, but you cannot modify it through write operations

**Example:**
```javascript
// Correct: Do not include _openid in write operations
await db.collection('todos').add({
    title: 'My Todo',
    completed: false
    // _openid is automatically added by SDK
});

// Wrong: Including _openid will cause an error
await db.collection('todos').add({
    title: 'My Todo',
    _openid: 'some-id'  // ERROR: Cannot manually set _openid
});

// Correct: Use _openid in security rules for permission checks
{
    "read": "doc._openid == auth.openid",
    "write": "doc._openid == auth.openid"
}
```

### Custom Rule Examples

**Example 1: User can only read/write their own documents**

```javascript
await managePermissions({
  action: "updateResourcePermission",
  resourceType: "noSqlDatabase",
  resourceId: "userTodos",
  permission: "CUSTOM",
  securityRule: JSON.stringify({
    "read": "auth.uid == doc.user_id",
    "write": "auth.uid == doc.user_id"
  })
});
```

**Example 2: Public read, authenticated users can create, only owner can update/delete**

```javascript
await managePermissions({
  action: "updateResourcePermission",
  resourceType: "noSqlDatabase",
  resourceId: "publicPosts",
  permission: "CUSTOM",
  securityRule: JSON.stringify({
    "read": true,
    "create": "auth != null",
    "update": "auth.uid == doc.author_id",
    "delete": "auth.uid == doc.author_id"
  })
});
```

> Warning: This owner-only pattern is not the best fit for CMS article collections that need app-level admin override. For article collections with admin override, prefer a `CUSTOM` rule that combines `get('database.user_roles.' + auth.uid).role == 'admin'` with `doc.authorId == auth.uid`, and keep frontend writes on `.doc(id).update()` / `.doc(id).remove()`.

**Example 2A: Keep owner-only CUSTOM rule and switch the client write path to `where(...)`**

```javascript
await managePermissions({
  action: "updateResourcePermission",
  resourceType: "noSqlDatabase",
  resourceId: "publicPosts",
  permission: "CUSTOM",
  securityRule: JSON.stringify({
    "read": true,
    "create": "auth != null",
    "update": "doc.author_id == auth.uid",
    "delete": "doc.author_id == auth.uid"
  })
});
```

And update through an explicit owner subset:

```javascript
await db.collection('publicPosts')
  .where({
    _id: postId,
    author_id: '{openid}'
  })
  .update({ title: 'Updated Title' });
```

**Example 3: Prevent price modification on update**

```javascript
await managePermissions({
  action: "updateResourcePermission",
  resourceType: "noSqlDatabase",
  resourceId: "orders",
  permission: "CUSTOM",
  securityRule: JSON.stringify({
    "read": "auth.uid == doc.user_id",
    "create": "auth != null",
    "update": "auth.uid == doc.user_id && (doc.price == request.data.price || request.data.price == undefined)",
    "delete": false
  })
});
```

**Example 4: Admin-only delete, users can read/write their own**

```javascript
await managePermissions({
  action: "updateResourcePermission",
  resourceType: "noSqlDatabase",
  resourceId: "userData",
  permission: "CUSTOM",
  securityRule: JSON.stringify({
    "read": "auth.uid == doc.user_id",
    "write": "auth.uid == doc.user_id",
    "delete": false  // Only admin can delete (admin bypasses rules)
  })
});
```

### Expression Syntax

**Expression Length Limit:** Expressions are pseudo-code statements. When configuring, expressions cannot be too long. A single expression is limited to **1024 characters**.

Custom rules support JavaScript-like expressions:

**Supported Operators:**

| Operator | Description | Example | Example Explanation (Collection Query) |
|----------|-------------|---------|----------------------------------------|
| **==** | Equal to | `auth.uid == 'zzz'` | User's uid is zzz |
| **!=** | Not equal to | `auth.uid != 'zzz'` | User's uid is not zzz |
| **>** | Greater than | `doc.age > 10` | Query condition's age property is greater than 10 |
| **>=** | Greater than or equal | `doc.age >= 10` | Query condition's age property is greater than or equal to 10 |
| **<** | Less than | `doc.age < 10` | Query condition's age property is less than 10 |
| **<=** | Less than or equal | `doc.age <= 10` | Query condition's age property is less than or equal to 10 |
| **in** | Exists in collection | `auth.uid in ['zzz','aaa']` | User's uid is one of ['zzz','aaa'] |
| **!(xx in [])** | Does not exist in collection | `!(auth.uid in ['zzz','aaa'])` | User's uid is not any of ['zzz','aaa'] |
| **&&** | Logical AND | `auth.uid == 'zzz' && doc.age > 10` | User's uid is zzz AND query condition's age property is greater than 10 |
| **\|\|** | Logical OR | `auth.uid == 'zzz' \|\| doc.age > 10` | User's uid is zzz OR query condition's age property is greater than 10 |
| **.** | Object element access | `auth.uid` | User's uid |
| **[]** | Array access operator | `get('database.collection_a.user')[auth.uid] == 'zzz'` | In collection_a, document with id 'user', key is user uid, property value is zzz |

### Supported Database Commands

Security rules support the following database commands:

**Logic Commands:**

| Command | Description |
|---------|-------------|
| `or` | `\|\|` Logical OR |
| `and` | `&&` Logical AND |

**Query Commands:**

| Command | Description |
|---------|-------------|
| `eq` | `==` |
| `ne` / `neq` | `!=` |
| `gt` | `>` |
| `gte` | `>=` |
| `lt` | `<` |
| `lte` | `<=` |
| `in` | `in` |
| `nin` | `!(in [])` |

**Update Commands:**

| Command | Description |
|---------|-------------|
| `set` | Overwrite write, `{key: set(object)}` |
| `remove` | Delete field, `{key: remove()}` |

**Example Expressions:**
```javascript
// User ID matches document owner
"auth.uid == doc.user_id"

// User is authenticated
"auth != null"

// User ID in allowed list
"auth.uid in ['admin1', 'admin2']"

// Complex condition
"auth.uid == doc.user_id && doc.status == 'active'"

// Price not modified or undefined
"doc.price == request.data.price || request.data.price == undefined"
```

### Built-in Functions

#### get() Function: Cross-Document Permission Verification

**Function Description:**

The `get()` function allows accessing other document data during permission verification, enabling complex cross-document permission control.

**Syntax:** `get('database.collectionName.documentId')`

**Usage Examples:**

**Role-based Permission Control:**
```json
{
  "read": "get('database.user_roles.' + auth.uid).role in ['admin', 'editor']",
  "write": "get('database.user_roles.' + auth.uid).role == 'admin'"
}
```

**Important syntax note:** put the field access **after** `get(...)`.

```json
{
  "write": "get('database.user_roles.' + auth.uid).role == 'admin'"
}
```

Do **not** write:

```json
{
  "write": "get('database.user_roles.' + auth.uid + '.role') == 'admin'"
}
```

Do **not** use JS template-literal placeholders inside the rule string either:

```json
{
  "write": "get('database.user_roles.${auth.uid}').role == 'admin'"
}
```

Security rules are expression strings, so use concatenation:

```json
{
  "write": "get('database.user_roles.' + auth.uid).role == 'admin'"
}
```

**Admin-or-owner control:**
```json
{
  "update": "get('database.users.' + auth.uid).role == 'admin' || doc.authorId == auth.uid",
  "delete": "get('database.users.' + auth.uid).role == 'admin' || doc.authorId == auth.uid"
}
```

If this collection only needs simple owner-only writes, `READONLY` may be enough. But if the product requirement is “admin users in the app can edit/delete all articles while editors only own their own articles”, use a `CUSTOM` rule such as:

```json
{
  "read": "auth.uid != null",
  "create": "auth.uid != null",
  "update": "auth.uid != null && (get('database.user_roles.' + auth.uid).role == 'admin' || doc.authorId == auth.uid)",
  "delete": "auth.uid != null && (get('database.user_roles.' + auth.uid).role == 'admin' || doc.authorId == auth.uid)"
}
```

For that CMS pattern, `.doc(id).update()` / `.doc(id).remove()` is a validated path, as long as article documents really store `authorId` and `user_roles` documents are keyed by `uid`.

**Associated Data Permissions:**
```json
{
  "read": "auth.uid == get('database.projects.' + doc.projectId).owner"
}
```

**Usage Limitations:**

> **Important:** When using the `get()` function, note the following limitations:
- **Variable restrictions in get parameters**: Variables `doc` that exist in get parameters must appear in query conditions in `==` or `in` format. If using `in` format, only `in` with a single value is allowed, i.e., `doc.shopId in array, array.length == 1`
- Maximum 3 `get` functions per expression
- Maximum access to 10 different documents
- Maximum nesting depth of 2 levels (i.e., `get(get(path))`)
- Generates additional database read operations (billed)

**Billing Notes:**

> **Important:** Security rules themselves are not charged, but additional data access by security rules will be counted in billing:
- **get() function**: Each `get()` produces additional data access
- **Document ID queries for all write operations**: All write operations for document ID queries produce one data access
- **Variable usage**: When not using variables, each `get()` produces one read operation. When using variables, each `get()` produces one read operation for each variable value. For example: rule `get(\`database.collection.${doc._id}\`).test`, when querying `_.or([{_id:1},{_id:2},{_id:3},{_id:4},{_id:5}])` will produce 5 reads. The system will cache reads for the same doc and field.

**Important:** Using `get()` or accessing `doc` counts toward database quota as it reads from the service.

## Best Practices

### 1. Rule Design Principles

- **Principle of Least Privilege:** Only grant necessary permissions
- **Clarity:** Rule expressions should be clear and understandable
- **Performance Considerations:** Avoid excessive `get()` function calls

### 2. General Best Practices

1. **Prefer Simple Permissions:** Use READONLY, PRIVATE, ADMINWRITE, or ADMINONLY for most cases
2. **Use CUSTOM Sparingly:** Only when you need fine-grained control
3. **Test After Configuration:** Wait a few minutes for cache to clear before testing
4. **Avoid Complex Expressions:** Keep custom rules simple and readable
5. **Document Your Rules:** Comment complex rules for future maintenance
6. **Handle Errors:** Always handle permission denied errors in your application code

### 3. Debugging Tips

- Start with simple rules and gradually increase complexity
- Fully test various scenarios in the development environment
- Pay attention to permission error messages in the console
- Reasonably use logs to record permission verification processes

**CRITICAL ERROR: Using ADMINWRITE with Frontend SDK**

| Error Scenario | Symptoms | Root Cause | Correct Approach |
|---------------|----------|------------|------------------|
| Using `ADMINWRITE` for cart/order collections | `.add()` or `.update()` fails<br>Keeps loading or permission error | "ADMIN" in `ADMINWRITE` refers to cloud function environment<br>Frontend SDK has no admin privileges | Use `CUSTOM` rules<br>`{"read": "auth.uid != null", "write": "auth.uid != null"}` |
| Using `PRIVATE` for product collections | Product list disappears after login | `PRIVATE` only allows creator and admin to read<br>Regular users have no permission | Use `READONLY`<br>All users can read, creator and admin can write |

**Key Understanding**:
- `ADMINWRITE` = Cloud functions have write access, Frontend SDK **can only read**
- `CUSTOM` = Configurable read/write permissions for Frontend SDK
- `READONLY` = All users (including anonymous) can read, creator and admin can write. Note: although `READONLY` permits anonymous reads at the ACL level, anonymous login is disabled by default for new environments — callers still need an active login method to obtain a session.

### Role-Based Access Limitations

Security rules work **per request** and cannot selectively grant access to “some” users while denying others unless those users belong to the same ownership context. Typical examples that fail:

- Allowing customer service reps to view **all** orders while normal users only see their own
- Granting merchandisers permission to edit every product while other employees cannot

For these scenarios:

1. Keep frontend collections locked down with `CUSTOM` rules that restrict users to their own data
2. Build **management console APIs** with **cloud functions** (CloudBase Run or functions)
3. Cloud functions bypass security rules, so they can read/write all data safely based on backend authentication/authorization

> TL;DR: **Frontend SDK permissions ≠ backend role management.** If a role needs global data access (e.g., admin dashboard), implement it via cloud functions and never expose that data directly through frontend security rules.

## Query Restrictions and Optimization

### Valid Queries

In actual use, queries are mainly divided into two types: **document ID queries** and **collection queries**.

- **Document ID queries**: Specify a single document ID through `doc` conditions
- **Collection queries**: Can be queries through `where` conditions or aggregate search `match` restriction conditions. For aggregate search, only the first `match` restriction condition is matched.

### Query Condition Requirements

**Critical: Rule Matching Mechanism**

For query or update operations, the input query conditions **must be a subset** of the security rules. The system does **not** actually fetch data from the database. Instead, it validates whether the input query conditions form a subset of the security rules. If the query conditions are n

... [Content truncated, total 38,494 chars] ...