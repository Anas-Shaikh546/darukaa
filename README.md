**🌿 Darukaa — Biodiversity Intelligence**
*Transforming multi-faceted environmental observations into verifiable, scientifically grounded ecological strategies.*

---

**Executive Overview**

Environmental systems operate through intricately linked ecological pathways rather than isolated metrics. A drop in soil organic carbon destabilizes soil architecture, compromising moisture retention and jeopardizing vegetation survival. Shifts in rainfall dictate regional water availability, while intense land-use patterns exacerbate habitat fragmentation, restricting species migration.

**Darukaa** is a domain-specific Retrieval-Augmented Generation (RAG) system engineered to navigate these complex environmental dynamics. By pairing structured environmental parameters with deterministic ecological relationship graphs and scientific document retrieval, Darukaa bypasses generic, ungrounded advice. The platform evaluates multi-variable conditions to yield auditable, evidence-backed interventions and continuous monitoring frameworks.

---

### **System Architecture & Core Methodology**

```
                         ┌─────────────────────┐
                         │       User          │
                         │ Environmental Query │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   FastAPI Backend   │
                         │ Conversation Layer  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Context Extraction │
                         │ SOC / Rainfall /    │
                         │ Land Use / etc.     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │       Retrieval Layer        │
                    │                              │
                    │ Facet-based scientific      │
                    │ retrieval from ChromaDB      │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   Curated Relationship Graph │
                    │                              │
                    │ Environmental relationships │
                    │ + ecological pathways        │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   Multi-Metric Reasoning     │
                    │                              │
                    │ Variables → Relationships   │
                    │ → Intervention → Metrics    │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ Scientific Evidence          │
                    │ Verification & Validation    │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
              ┌─────────────────────────────────────────┐
              │             Darukaa UI                  │
              │                                         │
              │ Understanding → Reasoning → Evidence   │
              │ → Recommendation → Monitoring          │
              └─────────────────────────────────────────┘

```

The system operates across a hybrid pipeline combining non-probabilistic ecological pathways with vector-backed document retrieval:

* **Scientific RAG Layer:** Powered by ChromaDB, the vector database indexes **2,735 chunked segments** across **16 foundational scientific source files**, including peer-reviewed literature and reports from the FAO, IPCC, Global Soil Partnership, *Nature*, *PNAS*, *PLOS ONE*, *Ecology Letters*, and *Scientific Advances*.
* **Facet-Based Retrieval Strategy:** To prevent high-variance vector searches, incoming inputs are decomposed into discrete environmental facets (e.g., *Soil Organic Carbon*, *Rainfall/Water*, *Land-Use Intensity*, *Habitat/Biodiversity*). Each facet executes an independent lookup, followed by a deterministic round-robin merge to unify evidence without biasing rank by query phrasing.
* **Deterministic Relationship Graph:** Multi-metric reasoning relies on explicit, curated ecological networks rather than unconstrained language model outputs. Interventions map across connected nodes:

$$\text{SOC} \longrightarrow \text{Soil Structure} \longrightarrow \text{Water Retention} \longrightarrow \text{Plant Survival} \longrightarrow \text{Vegetation} \longrightarrow \text{Habitat Quality} \longrightarrow \text{Biodiversity}$$

$$\text{Land-Use Intensity} \longrightarrow \text{Habitat Fragmentation} \longrightarrow \text{Connectivity} \longrightarrow \text{Species Movement} \longrightarrow \text{Species Richness}$$

$$\text{Rainfall} \longrightarrow \text{Water Availability} \longrightarrow \text{Species Survival} \longrightarrow \text{Biodiversity}$$

* **Verification & Validation Engine:** Before output delivery, candidate recommendations undergo deterministic checks:
1. **Variable Thresholding:** Ensures $\ge 3$ distinct environmental parameters are present.
2. **Evidence Grounding & Verification:** Confirms candidate claims exhibit substantial lexical alignment with retrieved sources.
3. **Numerical Integrity:** Strips unsupported quantitative projections unless explicitly present in the evidence text.
4. **Bounded Retry Protocol:** Executes a single retrieval retry with expanded context windows (`top_k=20`) if initial verification fails.



---

### **Multi-Turn Conversational Interaction Model**

When provided with incomplete environmental parameters, the interaction model prompts for missing context to satisfy the minimum variable threshold before generating analytical recommendations.

```
User:
"My soil organic carbon is 0.8% and rainfall is low."

Darukaa:
"To reason about biodiversity impacts, what is the current land use or crop system?"

User:
"I grow wheat as a monoculture."

Darukaa:
[Executes multi-variable context processing, facet retrieval, graph traversal, verification, and output formatting]

```

---

### **System Components & Repository Topology**

```
darukaa/
│
├── backend/
│   ├── app/
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
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── routes/
│   │   ├── lib/
│   │   └── data/
│   │
│   ├── package.json
│   └── ...
│
├── knowledge/
│   └── raw/
│       ├── scientific PDFs
│       ├── reports
│       └── metadata sidecars
│
└── README.md

```

#### **Technology Stack**

* **Backend Framework:** Python, FastAPI, Pydantic, ChromaDB, Uvicorn
* **Frontend Instrument UI:** React, TypeScript, Vite
* **Knowledge Store:** Scientific PDFs, JSON sidecar metadata (tracking `source`, `title`, `source_url`, `year`, `document_type`, `topic`, `variables`, `location_scope`), and embedded vector indices.

---

### **Example Execution & Analytical Output**

#### **Input State**

* **Soil:** Organic Carbon = 0.8%
* **Climate:** Rainfall Category = Low
* **Land Use:** Wheat Monoculture

#### **System Output**

* **Identified Variables:** `SOC`, `Rainfall`, `Land-use intensity`
* **Grounded Reasoning Paths:**
* $\text{SOC} \rightarrow \text{Soil Structure} \rightarrow \text{Water Retention} \rightarrow \text{Plant Survival} \rightarrow \text{Vegetation} \rightarrow \text{Habitat Quality} \rightarrow \text{Biodiversity}$
* $\text{Rainfall} \rightarrow \text{Water Availability} \rightarrow \text{Species Survival} \rightarrow \text{Biodiversity}$
* $\text{Land-use Intensity} \rightarrow \text{Habitat Fragmentation} \rightarrow \text{Habitat Connectivity} \rightarrow \text{Species Movement} \rightarrow \text{Species Richness}$


* **Validated Recommendation:** *Consider implementing agroforestry to improve ecosystem outcomes.*
* **Impacted Metrics:** Soil organic carbon, Soil moisture, Habitat diversity, Species richness.
* **Retrieved Evidence:** Matched chunks from indexed literature covering agroforestry practices, soil organic carbon dynamics, and agricultural diversification.
* **Structured Monitoring Framework:**

| Metric | Horizon | Rationale |
| --- | --- | --- |
| **Soil Organic Carbon** | Medium | Tracks soil-health response to organic matter inputs. |
| **Soil Moisture** | Short | Monitors water retention improvements in dry conditions. |
| **Habitat Diversity** | Medium | Evaluates structural vegetation strata restoration. |
| **Species Richness** | Long | Gauges macro-level biodiversity recovery over time. |

---

### **Local Deployment & Diagnostic Procedures**

#### **1. Environment Initialization**

```bash
# Clone the codebase
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd darukaa

# Backend setup
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# Frontend setup (in a separate terminal)
cd frontend
npm install
npm run dev

```

* Backend Service: `http://localhost:8000`
* Interface Application: `http://localhost:8080`

#### **2. Knowledge Ingestion Pipeline**

To parse source literature and populate the vector store:

```bash
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.services.retrieval.ingest

```

#### **3. Retrieval Diagnostics**

To run system checks across vector indices, metadata completeness, and merging behavior:

```bash
cd backend
.\.venv\Scripts\Activate.ps1
python diagnostic.py

```

---

### **Hackathon Capability Verification**

| Hackathon Requirement | Capability Status | Implementation Mechanism |
| --- | --- | --- |
| **Conversational AI** | ✅ | FastAPI multi-turn message state management |
| **Scientific RAG** | ✅ | Multi-facet querying against ChromaDB vector store |
| **Vector Database** | ✅ | Indexed collection (2,735 chunks / 16 sources) |
| **Environmental Knowledge Layer** | ✅ | Peer-reviewed PDFs, environmental reports, and JSON sidecars |
| **Soil Health Reasoning** | ✅ | Explicit SOC and soil-structure pathways |
| **Land-Use Reasoning** | ✅ | Monoculture and land-use intensity evaluation |
| **Climate/Rainfall Reasoning** | ✅ | Precipitation and moisture-availability tracking |
| **Biodiversity Reasoning** | ✅ | Habitat fragmentation, connectivity, and species richness paths |
| **Multi-Variable Reasoning** | ✅ | Combined traversal across $\ge 3$ environmental parameters |
| **Evidence-Backed Interventions** | ✅ | RAG-derived recommendation matching |
| **Scientific Provenance** | ✅ | Chunk-level attribution (source, title, page, URL) |
| **Clarifying Questions** | ✅ | Dynamic context checking prior to execution |
| **Multi-Turn Context** | ✅ | State persistence across clarification cycles |
| **Impacted Metrics** | ✅ | Plausible ecosystem outcome mapping |
| **Monitoring Horizons** | ✅ | Short, medium, and long-term indicator tracking |
| **Structured Output** | ✅ | Pydantic-validated JSON contract outputs |
| **Numerical Claim Validation** | ✅ | Automated regex matching and non-grounded token stripping |
| **Deterministic Evidence Validation** | ✅ | Lexical coverage checks against retrieved evidence chunks |

---

### **Future Extensions**

1. **Geographic Coordinates:** Integrating spatial overlays to map retrieval results to specific geographic bounds.
2. **Earth Observation Integration:** Supplementing user inputs with satellite-derived vegetative indices and land-cover data.
3. **Localized Species Inventories:** Incorporating regional biodiversity datasets to refine ecological impact assessments.
4. **Expanded Graph Traversal:** Broadening ecological node definitions to encompass macro-climate and hydrology models.