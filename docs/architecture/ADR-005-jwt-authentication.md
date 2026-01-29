# ADR-005: JWT-Based Authentication

**Status**: Accepted  
**Date**: 2026-01-20  
**Deciders**: Security Team, Development Team  
**Technical Story**: Security Audit P0-002

## Context

The HCD JanusGraph project initially lacked any authentication mechanism, exposing the system to unauthorized access. We needed to implement a robust, scalable authentication system that could:

- Support stateless authentication for distributed systems
- Enable API access from multiple clients
- Provide token expiration and refresh capabilities
- Integrate with existing security infrastructure
- Support future enhancements (MFA, SSO)

### Problem Statement

How do we implement secure, scalable authentication for the JanusGraph API that supports both human users and service accounts while maintaining performance and enabling future security enhancements?

### Constraints

- Must work with existing Python/Gremlin infrastructure
- Cannot require session storage (stateless preferred)
- Must support token expiration and refresh
- Should enable role-based access control
- Must be industry-standard and well-supported

### Assumptions

- Users will access the system through REST API or Python client
- Token lifetime will be configurable
- Refresh tokens will be stored securely
- Integration with external identity providers may be needed in future

## Decision Drivers

- **Security**: Industry-standard, proven security model
- **Scalability**: Stateless authentication for distributed systems
- **Performance**: Minimal overhead for token validation
- **Flexibility**: Support for various client types and future enhancements
- **Maintainability**: Well-documented, widely adopted standard

## Considered Options

### Option 1: Session-Based Authentication

**Pros:**
- Simple to implement
- Easy to revoke sessions
- Familiar pattern

**Cons:**
- Requires session storage (Redis/database)
- Not stateless - complicates scaling
- Sticky sessions or shared session store needed
- Higher latency for distributed systems

### Option 2: JWT (JSON Web Tokens)

**Pros:**
- Stateless - no server-side session storage
- Self-contained - includes user claims
- Industry standard (RFC 7519)
- Excellent library support
- Enables microservices architecture
- Built-in expiration
- Can include custom claims (roles, permissions)

**Cons:**
- Cannot revoke tokens before expiration (mitigated with short TTL + refresh tokens)
- Token size larger than session ID
- Requires secure key management

### Option 3: OAuth 2.0 / OpenID Connect

**Pros:**
- Industry standard for authorization
- Supports multiple grant types
- Built-in token refresh
- Excellent for third-party integrations

**Cons:**
- More complex to implement
- Overkill for current requirements
- Requires additional infrastructure (authorization server)
- Steeper learning curve

## Decision

**We will use JWT (JSON Web Tokens) for authentication with the following implementation:**

1. **Access Tokens**: Short-lived (15 minutes) JWT tokens for API access
2. **Refresh Tokens**: Long-lived (7 days) tokens for obtaining new access tokens
3. **Token Claims**: Include user ID, roles, permissions, and expiration
4. **Signing Algorithm**: HS256 (HMAC with SHA-256) with secure secret key
5. **Token Storage**: Access tokens in memory, refresh tokens in secure HTTP-only cookies

### Rationale

JWT provides the best balance of security, scalability, and flexibility:

- **Stateless**: No session storage required, enabling horizontal scaling
- **Self-contained**: All necessary information in the token
- **Standard**: RFC 7519 with excellent library support
- **Flexible**: Easy to add custom claims for RBAC
- **Future-proof**: Foundation for MFA, SSO, and microservices

The short access token lifetime (15 minutes) mitigates the revocation issue, while refresh tokens enable seamless user experience.

## Consequences

### Positive

- **Scalability**: Stateless authentication enables easy horizontal scaling
- **Performance**: Fast token validation without database lookups
- **Security**: Industry-standard cryptographic signing
- **Flexibility**: Easy to add custom claims and integrate with other systems
- **Developer Experience**: Excellent library support in Python and other languages
- **Microservices Ready**: Tokens can be validated by any service
- **API-Friendly**: Perfect for REST APIs and mobile clients

### Negative

- **Token Revocation**: Cannot immediately revoke tokens (mitigated with short TTL)
- **Token Size**: Larger than session IDs (typically 200-500 bytes)
- **Key Management**: Requires secure storage and rotation of signing keys
- **Clock Synchronization**: Requires synchronized clocks for expiration validation

### Neutral

- **Learning Curve**: Team needs to understand JWT best practices
- **Testing**: Requires mocking JWT generation in tests
- **Monitoring**: Need to track token generation and validation metrics

## Implementation

### Required Changes

1. **Authentication Module** (`src/python/security/auth.py`):
   - JWT token generation
   - Token validation and verification
   - Refresh token management
   - User authentication

2. **Middleware**:
   - JWT validation middleware for API endpoints
   - Token extraction from Authorization header
   - Claims extraction and user context

3. **API Endpoints**:
   - `/auth/login` - User authentication
   - `/auth/refresh` - Token refresh
   - `/auth/logout` - Token invalidation (blacklist)

4. **Configuration**:
   - JWT secret key (from environment)
   - Token expiration times
   - Signing algorithm

5. **Database**:
   - User credentials table
   - Refresh token storage (optional blacklist)

### Migration Path

1. **Phase 1**: Implement JWT authentication alongside existing system
2. **Phase 2**: Update all clients to use JWT tokens
3. **Phase 3**: Deprecate old authentication (if any)
4. **Phase 4**: Remove old authentication code

### Rollback Strategy

If JWT implementation fails:
1. Revert to previous authentication method
2. Clear all issued tokens
3. Force users to re-authenticate
4. Document lessons learned

## Compliance

- [x] Security review completed
- [x] Performance impact assessed (minimal overhead)
- [x] Documentation updated
- [x] Team notified and trained

## References

- [RFC 7519 - JSON Web Token (JWT)](https://tools.ietf.org/html/rfc7519)
- [JWT.io - JWT Debugger and Libraries](https://jwt.io/)
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)

## Notes

### Security Considerations

1. **Secret Key**: Must be cryptographically random, at least 256 bits
2. **HTTPS Only**: Tokens must only be transmitted over HTTPS
3. **Token Storage**: Never store tokens in localStorage (XSS risk)
4. **Expiration**: Short-lived access tokens (15 min) with refresh tokens
5. **Validation**: Always validate signature, expiration, and claims
6. **Blacklist**: Implement token blacklist for critical revocations

### Future Enhancements

- **MFA Integration**: Add MFA claim to tokens
- **SSO**: Integrate with corporate identity providers
- **Token Rotation**: Implement automatic key rotation
- **Asymmetric Keys**: Consider RS256 for microservices
- **Token Introspection**: Add endpoint for token validation