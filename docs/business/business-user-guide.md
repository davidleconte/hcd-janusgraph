# Business User Guide
# HCD + JanusGraph Banking Compliance Platform

**Date:** 2026-02-19  
**Version:** 1.0  
**For:** Business Analysts, Compliance Officers, Fraud Investigators  
**Author:** David LECONTE - IBM Worldwide | Data & AI | Tiger Team

---

## Welcome

Welcome to the HCD + JanusGraph Banking Compliance Platform! This guide will help you understand and use the platform's capabilities for financial crime detection, regulatory compliance, and business analytics.

### Who This Guide Is For

- **Business Analysts**: Analyze transaction patterns and generate reports
- **Compliance Officers**: Monitor regulatory compliance and file reports
- **Fraud Investigators**: Investigate suspicious activities and fraud rings
- **Risk Managers**: Assess and monitor risk across the organization
- **Operations Managers**: Monitor platform performance and capacity

### What You'll Learn

1. Platform overview and key capabilities
2. Common use cases and workflows
3. Dashboard navigation and interpretation
4. Report generation and export
5. Alert management and investigation
6. Best practices and tips

---

## 1. Platform Overview

### 1.1 What Is the Platform?

The HCD + JanusGraph Banking Compliance Platform is a **graph-based solution** for real-time financial crime detection and regulatory compliance automation. It analyzes relationships between entities (people, companies, accounts, transactions) to detect suspicious patterns that traditional systems miss.

### 1.2 Key Capabilities

#### Real-Time AML/Fraud Detection
- **Structuring Detection**: Identify smurfing patterns (multiple transactions below $10K threshold)
- **Fraud Ring Detection**: Discover coordinated fraud networks across 6 degrees of separation
- **Suspicious Activity Monitoring**: Automated SAR generation with 95% accuracy
- **Multi-Currency Analysis**: Support for 150+ currencies

#### Ultimate Beneficial Owner (UBO) Discovery
- **Ownership Chain Analysis**: Navigate complex corporate structures automatically
- **Shell Company Identification**: Detect and flag shell companies
- **KYC/CDD Compliance**: Automated due diligence workflows
- **Visual Network Mapping**: Interactive investigation tools

#### Insider Trading Detection
- **Temporal Correlation**: Link communications to trades within 48 hours
- **Multi-Lingual Analysis**: Process communications in 50+ languages
- **Network Relationship Mapping**: Identify family, friends, colleagues
- **Behavioral Anomaly Detection**: Flag unusual trading patterns

#### Trade-Based Money Laundering (TBML)
- **Circular Trading Detection**: Identify 10+ hop circular patterns
- **Price Manipulation**: Detect over/under-invoicing
- **Correspondent Banking**: Analyze multi-bank transaction chains
- **Sanctions Screening**: Integrate with OFAC and other watchlists

### 1.3 How It Works

```
1. Data Ingestion
   ↓
2. Graph Construction (entities + relationships)
   ↓
3. Pattern Detection (ML/AI algorithms)
   ↓
4. Alert Generation (suspicious activities)
   ↓
5. Investigation (analyst review)
   ↓
6. Action (SAR filing, account blocking, etc.)
```

### 1.4 Key Benefits

| Benefit | Impact |
|---------|--------|
| **Faster Detection** | 10x faster than traditional systems (minutes vs. hours) |
| **Higher Accuracy** | 95% detection accuracy (vs. 70% traditional) |
| **Fewer False Positives** | 70% reduction in false positives |
| **Better Insights** | Network analysis reveals hidden connections |
| **Automated Compliance** | Automated SAR/CTR generation and filing |

---

## 2. Getting Started

### 2.1 Accessing the Platform

**Web Interface**: http://localhost:8001 (or your organization's URL)

**Login Credentials**:
- Username: [Your email]
- Password: [Provided by IT]
- MFA: [Required for production]

**First-Time Login**:
1. Navigate to platform URL
2. Enter username and password
3. Complete MFA setup (if required)
4. Review and accept terms of use
5. Complete initial profile setup

### 2.2 User Roles and Permissions

| Role | Permissions | Typical Users |
|------|-------------|---------------|
| **Viewer** | View dashboards and reports | Executives, managers |
| **Analyst** | View + investigate alerts | Business analysts, investigators |
| **Compliance Officer** | View + investigate + file SARs | Compliance team |
| **Administrator** | Full access + user management | IT, platform admins |

**Your Role**: [Check with your manager or IT]

### 2.3 Platform Navigation

**Main Menu**:
- 🏠 **Home**: Dashboard overview
- 🔍 **Investigations**: Active alerts and cases
- 📊 **Analytics**: Advanced analytics and reports
- 📋 **Reports**: Compliance reports and exports
- ⚙️ **Settings**: User preferences and configuration

**Quick Actions**:
- Search: Global search for entities (people, companies, accounts)
- Alerts: View recent alerts and notifications
- Help: Access documentation and support

### 2.4 Dashboard Overview

**Main Dashboard Sections**:

1. **Summary Metrics** (Top)
   - Total alerts (today/week/month)
   - High-priority alerts
   - SARs filed
   - Detection accuracy

2. **Alert Feed** (Left)
   - Recent alerts
   - Priority sorting
   - Quick actions

3. **Visualizations** (Center)
   - Alert trends over time
   - Alert distribution by type
   - Network visualizations

4. **Quick Stats** (Right)
   - System health
   - Processing volume
   - User activity

---

## 3. Common Use Cases

### 3.1 Use Case 1: Investigating Structuring (Smurfing)

**Scenario**: Multiple deposits just below $10K threshold

**Steps**:

1. **Navigate to Alerts**
   - Click "Investigations" in main menu
   - Filter by "Structuring" alert type
   - Sort by priority (High → Low)

2. **Review Alert Details**
   - Click on alert to open details
   - Review summary:
     * Number of transactions
     * Total amount
     * Time period
     * Accounts involved
     * Risk score

3. **Analyze Transaction Pattern**
   - View transaction timeline
   - Check transaction amounts (proximity to $10K)
   - Review transaction locations
   - Identify coordinating accounts

4. **Investigate Network**
   - Click "View Network" button
   - Explore relationships between accounts
   - Identify common owners or beneficiaries
   - Check for shared addresses, phones, devices

5. **Make Decision**
   - **If Suspicious**: File SAR (see Section 3.6)
   - **If False Positive**: Mark as "Not Suspicious" with reason
   - **If Need More Info**: Assign to senior analyst

**Example**:
```
Alert: Structuring Detected
Risk Score: 85/100 (High)

Pattern:
- 15 deposits over 10 days
- Amounts: $9,500 - $9,900 each
- Total: $145,000
- 5 different accounts
- Same IP address for online banking

Action: File SAR (likely structuring)
```

### 3.2 Use Case 2: Discovering Ultimate Beneficial Owners (UBO)

**Scenario**: Identify who ultimately controls a company

**Steps**:

1. **Search for Company**
   - Use global search
   - Enter company name or ID
   - Select company from results

2. **View Ownership Structure**
   - Click "Ownership" tab
   - View ownership tree/graph
   - Identify direct and indirect owners

3. **Analyze Ownership Chain**
   - Follow ownership percentages
   - Identify controlling interests (>25%)
   - Check for circular ownership
   - Flag shell companies

4. **Identify UBOs**
   - Platform automatically highlights UBOs
   - Review UBO profiles
   - Check against sanctions lists
   - Assess risk scores

5. **Generate UBO Report**
   - Click "Generate Report"
   - Select report format (PDF/Excel)
   - Include ownership diagram
   - Export for compliance filing

**Example**:
```
Company: ABC Holdings Ltd
Ownership Chain:
- XYZ Corp (60%) → DEF Trust (80%) → John Smith (100%)
- PQR LLC (40%) → Jane Doe (100%)

UBOs Identified:
1. John Smith (48% indirect ownership)
2. Jane Doe (40% direct ownership)

Action: Complete KYC on both UBOs
```

### 3.3 Use Case 3: Detecting Insider Trading

**Scenario**: Suspicious trading before major announcement

**Steps**:

1. **Navigate to Insider Trading Alerts**
   - Click "Investigations"
   - Filter by "Insider Trading"
   - Review recent alerts

2. **Review Alert Details**
   - Company and announcement details
   - Trading activity timeline
   - Communication analysis
   - Network relationships

3. **Analyze Communication Patterns**
   - Review communications before trades
   - Check for suspicious keywords
   - Analyze sentiment and urgency
   - Identify communication networks

4. **Map Trading Network**
   - View network visualization
   - Identify insider and connections
   - Trace information flow
   - Calculate degrees of separation

5. **Assess Evidence**
   - Temporal correlation (communication → trade)
   - Network proximity to insider
   - Trading volume and timing
   - Profit/loss analysis

6. **Take Action**
   - **If Strong Evidence**: Report to regulators
   - **If Suspicious**: Continue monitoring
   - **If Coincidental**: Close with documentation

**Example**:
```
Alert: Potential Insider Trading
Company: ACME Corp
Announcement: Earnings beat (stock +25%)

Timeline:
- Day -3: Insider (CFO) → Friend (phone call)
- Day -2: Friend → Brother (text message)
- Day -1: Brother buys 10,000 shares
- Day 0: Announcement (stock jumps)
- Day +1: Brother sells (profit: $250,000)

Action: Report to SEC
```

### 3.4 Use Case 4: Identifying Fraud Rings

**Scenario**: Coordinated fraud across multiple accounts

**Steps**:

1. **Navigate to Fraud Alerts**
   - Click "Investigations"
   - Filter by "Fraud Ring"
   - Sort by network size

2. **Review Network Overview**
   - Number of accounts involved
   - Total fraud amount
   - Time period
   - Coordination indicators

3. **Analyze Shared Attributes**
   - Shared devices (device fingerprints)
   - Shared IP addresses
   - Shared phone numbers
   - Shared addresses
   - Similar transaction patterns

4. **Visualize Network**
   - View network graph
   - Identify central nodes (organizers)
   - Identify peripheral nodes (mules)
   - Analyze transaction flows

5. **Assess Coordination**
   - Transaction timing (simultaneous)
   - Transaction amounts (similar)
   - Transaction destinations (same)
   - Communication patterns

6. **Take Action**
   - Block all accounts in network
   - File fraud report
   - Notify law enforcement
   - Recover funds if possible

**Example**:
```
Alert: Fraud Ring Detected
Network Size: 25 accounts
Total Fraud: $500,000

Shared Attributes:
- Same IP address (10 accounts)
- Same device fingerprint (15 accounts)
- Similar transaction amounts ($19,500 - $20,500)
- Coordinated timing (within 1 hour)

Action: Block all accounts, file fraud report
```

### 3.5 Use Case 5: Monitoring Trade-Based Money Laundering

**Scenario**: Circular trading with price manipulation

**Steps**:

1. **Navigate to TBML Alerts**
   - Click "Investigations"
   - Filter by "TBML"
   - Review circular trading alerts

2. **Review Trading Chain**
   - View transaction flow diagram
   - Identify circular patterns
   - Calculate total hops
   - Assess complexity

3. **Analyze Price Manipulation**
   - Compare invoice prices to market rates
   - Calculate over/under-invoicing percentage
   - Identify price anomalies
   - Check for justification

4. **Assess Shell Companies**
   - Identify shell companies in chain
   - Check business legitimacy
   - Review ownership structures
   - Assess risk scores

5. **Check Sanctions**
   - Screen all entities against OFAC
   - Check high-risk jurisdictions
   - Review correspondent banks
   - Assess sanctions risk

6. **Take Action**
   - **If TBML Confirmed**: File SAR, block transactions
   - **If Suspicious**: Enhanced monitoring
   - **If Legitimate**: Document justification

**Example**:
```
Alert: Circular TBML Pattern
Chain: A → B → C → D → E → A (5 hops)
Total Value: $10M

Price Manipulation:
- Goods: Electronics
- Market Price: $1,000/unit
- Invoice Price: $2,500/unit (150% markup)
- Justification: None

Shell Companies: 3 of 5 entities
High-Risk Jurisdictions: 2 of 5

Action: File SAR, block transactions
```

### 3.6 Use Case 6: Filing a Suspicious Activity Report (SAR)

**Scenario**: Need to file SAR for suspicious activity

**Steps**:

1. **Navigate to SAR Filing**
   - From alert details, click "File SAR"
   - Or navigate to "Reports" → "File SAR"

2. **Complete SAR Form**
   - **Part I**: Subject Information
     * Name, address, SSN/TIN
     * Account numbers
     * Relationship to institution
   
   - **Part II**: Suspicious Activity Information
     * Activity type (structuring, fraud, etc.)
     * Date range
     * Total amount
     * Description of suspicious activity
   
   - **Part III**: Supporting Documentation
     * Transaction records
     * Communication logs
     * Network diagrams
     * Investigation notes

3. **Review and Validate**
   - Platform validates required fields
   - Reviews for completeness
   - Checks for consistency
   - Suggests improvements

4. **Obtain Approvals**
   - Submit to supervisor for review
   - Address any feedback
   - Obtain final approval
   - Sign electronically

5. **File with FinCEN**
   - Platform files electronically
   - Receives confirmation number
   - Stores confirmation
   - Updates case status

6. **Maintain Confidentiality**
   - Do not notify subject
   - Restrict access to SAR
   - Follow confidentiality procedures

**Timeline**:
- Detection → Filing: Within 30 days
- Platform tracks deadline automatically
- Sends reminders at 20 and 25 days

---

## 4. Dashboard Navigation

### 4.1 Main Dashboard

**URL**: http://localhost:8001/dashboard

**Sections**:

1. **Summary Cards** (Top Row)
   ```
   ┌─────────────┬─────────────┬─────────────┬─────────────┐
   │ Total Alerts│ High Priority│  SARs Filed │  Detection  │
   │     245     │      18      │      12     │    95%      │
   └─────────────┴─────────────┴─────────────┴─────────────┘
   ```

2. **Alert Trends** (Center Left)
   - Line chart showing alerts over time
   - Filter by date range (today, week, month, year)
   - Hover for details

3. **Alert Distribution** (Center Right)
   - Pie chart showing alert types
   - Click slice to filter
   - Shows percentages

4. **Recent Alerts** (Bottom Left)
   - Table of recent alerts
   - Sortable columns
   - Quick actions (view, investigate, close)

5. **Network Visualization** (Bottom Right)
   - Interactive graph of entities
   - Zoom and pan
   - Click nodes for details

### 4.2 Investigations Dashboard

**URL**: http://localhost:8001/investigations

**Features**:

- **Alert List**: All alerts with filters
- **Priority Sorting**: High → Medium → Low
- **Status Filters**: Open, In Progress, Closed
- **Type Filters**: Structuring, Fraud, Insider Trading, TBML
- **Search**: Find specific alerts
- **Bulk Actions**: Close multiple alerts

**Columns**:
- Alert ID
- Type
- Priority
- Risk Score
- Date
- Status
- Assigned To
- Actions

### 4.3 Analytics Dashboard

**URL**: http://localhost:8001/analytics

**Capabilities**:

1. **Custom Queries**
   - Build custom graph queries
   - Save and share queries
   - Export results

2. **Advanced Visualizations**
   - Network graphs
   - Heat maps
   - Sankey diagrams
   - Timeline views

3. **Statistical Analysis**
   - Trend analysis
   - Correlation analysis
   - Anomaly detection
   - Predictive analytics

4. **Benchmarking**
   - Compare to historical data
   - Compare to industry benchmarks
   - Track improvements

### 4.4 Reports Dashboard

**URL**: http://localhost:8001/reports

**Report Types**:

1. **Compliance Reports**
   - SAR summary reports
   - CTR summary reports
   - Audit reports
   - Regulatory submissions

2. **Operational Reports**
   - Alert volume reports
   - Investigation time reports
   - False positive reports
   - User activity reports

3. **Executive Reports**
   - Executive summary
   - KPI dashboard
   - Trend analysis
   - Risk assessment

**Report Actions**:
- Generate on-demand
- Schedule recurring reports
- Export (PDF, Excel, CSV)
- Email distribution

---

## 5. Alert Management

### 5.1 Alert Lifecycle

```
1. Generated → 2. Assigned → 3. Investigating → 4. Resolved → 5. Closed
```

**Status Definitions**:
- **Generated**: Alert created by system
- **Assigned**: Alert assigned to analyst
- **Investigating**: Analyst actively investigating
- **Resolved**: Decision made (SAR filed, false positive, etc.)
- **Closed**: Case closed with documentation

### 5.2 Alert Prioritization

**Priority Levels**:

| Priority | Risk Score | Response Time | Examples |
|----------|-----------|---------------|----------|
| **Critical** | 90-100 | 1 hour | Large-scale fraud, sanctions violations |
| **High** | 75-89 | 4 hours | Structuring, insider trading |
| **Medium** | 50-74 | 1 day | Unusual patterns, minor anomalies |
| **Low** | 0-49 | 3 days | Low-risk alerts, informational |

**Auto-Assignment Rules**:
- Critical → Senior analysts
- High → Experienced analysts
- Medium → All analysts (round-robin)
- Low → Junior analysts

### 5.3 Investigation Workflow

**Standard Workflow**:

1. **Review Alert**
   - Read alert summary
   - Check risk score
   - Review evidence

2. **Gather Information**
   - Query additional data
   - Review transaction history
   - Check customer profile
   - Analyze network

3. **Analyze Evidence**
   - Assess suspicious indicators
   - Consider legitimate explanations
   - Calculate risk score
   - Document findings

4. **Make Decision**
   - File SAR (if suspicious)
   - Mark false positive (if not suspicious)
   - Escalate (if uncertain)
   - Request more information

5. **Document**
   - Record investigation notes
   - Attach supporting documents
   - Update case status
   - Close case

**Investigation Time Targets**:
- Critical: 4 hours
- High: 1 day
- Medium: 3 days
- Low: 5 days

### 5.4 Escalation Procedures

**When to Escalate**:
- Uncertain about decision
- Complex case requiring expertise
- High-value or high-profile case
- Potential legal implications
- Deadline approaching

**Escalation Path**:
1. Analyst → Senior Analyst
2. Senior Analyst → Compliance Officer
3. Compliance Officer → Chief Compliance Officer
4. Chief Compliance Officer → Executive Management

**How to Escalate**:
- Click "Escalate" button in alert
- Select escalation reason
- Add notes explaining situation
- System notifies next level
- Case reassigned automatically

---

## 6. Report Generation

### 6.1 Standard Reports

**Available Reports**:

1. **SAR Summary Report**
   - All SARs filed in period
   - Summary statistics
   - Trend analysis

2. **Alert Volume Report**
   - Alerts by type
   - Alerts by priority
   - Alerts by status
   - Trend over time

3. **Investigation Performance Report**
   - Average investigation time
   - Cases closed
   - False positive rate
   - Analyst productivity

4. **Risk Assessment Report**
   - Overall risk score
   - Risk by category
   - High-risk entities
   - Risk trends

### 6.2 Custom Reports

**Creating Custom Reports**:

1. **Navigate to Reports**
   - Click "Reports" in main menu
   - Click "Create Custom Report"

2. **Select Data Sources**
   - Choose entity types (persons, accounts, transactions)
   - Select time period
   - Apply filters

3. **Choose Metrics**
   - Select metrics to include
   - Configure aggregations
   - Set thresholds

4. **Design Layout**
   - Choose visualizations
   - Arrange sections
   - Add branding

5. **Save and Schedule**
   - Save report template
   - Schedule recurring generation
   - Set up email distribution

### 6.3 Exporting Data

**Export Formats**:
- **PDF**: For sharing and printing
- **Excel**: For further analysis
- **CSV**: For data import
- **JSON**: For API integration

**Export Process**:
1. Navigate to report or data view
2. Click "Export" button
3. Select format
4. Choose options (date range, filters)
5. Click "Download"
6. File downloads to your computer

**Export Limits**:
- Maximum 100,000 rows per export
- For larger exports, contact administrator

---

## 7. Best Practices

### 7.1 Investigation Best Practices

1. **Be Thorough**
   - Review all available evidence
   - Check multiple data sources
   - Consider alternative explanations
   - Document your reasoning

2. **Be Timely**
   - Respond to alerts promptly
   - Meet investigation deadlines
   - Escalate if needed
   - Don't let cases go stale

3. **Be Objective**
   - Base decisions on evidence
   - Avoid assumptions
   - Consider context
   - Be consistent

4. **Be Compliant**
   - Follow procedures
   - Maintain confidentiality
   - Document everything
   - File SARs when required

### 7.2 Documentation Best Practices

1. **Be Clear**
   - Write clearly and concisely
   - Use proper grammar
   - Avoid jargon
   - Be specific

2. **Be Complete**
   - Include all relevant facts
   - Attach supporting documents
   - Explain your reasoning
   - Note any limitations

3. **Be Accurate**
   - Verify facts
   - Double-check numbers
   - Cite sources
   - Correct errors promptly

4. **Be Organized**
   - Use consistent format
   - Follow templates
   - Label attachments
   - Maintain chronology

### 7.3 Confidentiality Best Practices

1. **Protect SAR Information**
   - Never disclose SAR filing to subject
   - Restrict access to need-to-know
   - Use secure communication channels
   - Follow confidentiality procedures

2. **Protect Customer Information**
   - Access only what you need
   - Don't share unnecessarily
   - Use secure systems
   - Follow privacy policies

3. **Protect Investigation Information**
   - Don't discuss cases publicly
   - Use secure workspaces
   - Lock your computer
   - Shred sensitive documents

### 7.4 Performance Tips

1. **Use Filters**
   - Filter alerts by priority
   - Filter by type
   - Filter by date
   - Save common filters

2. **Use Shortcuts**
   - Learn keyboard shortcuts
   - Use quick actions
   - Bookmark frequent pages
   - Customize dashboard

3. **Stay Organized**
   - Keep cases up to date
   - Close completed cases
   - Use notes effectively
   - Maintain clean workspace

4. **Continuous Learning**
   - Attend training sessions
   - Read documentation
   - Learn from colleagues
   - Stay current on regulations

---

## 8. Troubleshooting

### 8.1 Common Issues

**Issue**: Can't log in
- **Solution**: Check username/password, reset if needed, contact IT

**Issue**: Alert not loading
- **Solution**: Refresh page, clear cache, try different browser

**Issue**: Export failing
- **Solution**: Reduce date range, check file size, contact support

**Issue**: Slow performance
- **Solution**: Close unused tabs, clear cache, check network

### 8.2 Getting Help

**Documentation**:
- This user guide
- Online help (click "?" icon)
- Video tutorials
- FAQ

**Support**:
- **Email**: support@example.com
- **Phone**: 1-800-XXX-XXXX
- **Chat**: Click chat icon in platform
- **Ticket**: Submit support ticket

**Training**:
- New user training (required)
- Advanced training (optional)
- Webinars (monthly)
- One-on-one coaching (available)

---

## 9. Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **AML** | Anti-Money Laundering |
| **BSA** | Bank Secrecy Act |
| **CTR** | Currency Transaction Report |
| **EDD** | Enhanced Due Diligence |
| **FinCEN** | Financial Crimes Enforcement Network |
| **KYC** | Know Your Customer |
| **OFAC** | Office of Foreign Assets Control |
| **SAR** | Suspicious Activity Report |
| **TBML** | Trade-Based Money Laundering |
| **UBO** | Ultimate Beneficial Owner |

### Appendix B: Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Global search |
| `Ctrl+N` | New investigation |
| `Ctrl+S` | Save notes |
| `Ctrl+E` | Export current view |
| `Ctrl+F` | Find in page |
| `Esc` | Close modal |

### Appendix C: Alert Type Reference

| Alert Type | Description | Priority | Response Time |
|------------|-------------|----------|---------------|
| **Structuring** | Multiple transactions below threshold | High | 4 hours |
| **Fraud Ring** | Coordinated fraud network | Critical | 1 hour |
| **Insider Trading** | Trading on non-public information | High | 4 hours |
| **TBML** | Trade-based money laundering | High | 4 hours |
| **Sanctions** | OFAC or sanctions violation | Critical | 1 hour |
| **Unusual Activity** | Anomalous transaction pattern | Medium | 1 day |

---

**Document Classification**: User Guide  
**Confidentiality**: Internal Use Only  
**Version**: 1.0  
**Date**: 2026-02-19  
**Next Review**: 2026-08-19 (Semi-annual)  
**Owner**: Product Management

---

**End of Business User Guide**