# 🌿 Darukaa — Biodiversity Intelligence Platform

> **Transforming Multi-Faceted Environmental Observations into Verifiable, Scientifically Grounded Ecological Strategies**

## 🚀 Live Platform & Access Points

| Service               | Description                              | Endpoint                                                                     |
| --------------------- | ---------------------------------------- | ---------------------------------------------------------------------------- |
| **Web Application**   | Interactive React + TypeScript interface | [darukaa-rho.vercel.app](https://darukaa-rho.vercel.app/)                    |
| **API Service**       | Production FastAPI engine                | [darukaa-d6d1.onrender.com](https://darukaa-d6d1.onrender.com)               |
| **API Health Check**  | Service availability endpoint            | [darukaa-d6d1.onrender.com/health](https://darukaa-d6d1.onrender.com/health) |
| **GitHub Repository** | Source code and system architecture      | [Anas-Shaikh546/darukaa](https://github.com/Anas-Shaikh546/darukaa)          |

Darukaa is deployed as a cloud-based environmental intelligence platform with a **React + TypeScript frontend hosted on Vercel** and a **FastAPI backend hosted on Render**.

The backend connects the conversational layer, scientific retrieval pipeline, deterministic ecological reasoning engine, evidence validation, and environmental monitoring logic.

---

## 🌍 Executive Overview

Environmental systems are interconnected. Changes in **soil organic carbon, rainfall, land use, water availability, habitat structure, and biodiversity** can influence one another through multiple ecological pathways.

Darukaa is designed to **reason across these relationships** rather than treating environmental observations as isolated variables.

### Core Platform Capabilities

* 🔬 **Scientific Retrieval:** Facet-based retrieval from a curated environmental knowledge corpus.
* 🕸️ **Curated Ecological Relationship Graph:** Explicit and traceable ecological reasoning pathways.
* ⚖️ **Multi-Variable Reasoning:** Connects multiple environmental variables before producing recommendations.
* 🛡️ **Evidence Verification:** Validates recommendations against retrieved scientific evidence.
* 💬 **Conversational Clarification:** Requests missing environmental context instead of guessing.
* 📊 **Environmental Monitoring:** Maps recommendations to short-, medium-, and long-term indicators.

> **Goal:** Turn environmental observations into transparent, evidence-grounded ecological strategies that users can inspect, understand, and monitor.

---

# 🧠 How Darukaa Reasons

Darukaa follows a structured intelligence pipeline:

```text
Environmental Query
        ↓
Context Extraction
        ↓
Scientific Retrieval
        ↓
Ecological Relationships
        ↓
Multi-Metric Reasoning
        ↓
Evidence Validation
        ↓
Recommendation
        ↓
Monitoring
```

### Core Intelligence Components

1. **Context Extraction Engine**
   Identifies environmental variables from the user's description, including soil organic carbon, rainfall, land-use intensity, biodiversity, and environmental disturbance.

2. **Facet-Based Scientific Retrieval**
   Decomposes environmental queries into domain-specific facets and retrieves relevant scientific material from the ChromaDB knowledge layer.

3. **Curated Ecological Relationship Graph**
   Uses explicit ecological relationships to construct interpretable reasoning pathways rather than unrestricted model-generated reasoning chains.

4. **Multi-Metric Reasoning Framework**
   Connects multiple environmental variables and maps their relationships to ecological outcomes.

5. **Evidence Verification Pipeline**
   Checks whether the generated recommendation is supported by retrieved scientific evidence.

6. **Monitoring Matrix**
   Maps recommendations to measurable environmental indicators across short-, medium-, and long-term horizons.

---

# 🏗️ System Architecture

```text
                         ┌─────────────────────┐
                         │        User         │
                         │ Environmental Query │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   FastAPI Backend   │
                         │  Conversation Layer │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Context Extraction  │
                         │                     │
                         │ SOC / Rainfall /    │
                         │ Land Use / etc.     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │       Scientific RAG         │
                    │                              │
                    │ Facet-based retrieval from   │
                    │ ChromaDB knowledge corpus    │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │  Curated Ecological Graph    │
                    │                              │
                    │ Explicit ecological          │
                    │ relationship pathways        │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   Multi-Metric Reasoning     │
                    │                              │
                    │ Variables → Relationships →  │
                    │ Intervention → Metrics       │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ Evidence Verification &      │
                    │ Output Validation             │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
              ┌─────────────────────────────────────────┐
              │              Darukaa UI                 │
              │                                         │
              │ Understanding → Reasoning → Evidence   │
              │ → Recommendation → Monitoring          │
              └─────────────────────────────────────────┘
```

---

# 🔬 Core Methodology

## 1. Scientific Knowledge Layer

Darukaa uses a local **ChromaDB vector knowledge layer** containing scientific publications and institutional environmental reports.

### Development Corpus

* **16 scientific source files**
* **2,735 indexed chunks**
* Structured provenance metadata for each source

### Production Corpus

* **15 indexed source files**
* **2,698 indexed chunks**
* Provenance-enforced indexing
* Documents without required metadata sidecars are excluded rather than indexed as anonymous evidence

### Knowledge Domains

The corpus covers:

* Soil organic carbon
* Soil health
* Soil biodiversity
* Water availability
* Rainfall and precipitation
* Land-use intensity
* Habitat fragmentation
* Habitat connectivity
* Biodiversity
* Species richness
* Agroforestry
* Agricultural diversification
* Environmental disturbance
* Pollution
* Deforestation
* Forest management

The corpus includes scientific literature and institutional publications from sources such as **FAO, IPCC, Global Soil Partnership, PLOS ONE, PNAS, Ecology Letters**, and related environmental research.

---

# 🔎 2. Facet-Based Retrieval Engine

Instead of relying on one broad similarity search, Darukaa decomposes an environmental query into meaningful scientific facets.

Example facets include:

* **Soil Organic Carbon**
* **Rainfall / Water Availability**
* **Land-Use Intensity**
* **Habitat Integrity**
* **Biodiversity / Species Metrics**
* **Pollution / Environmental Disturbance**

Each facet retrieves relevant scientific material independently.

The results are combined using a **deterministic round-robin merge strategy**, reducing the risk that one facet dominates the final evidence pool solely because its similarity scores are numerically higher.

---

# 🌱 3. Curated Ecological Relationship Graph

Darukaa uses an explicit relationship graph to make ecological reasoning **traceable and interpretable**.

### Soil Carbon Pathway

```text
SOC
 ↓
Soil Structure
 ↓
Water Retention
 ↓
Plant Survival
 ↓
Vegetation
 ↓
Habitat Quality
 ↓
Biodiversity
```

### Land-Use Pathway

```text
Land-Use Intensity
 ↓
Habitat Fragmentation
 ↓
Habitat Connectivity
 ↓
Species Movement
 ↓
Species Richness
```

### Rainfall Pathways

```text
Rainfall
 ↓
Water Availability
 ├──→ Vegetation Productivity
 │
 └──→ Species Survival
          ↓
      Biodiversity
```

These pathways provide a deterministic reasoning structure that can be exposed directly through the user interface.

---

# 🛡️ 4. Verification & Validation Framework

Darukaa applies multiple validation constraints before accepting a recommendation.

### 1. Context Sufficiency

A recommendation requires at least **3 environmental variables**.

If insufficient information is available, the system asks a clarification question instead of filling in missing values.

### 2. Evidence Grounding

Retrieved scientific evidence must be present before a recommendation is accepted.

### 3. Recommendation Verification

The recommendation is checked against retrieved evidence using deterministic lexical evidence verification.

### 4. Numerical Claim Integrity

Unsupported quantitative claims are detected and removed instead of allowing unsupported numbers into the final response.

### 5. Bounded Retry

If validation fails, Darukaa performs **one controlled higher-k retrieval attempt (`k=20`)** before returning a fallback state.

This keeps the reasoning pipeline bounded and predictable.

---

# 💬 Interactive Multi-Turn Reasoning

Darukaa does not force a recommendation when the environmental context is incomplete.

### Example

**User:**

> My soil organic carbon is 0.8% and rainfall is low.

**Darukaa:**

> To provide an evidence-grounded recommendation, we need at least 3 environmental variables. Could you please share your land use or current crop pattern?

**User:**

> The land is under wheat monoculture.

Darukaa combines:

```text
SOC
+
Rainfall
+
Land-Use Intensity
```

and executes the complete reasoning pipeline.

This enables **clarification-driven environmental reasoning instead of assumption-driven responses**.

---

# 🧪 End-to-End Example

## Input Parameters

* **Soil Organic Carbon:** `0.8%`
* **Rainfall:** `Low`
* **Land Use:** `Wheat Monoculture`

### Detected Variables

```text
SOC
Rainfall
Land-Use Intensity
```

### Constructed Pathways

```text
SOC
→ Soil Structure
→ Water Retention
→ Plant Survival
→ Vegetation
→ Habitat Quality
→ Biodiversity
```

```text
Rainfall
→ Water Availability
→ Species Survival
→ Biodiversity
```

```text
Land-Use Intensity
→ Habitat Fragmentation
→ Habitat Connectivity
→ Species Movement
→ Species Richness
```

### Validated Recommendation

> **Consider agroforestry under low soil-carbon conditions and monoculture land use to support soil organic carbon, water availability and soil moisture, habitat structure, and species richness.**

### Impacted Metrics & Monitoring Matrix

| Metric                  | Monitoring Horizon | Purpose                                              |
| ----------------------- | ------------------ | ---------------------------------------------------- |
| **Soil Organic Carbon** | Medium-term        | Tracks the soil-health response to the intervention. |
| **Soil Moisture**       | Short-term         | Tracks water availability and retention.             |
| **Habitat Diversity**   | Medium-term        | Tracks habitat structure and spatial connectivity.   |
| **Species Richness**    | Long-term          | Tracks the longer-term biodiversity response.        |

---

# 🖥️ User Experience

The Darukaa interface is structured around an explainable intelligence workflow:

```text
Understanding
      ↓
Reasoning
      ↓
Scientific Evidence
      ↓
Recommendation
      ↓
Impact & Monitoring
```

### Interface Inspection Panels

* **Detected Variables** — extracted directly from user-provided context.
* **Ecological Pathways** — visual representation of deterministic graph traversal.
* **Scientific Evidence** — expandable retrieved passages with provenance.
* **Intervention Plan** — recommendation and impacted ecological metrics.
* **Monitoring Grid** — short-, medium-, and long-term environmental indicators.

---

# 🚀 Step-by-Step User Guide

1. **Open the Application**
   Visit [darukaa-rho.vercel.app](https://darukaa-rho.vercel.app/).

2. **Describe the Environmental Situation**
   Enter observations such as:

   > My soil organic carbon is 0.8%, and rainfall is low.

3. **Provide Additional Context**
   Answer clarification prompts about land use, crop patterns, or other environmental conditions.

4. **Review Detected Variables**
   Verify the extracted environmental context in the Understanding panel.

5. **Inspect Ecological Pathways**
   Follow how environmental variables connect to ecological outcomes.

6. **Inspect Scientific Evidence**
   Expand evidence items to review retrieved passages and provenance.

7. **Review the Recommendation**
   Examine the suggested intervention and impacted environmental metrics.

8. **Track Environmental Response**
   Use the suggested indicators across short-, medium-, and long-term horizons.

---

# ☁️ Deployment Architecture

```text
                     INTERNET USER
                           │
                           ▼
              ┌────────────────────────┐
              │    Vercel Frontend     │
              │                        │
              │ React + TypeScript     │
              │ Vite                   │
              └───────────┬────────────┘
                          │
                          │ HTTPS REST API
                          ▼
              ┌────────────────────────┐
              │    Render Backend      │
              │                        │
              │ FastAPI + Uvicorn      │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │       ChromaDB         │
              │ Scientific Knowledge   │
              │ Corpus                 │
              └────────────────────────┘
```

### Production Endpoints

* **Frontend:** https://darukaa-rho.vercel.app/
* **Backend API:** https://darukaa-d6d1.onrender.com
* **Health Check:** https://darukaa-d6d1.onrender.com/health → `{"status":"ok"}`

---

# 📁 Repository Structure

```text
darukaa/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── conversation.py
│   │   │   ├── evidence.py
│   │   │   └── recommendation.py
│   │   │
│   │   ├── services/
│   │   │   ├── retrieval/
│   │   │   │   ├── ingest.py
│   │   │   │   └── retriever.py
│   │   │   │
│   │   │   └── reasoning.py
│   │   │
│   │   └── main.py
│   │
│   ├── diagnostic.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── routes/
│   │   ├── lib/
│   │   └── data/
│   │
│   └── package.json
│
├── knowledge/
│   └── raw/
│       ├── scientific source files
│       └── metadata sidecars
│
└── README.md
```

---

# ⚙️ Local Development

## 1. Repository Setup

```bash
git clone https://github.com/Anas-Shaikh546/darukaa.git
cd darukaa
```

## 2. Backend Initialization

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

**API Engine:** `http://localhost:8000`

**Health Check:** `http://localhost:8000/health`

## 3. Frontend Initialization

```bash
cd frontend
npm install
npm run dev
```

**Client Application:** `http://localhost:8080`

## 4. Data Ingestion & Diagnostics

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.services.retrieval.ingest
python diagnostic.py
```

---

# 🏆 Hackathon Capability Matrix

| Capability                              | Status | Technical Implementation                         |
| --------------------------------------- | ------ | ------------------------------------------------ |
| **Conversational Intelligence**         | ✅      | Multi-turn FastAPI conversation state            |
| **Scientific RAG**                      | ✅      | Facet-based retrieval with ChromaDB              |
| **Vector Knowledge Layer**              | ✅      | Scientific corpus indexed into ChromaDB          |
| **Environmental Knowledge**             | ✅      | Scientific literature and institutional reports  |
| **Soil Health Reasoning**               | ✅      | SOC and soil-function pathways                   |
| **Land-Use Reasoning**                  | ✅      | Land-use intensity and habitat pathways          |
| **Climate Reasoning**                   | ✅      | Rainfall and water-availability pathways         |
| **Biodiversity Reasoning**              | ✅      | Habitat, movement, and species-richness pathways |
| **Multi-Variable Reasoning**            | ✅      | Deterministic reasoning across 3+ variables      |
| **Evidence-Grounded Output**            | ✅      | Retrieved scientific evidence + validation       |
| **Scientific Provenance**               | ✅      | Source and chunk-level metadata                  |
| **Clarifying Questions**                | ✅      | Context sufficiency validation                   |
| **Multi-Turn Context**                  | ✅      | Conversation state across clarification          |
| **Impacted Metrics**                    | ✅      | Environmental outcome mapping                    |
| **Monitoring Horizons**                 | ✅      | Short-, medium-, and long-term indicators        |
| **Structured Output**                   | ✅      | Pydantic-validated response contracts            |
| **Numerical Claim Validation**          | ✅      | Unsupported quantitative-claim filtering         |
| **Deterministic Evidence Verification** | ✅      | Lexical evidence verification                    |
| **Live Cloud Deployment**               | ✅      | Vercel frontend + Render backend                 |

---

# 🔭 Future Extensions

1. **Geographic Intelligence**
   Integrate spatial coordinates and regional GIS data.

2. **Earth Observation**
   Incorporate satellite-derived indicators such as vegetation and soil-moisture observations.

3. **Localized Biodiversity Data**
   Connect regional species distribution and biodiversity datasets.

4. **Expanded Ecological Graph**
   Extend the relationship graph with hydrological, climatic, and ecological pathways.

5. **Structured Data Fusion**
   Combine scientific literature with structured environmental and geospatial datasets.

---

# 🎯 Why Darukaa?

> **Environmental intelligence should be explainable, evidence-grounded, and connected across multiple ecological dimensions.**

Instead of producing an isolated generic answer, **Darukaa**:

**Understands the context → identifies missing information → retrieves scientific evidence → traverses explicit ecological relationships → connects multiple environmental variables → validates the output → identifies measurable environmental indicators.**

The result is an environmental intelligence workflow where users can see **not only what is recommended, but also why the recommendation was produced, which evidence supports it, and what should be monitored afterward.**

---

# 🔗 Resource Links

* 🌐 **Live Application:** https://darukaa-rho.vercel.app/
* ⚡ **Backend Engine:** https://darukaa-d6d1.onrender.com
* 🩺 **API Health Check:** https://darukaa-d6d1.onrender.com/health
* 💻 **Source Code:** https://github.com/Anas-Shaikh546/darukaa
