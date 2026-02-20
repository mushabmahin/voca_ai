# APP_FLOW.md — VOCA AI

## App Description

VOCA AI is an API-first, multimodal conversation intelligence backend that enables enterprises to analyze voice and text conversations. It provides structured insights such as summaries, sentiment, intents, entities, and compliance risk signals via secure REST APIs and a minimal web console for configuration, monitoring, and API key management.

The application includes:
- Developer Console (API management & testing)
- Configuration Management
- Usage Monitoring
- Authentication & Access Control

---

# 1. Entry Points

Users can access VOCA AI through the following entry points:

### 1.1 Direct URL
- `https://console.vocaai.com`
  - IF unauthenticated → Redirect to Login
  - IF authenticated → Redirect to Dashboard

### 1.2 Marketing Website CTA
- `https://vocaai.com`
  - Click "Get Started" → Redirect to Registration

### 1.3 Email Invitation Link
- Invitation link with token
  - IF token valid → Accept Invitation screen
  - IF token expired → Show "Link Expired" → Option to request new link

### 1.4 Email Verification Link
- After signup
  - IF valid → Activate account → Redirect to Onboarding
  - IF invalid → Show error → Resend verification option

### 1.5 Password Reset Link
- From “Forgot Password”
  - IF valid token → Reset Password screen
  - IF expired → Prompt to re-request reset

### 1.6 API Access (Backend)
- `POST /v1/analyze`
  - IF valid API key → Process request
  - IF invalid → 401 Unauthorized

---

# 2. Core User Flows

---

## 2.1 User Registration & Onboarding

### Happy Path

1. User clicks “Get Started”
2. Enters:
   - Name
   - Work Email
   - Password
   - Organization Name
3. Clicks "Create Account"
4. System:
   - Validates inputs
   - Creates account (unverified)
   - Sends verification email
5. User clicks email verification link
6. Account status → Verified
7. Redirect to Onboarding Wizard
8. Onboarding:
   - Select Industry (Banking / Telecom / Fintech / BPO / Other)
   - Upload or define sample configuration JSON
   - Generate first API key
9. Redirect to Dashboard

Next Step: User can test API or configure rules.

---

### Error States

| Error | System Behavior | Next Step |
|-------|----------------|-----------|
| Email already exists | Show inline error | Offer Login |
| Weak password | Show password policy | User retries |
| Verification expired | Show error | Resend verification |
| Invalid onboarding JSON | Show validation error | User edits config |

---

### Edge Cases

- User closes browser before verification  
  → Must verify before login allowed
- User registers but never verifies  
  → Account auto-deactivated after 7 days
- Corporate email domain restriction enabled  
  → Block public domains

---

## 2.2 Main Feature Usage (Conversation Analysis)

### Happy Path (Web Console Testing)

1. User logs in
2. Lands on Dashboard
3. Clicks “Analyze Conversation”
4. Chooses input type:
   - Upload Audio
   - Paste Transcript
5. (Optional) Select Configuration Profile
6. Clicks “Run Analysis”
7. System:
   - Validates input
   - Processes request
   - Displays structured JSON output
8. User can:
   - Download JSON
   - Copy API request
   - Save as template

Next Step: User iterates or integrates via API.

---

### Happy Path (API Usage)

1. Developer sends POST `/v1/analyze`
2. Includes:
   - API Key
   - Audio file or transcript
   - Optional config JSON
3. System validates:
   - Auth
   - File size
   - Format
4. System processes
5. Returns JSON response
6. Client system consumes response

Next Step: Store insights or trigger workflow.

---

### Error States

| Error | Response | Next Step |
|-------|----------|----------|
| Missing input | 400 Bad Request | Fix request |
| File >50MB | 413 Payload Too Large | Compress/retry |
| Invalid API key | 401 Unauthorized | Regenerate key |
| Rate limit exceeded | 429 Too Many Requests | Retry after delay |
| Invalid config | 422 Unprocessable Entity | Correct JSON |

---

### Edge Cases

- Mixed-language conversation → Return multiple languages
- Corrupted audio → Return partial insights + warning
- Ambiguous intent → Return multiple intents with confidence scores
- Timeout → Return 504 Gateway Timeout

---

## 2.3 Account Management

### Happy Path

1. User clicks Profile
2. Views:
   - Organization details
   - API keys
   - Usage metrics
3. Can:
   - Generate new API key
   - Revoke API key
   - Update config
   - Invite team member
4. System confirms action
5. Update saved successfully

Next Step: Return to Dashboard

---

### Error States

| Action | Error | Next Step |
|--------|-------|----------|
| Generate key | Permission denied | Contact admin |
| Update config | Invalid JSON | Correct & retry |
| Invite member | Email invalid | Fix email |

---

### Edge Cases

- Revoking active API key → Immediate invalidation
- User removed from org → Forced logout
- Plan limit exceeded → Prompt upgrade

---

# 3. Navigation Map
/
├── Login
├── Register
├── Verify Email
├── Forgot Password
├── Reset Password
├── Dashboard
│ ├── Analyze Conversation
│ ├── Analysis History
│ ├── Configurations
│ ├── API Keys
│ ├── Usage Metrics
│ ├── Team Management
│ └── Account Settings
├── Error Pages
│ ├── 404
│ ├── 500
│ └── Access Denied

---

# 4. Screen Inventory

---

## Login

- Route: `/login`
- Access: Public
- Purpose: Authenticate user
- Key Elements: Email, Password, Forgot Password
- Actions: Login → Dashboard
- States: Invalid credentials, Account unverified

---

## Dashboard

- Route: `/dashboard`
- Access: Authenticated
- Purpose: Overview & quick actions
- Key Elements: Usage graph, Analyze button, Recent activity
- Actions: Navigate to tools
- States: Empty (no analyses yet)

---

## Analyze Conversation

- Route: `/analyze`
- Access: Authenticated
- Purpose: Submit conversation
- Key Elements: File upload, Transcript box, Config selector
- Actions: Run Analysis → Results
- States: Processing, Success, Error

---

## Configurations

- Route: `/config`
- Access: Authenticated (Admin)
- Purpose: Manage rule sets
- Actions: Create/Edit/Delete config
- States: Validation errors

---

## API Keys

- Route: `/api-keys`
- Access: Authenticated (Admin)
- Purpose: Manage API credentials
- Actions: Generate/Revoke key

---

# 5. Decision Points

### Authentication
- IF not logged in → Redirect to Login
- IF logged in but unverified → Restrict dashboard access

### Authorization
- IF role = Admin → Full access
- IF role = Developer → No team management
- IF role = Viewer → Read-only

### Empty States
- IF no API keys → Prompt generate key
- IF no analyses → Show “Run first analysis”
- IF no config → Prompt create config

---

# 6. Error Handling

### 404 Not Found
- Show friendly message
- Provide link to Dashboard

### 500 Internal Server Error
- Show generic error
- Log error ID
- Retry option

### Network Offline
- Show banner
- Retry automatically when reconnected

### Permission Denied (403)
- Show "Access Restricted"
- Suggest contacting admin

---

# 7. Responsive Behavior

## Desktop
- Sidebar navigation
- Split screen (Input | Output view)
- Full JSON viewer

## Mobile
- Bottom navigation
- Collapsible sections
- JSON collapses into expandable tree
- File upload via device picker

Differences:
- Mobile limits large JSON preview
- Desktop supports drag-drop upload
- Desktop shows multi-panel analytics

---

# End-to-End Flow Guarantee

Every action leads to:
- A success state (dashboard update, JSON response, confirmation message)
OR
- A recoverable error state (validation error, retry option, support contact)

There are no dead-end screens.

---

# Summary

VOCA AI’s application flow ensures:
- Secure onboarding
- Clear API usage paths
- Robust error handling
- Enterprise-grade permission logic
- Fully documented success and failure transitions