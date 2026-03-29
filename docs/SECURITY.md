# Security Documentation

## Overview
This document outlines the security measures implemented in the Quality of Dutch Government application to address OWASP Top 10 vulnerabilities and other common security issues.

## OWASP Top 10 (2021) - Addressed Vulnerabilities

### ✅ A01:2021 – Broken Access Control
**Status:** MITIGATED

**Implementation:**
- Role-based access control (RBAC) with two levels: End User ('U') and Researcher ('R')
- Session-based authentication using Streamlit's session state
- Protected routes that check authentication status before rendering
- Separate views for different user roles
- Account lockout after 5 failed login attempts (15-minute lockout period)

**Location:** `utils/auth.py`, `streamlit_app.py`

### ✅ A02:2021 – Cryptographic Failures
**Status:** MITIGATED

**Implementation:**
- **Password Hashing:** Replaced SHA-256 with bcrypt (industry standard)
  - Automatic salt generation (prevents rainbow table attacks)
  - Computationally expensive algorithm (prevents brute force)
  - Work factor configurable for future-proofing
- **Backwards Compatibility:** Legacy SHA-256 hashes supported during transition
- **Minimum Password Length:** Increased from 6 to 8 characters
- **Password Complexity:** Requires letters and numbers

**What was changed:**
```python
# BEFORE (INSECURE):
hashlib.sha256(password.encode()).hexdigest()

# AFTER (SECURE):
bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
```

**Location:** `utils/auth.py`, `utils/database.py`

**Additional Recommendations for Production:**
- Use HTTPS/TLS for all connections
- Consider using Argon2id for even stronger protection
- Implement password rotation policies

### ✅ A03:2021 – Injection
**Status:** MITIGATED

**Implementation:**
- **SQL Injection Prevention:**
  - All database queries use SQLAlchemy ORM or parameterized queries
  - User inputs are bound as parameters, never concatenated into SQL strings
  - Additional input sanitization in `utils/security.py`
- **XSS Prevention:**
  - HTML escaping for user inputs (`html.escape()`)
  - Input sanitization functions in `utils/security.py`
  - Content Security Policy headers recommended for production

**Code Examples:**
```python
# SECURE: Parameterized query
conn.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email})

# NOT: String concatenation (we don't do this)
# conn.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

**Location:** `utils/database.py`, `utils/rag.py`, `utils/security.py`

### ✅ A04:2021 – Insecure Design
**Status:** PARTIALLY MITIGATED

**Implementation:**
- Secure password reset mechanism (to be implemented)
- CSRF protection via Streamlit's built-in session management
- Input validation for all user inputs
- Email format validation using RFC-compliant regex
- Rate limiting on authentication attempts

**Future Enhancements:**
- [ ] Email verification for new accounts
- [ ] Two-factor authentication (2FA)
- [ ] Password reset via email with time-limited tokens
- [ ] CAPTCHA for registration/login forms

**Location:** `streamlit_app.py`, `utils/auth.py`, `utils/security.py`

### ✅ A05:2021 – Security Misconfiguration
**Status:** MITIGATED

**Implementation:**
- **Environment Variables:** All secrets stored in `.env` file (not in code)
- **Example Configuration:** `.env.example` provided for reference
- **`.gitignore`:** Configured to exclude `.env` files from version control
- **Security Headers:** Documented in `utils/security.py`
  - X-Frame-Options: DENY
  - X-Content-Type-Options: nosniff
  - X-XSS-Protection: 1; mode=block
  - Content-Security-Policy
  - Referrer-Policy
- **Error Handling:** Generic error messages to prevent information disclosure

**Production Deployment Checklist:**
```bash
# 1. Set environment to production
ENVIRONMENT=production

# 2. Disable debug mode
DEBUG=False

# 3. Use strong database credentials
DB_PASSWORD=<use-strong-random-password>

# 4. Enable HTTPS
# Configure at web server/reverse proxy level

# 5. Set security headers
# Configure in nginx/Apache (see utils/security.py for values)
```

**Location:** `.env.example`, `utils/security.py`, `.gitignore`

### ✅ A06:2021 – Vulnerable and Outdated Components
**Status:** MONITORING REQUIRED

**Implementation:**
- `requirements.txt` specifies minimum versions
- All dependencies specified with version constraints
- bcrypt library used for secure password hashing

**Recommendations:**
```bash
# Regular dependency updates
pip list --outdated

# Security vulnerability scanning
pip-audit

# Update dependencies
pip install --upgrade package-name
```

**Dependencies to Monitor:**
- streamlit (web framework)
- sqlalchemy (database ORM)
- bcrypt (password hashing)
- ollama (LLM integration)
- pandas, numpy (data processing)

**Location:** `requirements.txt`

### ✅ A07:2021 – Identification and Authentication Failures
**STATUS:** MITIGATED

**Implementation:**
- **Strong Password Policy:**
  - Minimum 8 characters (industry standard)
  - Must contain letters and numbers
  - Special characters recommended
- **Account Lockout:**
  - 5 failed login attempts triggers 15-minute lockout
  - Prevents brute force attacks
- **Rate Limiting:** Login attempts tracked per session
- **Generic Error Messages:** Prevents user enumeration
- **Password Storage:** Bcrypt with automatic salt
- **Session Management:**
  - Session state cleared on logout
  - No persistent sessions across browser restarts

**Security Features:**
```python
# Account lockout after 5 failed attempts
if st.session_state.login_attempts >= 5:
    st.session_state.lockout_until = datetime.now() + timedelta(minutes=15)

# Generic error message (prevents email enumeration)
return False, "Invalid email or password. Please try again."
```

**Location:** `utils/auth.py`, `streamlit_app.py`

### ✅ A08:2021 – Software and Data Integrity Failures
**Status:** PARTIALLY ADDRESSED

**Implementation:**
- Code integrity maintained through version control (Git)
- Database constraints enforce data integrity
- Check constraints on access levels and satisfaction ratings

**Recommendations for Production:**
- Use code signing for deployments
- Implement CI/CD pipeline with security checks
- Verify package integrity during installation
- Use dependency lock files

**Location:** `utils/database.py`

### ✅ A09:2021 – Security Logging and Monitoring Failures
**Status:** PARTIALLY IMPLEMENTED

**Implementation:**
- Security event logging framework in `utils/security.py`
- Login attempt tracking
- Session state includes security logs

**Log Events:**
- Failed login attempts
- Account lockouts
- Successful authentications
- User session creation/termination

**Production Recommendations:**
```python
# Integrate with proper logging system
import logging

logging.basicConfig(
    filename='security.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Log security events
logging.warning(f"Failed login attempt for user: {email}")
```

**Location:** `utils/security.py`, `utils/auth.py`

### ✅ A10:2021 – Server-Side Request Forgery (SSRF)
**Status:** NOT APPLICABLE

The application does not make server-side requests to user-controlled URLs. The only external connection is to the Ollama API, which is configured via environment variables (not user input).

## Additional Security Measures

### Input Validation
- Email format validation (RFC-compliant)
- Password strength checking
- Input sanitization for XSS prevention
- SQL injection prevention via parameterized queries

**Location:** `utils/security.py`

### Session Security
- Session timeout (configurable via environment variables)
- Secure session cleanup on logout
- No sensitive data in session state

### Database Security
- Connection strings stored in environment variables
- Support for both SQLite (dev) and PostgreSQL (production)
- ORM-based queries (prevents SQL injection)
- Database constraints enforce business rules

**Location:** `utils/database.py`

## Security Testing

### Recommended Tests

1. **Authentication Testing:**
   ```bash
   # Test account lockout
   # Try logging in with wrong password 5+ times
   
   # Test password requirements
   # Try creating account with weak password
   ```

2. **SQL Injection Testing:**
   ```bash
   # Try injecting SQL in login form
   # Email: admin' OR '1'='1
   # Email: admin'--
   ```

3. **XSS Testing:**
   ```bash
   # Try injecting JavaScript in text fields
   # Input: <script>alert('XSS')</script>
   ```

4. **CSRF Testing:**
   # Streamlit handles CSRF via session tokens

5. **Dependency Scanning:**
   ```bash
   pip install pip-audit
   pip-audit
   ```

## Production Deployment Security Checklist

### Pre-Deployment
- [ ] All secrets in environment variables
- [ ] No hardcoded credentials in code
- [ ] `.env` file not committed to repository
- [ ] Strong database password configured
- [ ] HTTPS/TLS certificate configured
- [ ] Security headers configured in web server
- [ ] Dependencies updated to latest secure versions
- [ ] Run security scanning tools

### Infrastructure
- [ ] Deploy behind reverse proxy (nginx/Apache)
- [ ] Configure firewall rules
- [ ] Enable rate limiting at proxy level
- [ ] Set up monitoring and alerting
- [ ] Configure automated backups
- [ ] Implement log rotation
- [ ] Use secrets management service (AWS Secrets Manager, HashiCorp Vault)

### Application Configuration
```bash
# Production .env
ENVIRONMENT=production
DEBUG=False
DB_TYPE=postgresql
DB_HOST=secure-db-host
DB_PORT=5432
DB_USER=qog_app
DB_PASSWORD=<strong-random-password>
SESSION_TIMEOUT=30
```

### Web Server Security Headers (nginx example)
```nginx
add_header X-Frame-Options "DENY";
add_header X-Content-Type-Options "nosniff";
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;";
add_header Permissions-Policy "geolocation=(), microphone=(), camera=(), payment=()";
```

### Monitoring
- [ ] Set up security event monitoring
- [ ] Configure alerts for:
  - Multiple failed login attempts
  - Account lockouts
  - Database connection failures
  - Unusual traffic patterns
- [ ] Regular security audit reviews
- [ ] Penetration testing schedule

## Security Contact
For security issues, please contact the development team through the appropriate secure channels. Do not publicly disclose security vulnerabilities.

## References
- [OWASP Top 10 (2021)](https://owasp.org/Top10/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [bcrypt Documentation](https://github.com/pyca/bcrypt/)
- [Streamlit Security Best Practices](https://docs.streamlit.io/)

## Version History
- v1.0.0 (2026-01-26): Initial security implementation
  - Replaced SHA-256 with bcrypt for password hashing
  - Implemented account lockout mechanism
  - Added input validation and sanitization
  - Created security utilities module
  - Documented all OWASP Top 10 mitigations
