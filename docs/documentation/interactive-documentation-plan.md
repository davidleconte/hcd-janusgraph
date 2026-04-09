# Interactive Documentation Implementation Plan
# Priority Action 3: +0.1 Points to Excellence Score

**Date:** 2026-04-09  
**Target:** Documentation Excellence 9.9 → 10.0  
**Effort:** 1-2 weeks  
**Status:** Pending

---

## Executive Summary

Implement interactive documentation including Swagger UI for API documentation, interactive Jupyter notebooks, and video tutorials. This will improve documentation accessibility and user experience.

---

## Objectives

1. **Add Swagger UI for API documentation** (+0.05)
   - Interactive API explorer
   - Try-it-out functionality
   - Auto-generated from OpenAPI spec

2. **Create video tutorials for key scenarios** (+0.05)
   - Banking scenario walkthroughs
   - Setup and deployment guides
   - Troubleshooting videos

---

## Phase 1: Swagger UI Integration (Week 1)

### 1.1 OpenAPI Specification Enhancement

**Enhance existing OpenAPI spec:**

```yaml
# docs/api/openapi-enhanced.yaml

openapi: 3.0.3
info:
  title: JanusGraph Banking API
  description: |
    # Banking Compliance Platform API
    
    This API provides access to the JanusGraph Banking Compliance Platform,
    enabling AML detection, fraud analysis, and UBO discovery.
    
    ## Authentication
    
    All endpoints require JWT authentication. Obtain a token from `/auth/login`.
    
    ```bash
    curl -X POST http://localhost:8000/auth/login \
      -H "Content-Type: application/json" \
      -d '{"username": "admin", "password": "secure_password"}'
    ```
    
    ## Rate Limiting
    
    - 100 requests per minute per IP
    - 1000 requests per hour per user
    
    ## Try It Out
    
    Use the interactive API explorer below to test endpoints.
    
  version: 1.0.0
  contact:
    name: API Support
    email: support@example.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: http://localhost:8000
    description: Local development
  - url: https://api-staging.example.com
    description: Staging environment
  - url: https://api.example.com
    description: Production environment

tags:
  - name: Authentication
    description: User authentication and authorization
  - name: AML
    description: Anti-Money Laundering detection
  - name: Fraud
    description: Fraud detection and analysis
  - name: UBO
    description: Ultimate Beneficial Owner discovery
  - name: Health
    description: Service health and monitoring

paths:
  /auth/login:
    post:
      tags: [Authentication]
      summary: User login
      description: Authenticate user and obtain JWT token
      operationId: login
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [username, password]
              properties:
                username:
                  type: string
                  example: admin
                password:
                  type: string
                  format: password
                  example: secure_password
            examples:
              admin:
                summary: Admin login
                value:
                  username: admin
                  password: secure_password
              analyst:
                summary: Analyst login
                value:
                  username: analyst
                  password: analyst_password
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                    example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
                  token_type:
                    type: string
                    example: bearer
                  expires_in:
                    type: integer
                    example: 3600
              examples:
                success:
                  summary: Successful login
                  value:
                    access_token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
                    token_type: bearer
                    expires_in: 3600
        '401':
          description: Invalid credentials
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              examples:
                invalid_credentials:
                  summary: Invalid username or password
                  value:
                    error: Invalid credentials
                    message: Username or password is incorrect

  /aml/structuring:
    post:
      tags: [AML]
      summary: Detect structuring patterns
      description: |
        Analyze transactions for structuring patterns (smurfing).
        
        Structuring is the practice of breaking up large transactions
        into smaller amounts to avoid reporting thresholds.
        
        **Example Use Case:**
        Detect if a customer is making multiple deposits just below
        the $10,000 reporting threshold.
      operationId: detectStructuring
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/StructuringRequest'
            examples:
              suspicious:
                summary: Suspicious pattern
                value:
                  customer_id: "C-12345"
                  time_window_days: 7
                  threshold: 10000
              normal:
                summary: Normal activity
                value:
                  customer_id: "C-67890"
                  time_window_days: 30
                  threshold: 10000
      responses:
        '200':
          description: Analysis complete
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/StructuringResponse'
              examples:
                detected:
                  summary: Structuring detected
                  value:
                    detected: true
                    confidence: 0.95
                    transactions: 15
                    total_amount: 145000
                    pattern: "Multiple deposits just below threshold"
                    recommendation: "File SAR"

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  
  schemas:
    Error:
      type: object
      properties:
        error:
          type: string
        message:
          type: string
        details:
          type: object
    
    StructuringRequest:
      type: object
      required: [customer_id]
      properties:
        customer_id:
          type: string
          description: Customer identifier
          example: "C-12345"
        time_window_days:
          type: integer
          description: Analysis time window in days
          default: 7
          minimum: 1
          maximum: 365
        threshold:
          type: number
          description: Reporting threshold amount
          default: 10000
          minimum: 0
    
    StructuringResponse:
      type: object
      properties:
        detected:
          type: boolean
          description: Whether structuring was detected
        confidence:
          type: number
          format: float
          description: Confidence score (0-1)
          minimum: 0
          maximum: 1
        transactions:
          type: integer
          description: Number of transactions analyzed
        total_amount:
          type: number
          description: Total transaction amount
        pattern:
          type: string
          description: Detected pattern description
        recommendation:
          type: string
          description: Recommended action
```

### 1.2 Swagger UI Deployment

**Add Swagger UI to FastAPI app:**

```python
# src/python/api/main.py

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
import yaml

app = FastAPI(
    title="JanusGraph Banking API",
    description="Banking Compliance Platform API",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
)

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    # Load enhanced OpenAPI spec
    with open("docs/api/openapi-enhanced.yaml") as f:
        openapi_schema = yaml.safe_load(f)
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Serve Swagger UI at /docs
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>JanusGraph Banking API</title>
        </head>
        <body>
            <h1>JanusGraph Banking API</h1>
            <ul>
                <li><a href="/docs">Swagger UI (Interactive API Explorer)</a></li>
                <li><a href="/redoc">ReDoc (API Documentation)</a></li>
                <li><a href="/health">Health Check</a></li>
            </ul>
        </body>
    </html>
    """
```

### 1.3 API Examples & Tutorials

**Create interactive API tutorials:**

```markdown
# docs/api/interactive-tutorial.md

# Interactive API Tutorial

## Getting Started

1. **Start the API server:**
   ```bash
   cd src/python/api
   uvicorn main:app --reload
   ```

2. **Open Swagger UI:**
   Navigate to http://localhost:8000/docs

3. **Authenticate:**
   - Click "Authorize" button
   - Enter credentials: `admin` / `secure_password`
   - Click "Authorize"

## Try It Out: AML Structuring Detection

### Step 1: Login

1. Expand `/auth/login` endpoint
2. Click "Try it out"
3. Use example payload:
   ```json
   {
     "username": "admin",
     "password": "secure_password"
   }
   ```
4. Click "Execute"
5. Copy the `access_token` from response

### Step 2: Detect Structuring

1. Click "Authorize" and paste token
2. Expand `/aml/structuring` endpoint
3. Click "Try it out"
4. Use example payload:
   ```json
   {
     "customer_id": "C-12345",
     "time_window_days": 7,
     "threshold": 10000
   }
   ```
5. Click "Execute"
6. Review detection results

### Step 3: Explore Other Endpoints

- `/fraud/detect` - Fraud detection
- `/ubo/discover` - UBO discovery
- `/health` - Service health
```

**Estimated Effort:** 3-4 days

---

## Phase 2: Video Tutorials (Week 1-2)

### 2.1 Video Content Plan

**Tutorial Videos to Create:**

1. **Getting Started (5 minutes)**
   - Project overview
   - Quick setup
   - First query

2. **Banking Scenarios (15 minutes)**
   - AML structuring detection
   - Fraud ring detection
   - UBO discovery
   - Customer 360 view

3. **Deployment Guide (10 minutes)**
   - Podman setup
   - Service deployment
   - Health verification
   - Troubleshooting

4. **API Usage (8 minutes)**
   - Authentication
   - Making requests
   - Error handling
   - Rate limiting

5. **Notebook Walkthrough (12 minutes)**
   - Opening notebooks
   - Running cells
   - Interpreting results
   - Customization

6. **Troubleshooting (7 minutes)**
   - Common issues
   - Log analysis
   - Service restart
   - Getting help

### 2.2 Video Production

**Tools:**
- Screen recording: OBS Studio (free)
- Video editing: DaVinci Resolve (free)
- Hosting: YouTube (unlisted/public)

**Production Checklist:**
- [ ] Write script
- [ ] Record screen
- [ ] Record voiceover
- [ ] Edit video
- [ ] Add captions
- [ ] Upload to YouTube
- [ ] Embed in docs

**Video Template:**

```markdown
# Video: Getting Started with JanusGraph Banking Platform

## Overview
This 5-minute tutorial shows you how to get started with the platform.

## What You'll Learn
- Project structure
- Quick setup with Podman
- Running your first query
- Viewing results

## Video
<iframe width="560" height="315" 
  src="https://www.youtube.com/embed/VIDEO_ID" 
  frameborder="0" 
  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
  allowfullscreen>
</iframe>

## Timestamps
- 0:00 - Introduction
- 0:30 - Project overview
- 1:30 - Setup with Podman
- 3:00 - First query
- 4:30 - Next steps

## Resources
- [QUICKSTART.md](../../QUICKSTART.md)
- [Deployment Guide](../operations/deployment-guide.md)
- [API Reference](../api/rest-api.md)

## Transcript
[Full transcript for accessibility]
```

### 2.3 Video Integration

**Update documentation with video embeds:**

```markdown
# README.md

## Quick Start

Watch our 5-minute getting started video:

[![Getting Started](https://img.youtube.com/vi/VIDEO_ID/0.jpg)](https://www.youtube.com/watch?v=VIDEO_ID)

Or follow the [written guide](QUICKSTART.md).

## Video Tutorials

- [Getting Started (5 min)](docs/videos/getting-started.md)
- [Banking Scenarios (15 min)](docs/videos/banking-scenarios.md)
- [Deployment Guide (10 min)](docs/videos/deployment-guide.md)
- [API Usage (8 min)](docs/videos/api-usage.md)
- [Troubleshooting (7 min)](docs/videos/troubleshooting.md)
```

**Estimated Effort:** 5-7 days

---

## Phase 3: Interactive Notebooks (Week 2)

### 3.1 Binder Integration

**Add Binder support for interactive notebooks:**

```yaml
# binder/environment.yml

name: janusgraph-analysis
channels:
  - conda-forge
dependencies:
  - python=3.11
  - jupyter
  - jupyterlab
  - pandas
  - matplotlib
  - seaborn
  - networkx
  - pip
  - pip:
    - gremlinpython
    - fastapi
    - uvicorn
```

**Add Binder badge to README:**

```markdown
# README.md

## Try It Online

Launch interactive notebooks in your browser (no installation required):

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/your-org/hcd-janusgraph/main?filepath=notebooks)

Click the badge above to start exploring banking scenarios interactively.
```

### 3.2 Interactive Notebook Enhancements

**Add interactive widgets to notebooks:**

```python
# notebooks/interactive-aml-detection.ipynb

import ipywidgets as widgets
from IPython.display import display

# Interactive threshold slider
threshold_slider = widgets.FloatSlider(
    value=10000,
    min=1000,
    max=50000,
    step=1000,
    description='Threshold:',
    continuous_update=False
)

# Interactive time window selector
time_window = widgets.IntSlider(
    value=7,
    min=1,
    max=30,
    step=1,
    description='Days:',
    continuous_update=False
)

# Run button
run_button = widgets.Button(
    description='Detect Structuring',
    button_style='success'
)

def on_run_clicked(b):
    threshold = threshold_slider.value
    days = time_window.value
    
    # Run detection
    results = detect_structuring(
        customer_id="C-12345",
        threshold=threshold,
        time_window_days=days
    )
    
    # Display results
    print(f"Detected: {results['detected']}")
    print(f"Confidence: {results['confidence']:.2%}")
    print(f"Transactions: {results['transactions']}")

run_button.on_click(on_run_clicked)

# Display widgets
display(threshold_slider, time_window, run_button)
```

**Estimated Effort:** 2-3 days

---

## Success Criteria

### Swagger UI
- ✅ Enhanced OpenAPI spec with examples
- ✅ Swagger UI deployed at /docs
- ✅ ReDoc deployed at /redoc
- ✅ Interactive API tutorial created
- ✅ All endpoints documented

### Video Tutorials
- ✅ 6 tutorial videos created
- ✅ Total runtime: ~60 minutes
- ✅ Videos uploaded to YouTube
- ✅ Videos embedded in documentation
- ✅ Transcripts provided for accessibility

### Interactive Notebooks
- ✅ Binder integration configured
- ✅ Interactive widgets added to 5+ notebooks
- ✅ Launch badge in README
- ✅ Online demo available

### Impact
- **Documentation Score:** 9.9 → 10.0 (+0.1)
- **Overall Score:** 9.9 → 10.0 (+0.1) (with other actions)

---

## Timeline

| Week | Tasks | Deliverables |
|------|-------|--------------|
| Week 1 | Swagger UI, API tutorials, video scripts | Interactive API docs, 3 videos |
| Week 2 | Video production, Binder setup | 6 videos, interactive notebooks |

**Total Effort:** 1-2 weeks  
**Resources:** 1 technical writer + 1 developer  
**Dependencies:** None

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Video production takes longer | Medium | Start with most important videos |
| Binder setup issues | Low | Provide local alternative |
| API changes break examples | Low | Automated testing of examples |

---

## Next Steps

1. ⏳ Enhance OpenAPI specification
2. ⏳ Deploy Swagger UI
3. ⏳ Write video scripts
4. ⏳ Record and edit videos
5. ⏳ Configure Binder
6. ⏳ Add interactive widgets to notebooks
7. ⏳ Update documentation with videos
8. ⏳ Test all interactive features

---

**Status:** Ready to start  
**Owner:** Documentation Team  
**Reviewer:** Product Manager  
**Next Review:** 2026-04-16 (Week 1 checkpoint)