# Quality of Dutch Government
## Tech Demo Feature List

**Institute for Government Quality Research | Utrecht University**

---

### Overview

A web-based research tool that translates qualitative Dutch government audit reports into quantitative performance indicators using AI/LLM technology. The system enables citizen feedback collection while providing researchers with analytical tools to study government performance.

---

## End-User Features

### AI-Powered Chat Interface
- **Conversational Q&A** — Ask natural language questions about Dutch government quality and performance
- **Topic & Subtopic Filtering** — Filter queries by government domain (Defence, Climate, etc.) and specific subtopics
- **Source Citations** — Every response includes collapsible source references with document names and chunk locations
- **Smart Query Routing** — Agent validates queries against available sources before responding; informs users when no matching documents exist

### Satisfaction Rating System
- **5-Point Likert Scale** — Rate government performance after each response (Very dissatisfied → Very satisfied)
- **Response Quality Score (RQS)** — System calculates quality metrics based on source citations and response relevance
- **Verified Responses** — Responses meeting quality thresholds are automatically flagged as verified

### Privacy & Transparency
- **No Chat Storage** — Conversations exist only in browser session and are never saved
- **Anonymized Data** — Only aggregated, anonymized summaries stored for research
- **GDPR Compliant** — Clear privacy notice explaining data handling
- **Session-Based** — Anonymous session IDs, no personal identifiers

---

## Researcher Features

### Data Table Dashboard
- **Real-Time Database Connection** — Live indicator showing DB status
- **Advanced Filtering** — Filter by date range, topic, user, and verification status
- **Full-Text Search** — Search across all columns
- **User-Normalized Metrics** — Prevents single users from skewing results (one vote per user-topic pair)
- **Summary Metrics Row** — Total records, avg. satisfaction (raw & normalized), quality score, verified %, unique users

### Interactive Visualizations
*Note: Currently displays demo data; database integration pending*

- **Time Series Charts** — Satisfaction trends over time, grouped by topic/source/period
- **Distribution Analysis** — Topic pie charts, satisfaction histograms, source breakdowns
- **Comparison Views** — Box plots by topic, grouped bar charts by source & verification
- **Correlation Analysis** — Heatmaps showing topic relationships, satisfaction vs. quality scatter plots
- **Color Scheme Options** — Choose between Dutch Theme (UU yellow/blue) or Rainbow (vibrant spectrum) color palettes

### Data Export
- **Multiple Formats** — Export filtered data as CSV, Excel, or JSON
- **Customizable Columns** — Select which fields to include
- **Date-Stamped Files** — Automatic timestamping for version control

### Feedback Management
- **Centralized View** — All user feedback in one place
- **Type Classification** — Bug reports, feature requests, general feedback, data quality issues
- **Filtering & Search** — Filter by type and date range
- **Card & Table Views** — Expandable cards or traditional table format

---

## Backend & RAG System

### Document Ingestion Pipeline
- **Automated PDF Processing** — Extract text from PDFs (PyMuPDF/pypdf)
- **Smart Chunking** — Character-based chunking with configurable overlap
- **Document Summaries** — LLM-generated summaries for each document
- **Topic Auto-Classification** — Automatic topic/subtopic labeling via LLM

### Retrieval-Augmented Generation (RAG)
- **Keyword-Based Retrieval** — Efficient chunk retrieval with keyword ranking
- **Subtopic Filtering** — Retrieve only relevant chunks based on selected subtopics
- **Context Formatting** — Automatic source formatting for LLM context window
- **Summary-First Retrieval** — Agent checks document summaries before detailed chunk retrieval

### LLM Integration
- **Ollama Backend** — Local LLM deployment (Llama 3.2)
- **Agent + LLM Architecture** — Separate agent for query analysis and LLM for response generation
- **Synthesis Pipeline** — User prompt → LLM response → Synthesis → Verification → DB Storage
- **Configurable Context Window** — Optimized for performance

---

## Authentication & Security

### User Management
- **Role-Based Access** — End-User vs. Researcher access levels
- **Email/Password Auth** — Secure registration with validation
- **Password Requirements** — Minimum length, alphanumeric requirements
- **Researcher Accounts** — Manual admin creation for researcher access

### Session Management
- **Secure Session State** — Streamlit session-based authentication
- **Full Page Refresh on Logout** — Clean session clearing
- **Demo Credentials** — Built-in test accounts for demonstration

---

## User Interface

### Design System
- **Utrecht University Branding** — UU yellow (#FFCD00), Dutch blue theme
- **Dark Mode** — Professional dark gradient background
- **Material Design Icons** — Consistent iconography throughout
- **DM Sans / Space Mono Typography** — Modern, readable fonts

### UX Features
- **Fragment-Based Updates** — Chat interactions don't cause full page reloads
- **Responsive Layout** — Works across different screen sizes
- **Status Badges** — Real-time API/DB connection indicators with pulse animations
- **Collapsible Sections** — Expanders for sources, privacy notices, help text

---

## Data Sources

### Currently Ingested
- **Defence Reports** — 24 documents (submarines, military budget, cybersecurity, etc.)
- **Climate Reports** — 11 documents (energy transition, citizen council, policy analysis)

### Supported Sources
- Dutch Court of Audit (Algemene Rekenkamer)
- Auditdienst Rijk (Internal Auditor)
- IOB (Policy Evaluation)

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| Database | SQLite (local) / PostgreSQL (production) |
| LLM | Ollama (Llama 3.2) |
| PDF Processing | PyMuPDF, pypdf |
| Visualizations | Plotly |
| Auth | Custom session-based |
| Export | pandas, openpyxl |

---

## Key Metrics Tracked

| Metric | Description |
|--------|-------------|
| Satisfaction (Raw) | Direct 1-5 Likert rating |
| Satisfaction (Normalized) | User-weighted average per topic |
| Response Quality Score | Source citation + relevance measure |
| Verification Flag | Automatic quality threshold check |

---

*Built by DSPG Project Group A — Utrecht University*  
*December 2025 – January 2026*