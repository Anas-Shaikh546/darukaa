**🌿 Darukaa — Biodiversity Intelligence Platform**

*Transforming Multi-Faceted Environmental Observations into Verifiable, Scientifically Grounded Ecological Strategies*

---

### **Live Platform Architecture & Access Points**

* **Web Application Interface:** [https://darukaa-rho.vercel.app/](https://darukaa-rho.vercel.app/)
* **API Service Engine:** [https://darukaa-d6d1.onrender.com](https://darukaa-d6d1.onrender.com)
* **API Health Monitor:** [https://darukaa-d6d1.onrender.com/health](https://darukaa-d6d1.onrender.com/health) `(Returns: {"status": "ok"})`

Darukaa operates as a high-reliability, cloud-deployed intelligence platform, orchestrating a **Vercel-hosted React single-page application** and a high-performance **FastAPI microservice** hosted on Render.

---

### **Executive Overview**

Ecological dynamics are inherently multi-variate. A shift in soil organic carbon cascades directly into soil structural integrity and hydrological retention. Rainfall patterns regulate water availability and vegetation stress, while land-use intensity drives habitat fragmentation, spatial connectivity loss, and biodiversity decline.

**Darukaa** is an enterprise-grade Retrieval-Augmented Generation (RAG) platform purpose-built to execute deterministic, evidence-backed reasoning across complex environmental variables.

**System Integration Architecture:**

* **Context Extraction Engine:** Parses multi-variable environmental parameters.
* **Facet-Based ChromaDB RAG:** Retrieves precise domain-specific scientific literature.
* **Deterministic Ecological Graph:** Enforces structured pathway traversal.
* **Multi-Metric Reasoning Framework:** Maps interventions against complex ecological variables.
* **Verification & Validation Pipeline:** Guarantees empirical evidence grounding and strips unsupported numerical claims.
* **Monitoring Matrix Generator:** Formulates temporal indicator plans.

---

### **System Architecture Diagram**

```
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
                         │ SOC / Rainfall /    │
                         │ Land Use / etc.     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │       Retrieval Layer        │
                    │                              │
                    │ Facet-based retrieval from   │
                    │ ChromaDB scientific corpus   │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │  Curated Relationship Graph  │
                    │                              │
                    │ Explicit ecological pathways │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │     Multi-Metric Reasoning   │
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

### **Core Methodology & Engineering Standards**

#### **1. Scientific RAG Layer**

* **Local Knowledge Engine:** ChromaDB high-density vector store.
* **Corpus Metrics:** 16 peer-reviewed scientific source files and 2,735 indexed chunks in core development. The production Render cluster hosts **15 indexed sources and 2,698 chunks** (strictly skipping files lacking required provenance metadata sidecars).
* **Literature Scope:** Peer-reviewed journals and institutional reports covering soil organic carbon, soil health, water availability, precipitation, land use, habitat fragmentation, biodiversity, species richness, agroforestry, environmental disturbance, pollution, and deforestation.
* **Publisher Sources:** FAO, IPCC, Global Soil Partnership, *Nature*, *PNAS*, *PLOS ONE*, *Ecology Letters*, and *Scientific Advances*.

#### **2. Facet-Based Retrieval Engine**

Rather than executing a single high-variance search query, Darukaa decomposes queries into isolated domain facets:

* *Soil Organic Carbon (SOC)*
* *Rainfall / Water Availability*
* *Land-Use Intensity*
* *Habitat Integrity*
* *Biodiversity & Species Metrics*
* *Environmental Pollution / Disturbance*

Retrieval outputs are synthesized using a **deterministic round-robin merge protocol**, preventing similarity score bias across disparate search spaces.

#### **3. Curated Ecological Relationship Graph**

The engine enforces non-probabilistic, explicit relationship mapping to eliminate AI hallucinations while handling context-dependent ecological pressures:

$$\text{SOC} \longrightarrow \text{Soil Structure} \longrightarrow \text{Water Retention} \longrightarrow \text{Plant Survival} \longrightarrow \text{Vegetation} \longrightarrow \text{Habitat Quality} \longrightarrow \text{Biodiversity}$$

$$\text{Land-Use Intensity} \longrightarrow \text{Habitat Fragmentation} \longrightarrow \text{Habitat Connectivity} \longrightarrow \text{Species Movement} \longrightarrow \text{Species Richness}$$

$$\text{Rainfall} \longrightarrow \text{Water Availability} \longrightarrow \text{Species Survival} \longrightarrow \text{Biodiversity}$$

#### **4. Verification & Validation Framework**

* **Context Sufficiency Check:** Enforces a minimum constraint of $\ge 3$ environmental variables before authorizing recommendation generation.
* **Evidence Grounding Verification:** Validates that outputs map directly to retrieved chunk payloads.
* **Numerical Claim Integrity:** Automatically redacts quantitative targets unsupported by evidence text.
* **Bounded Retry Protocol:** Executes a single, controlled high-k retrieval attempt (`top_k=20`) if validation constraints are violated.

---

### **Interactive Multi-Turn Dialogue Model**

When initial inputs lack sufficient variable density, Darukaa pauses execution to gather parameters:

```text
User: 
"My soil organic carbon is 0.8% and rainfall is low."

Darukaa: 
"To reason about biodiversity impacts, what is the current land use or crop system?"

User: 
"I grow wheat as a monoculture."

Darukaa: 
[Executes full analysis: SOC + Rainfall + Land-Use Intensity]

```

---

### **Execution Workflow Example**

* **User Input Constraints:** Soil Organic Carbon = 0.8% | Rainfall Category = Low | Land Use = Wheat Monoculture
* **Detected Parameters:** `SOC`, `Rainfall`, `Land-use intensity`
* **Constructed Pathways:**
* $\text{SOC} \rightarrow \text{Soil Structure} \rightarrow \text{Water Retention} \rightarrow \text{Plant Survival} \rightarrow \text{Vegetation} \rightarrow \text{Habitat Quality} \rightarrow \text{Biodiversity}$
* $\text{Rainfall} \rightarrow \text{Water Availability} \rightarrow \text{Species Survival} \rightarrow \text{Biodiversity}$
* $\text{Land-Use Intensity} \rightarrow \text{Habitat Fragmentation} \rightarrow \text{Habitat Connectivity} \rightarrow \text{Species Movement} \rightarrow \text{Species Richness}$


* **Validated Recommendation:** *Consider implementing agroforestry to improve ecosystem outcomes.*
* **Impact Metrics:** Soil organic carbon, Soil moisture, Habitat diversity, Species richness.

**Structured Monitoring Plan:**

| Metric | Horizon | Analytical Rationale |
| --- | --- | --- |
| **Soil Organic Carbon** | Medium | Tracks soil-health response to organic matter inputs. |
| **Soil Moisture** | Short | Monitors water retention capacity in low-rainfall environments. |
| **Habitat Diversity** | Medium | Evaluates canopy stratification and vegetative structure recovery. |
| **Species Richness** | Long | Gauges long-term biodiversity stabilization and species recovery. |

---

### **Step-by-Step User Operation Guide**

1. **Access Application Interface:** Navigate to [https://darukaa-rho.vercel.app/](https://darukaa-rho.vercel.app/).
2. **Submit Environmental Context:** Input initial observation metrics (e.g., *"My soil organic carbon is 0.8%, and rainfall is low"*).
3. **Fulfill Clarification Prompts:** Provide missing parameter context (e.g., land-use type, cropping systems, or pollution metrics) when requested.
4. **Verify Parameter Extraction:** Confirm detected variables in the interactive context panel.
5. **Inspect Pathway Graph:** Review the explicit ecological chain connecting variables to interventions.
6. **Audit Scientific Provenance:** Validate underlying source literature, titles, chunk IDs, and source URLs.
7. **Review Intervention Strategy:** Analyze the evidence-backed, contextualized ecological plan.
8. **Execute Monitoring Strategy:** Deploy suggested metric tracking across designated short, medium, and long-term time horizons.

---

### **System Deployment Topology**

```
                 INTERNET USER
                       │
                       ▼
            ┌─────────────────────┐
            │   Vercel Frontend   │
            │ React + TypeScript  │
            │       + Vite        │
            └──────────┬──────────┘
                       │
                       │ HTTPS REST API
                       ▼
            ┌─────────────────────┐
            │   Render Backend    │
            │ FastAPI + Uvicorn   │
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ ChromaDB Knowledge  │
            │ Scientific Corpus   │
            └─────────────────────┘

```

---

### **Repository & Directory Structure**

```
darukaa/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── conversation.py
│   │   │   ├── evidence.py
│   │   │   └── recommendation.py
│   │   ├── services/
│   │   │   ├── retrieval/
│   │   │   │   ├── ingest.py
│   │   │   │   └── retriever.py
│   │   │   └── reasoning.py
│   │   └── main.py
│   ├── diagnostic.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── routes/
│   │   ├── lib/
│   │   └── data/
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

### **Local Environment Setup & Administration**

#### **1. Codebase Initialization**

```bash
git clone https://github.com/Anas-Shaikh546/darukaa.git
cd darukaa

```

#### **2. Backend Service Launch**

```bash
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
# Service: http://localhost:8000 | Health Endpoint: http://localhost:8000/health

```

#### **3. Frontend Application Launch**

```bash
cd frontend
npm install
npm run dev
# Interface: http://localhost:8080 (Targeting VITE_API_URL)

```

#### **4. Knowledge Base Ingestion & Diagnostics**

```bash
# Execute Knowledge Ingestion
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.services.retrieval.ingest

# Run System Retrieval Diagnostics
python diagnostic.py

```

---

### **Hackathon Capability & Compliance Verification**

| Feature Requirement | Status | Technical Implementation Mechanism |
| --- | --- | --- |
| **Conversational AI** | ✅ | FastAPI multi-turn message state management |
| **Scientific RAG** | ✅ | Multi-facet querying against ChromaDB vector store |
| **Vector Database** | ✅ | ChromaDB indexed collection (2,735 chunks / 16 sources) |
| **Environmental Knowledge Layer** | ✅ | Peer-reviewed PDFs, environmental reports, and JSON sidecars |
| **Soil Health Reasoning** | ✅ | Explicit SOC and soil-structure pathways |
| **Land-Use Reasoning** | ✅ | Monoculture and land-use intensity evaluation |
| **Climate/Rainfall Reasoning** | ✅ | Precipitation and moisture-availability tracking |
| **Biodiversity Reasoning** | ✅ | Habitat fragmentation, connectivity, and species richness paths |
| **Multi-Variable Reasoning** | ✅ | Combined traversal across $\ge 3$ environmental parameters |
| **Evidence-Backed Recommendations** | ✅ | RAG-derived recommendation matching |
| **Scientific Provenance** | ✅ | Source and chunk-level evidence metadata |
| **Clarifying Questions** | ✅ | Missing-context detection |
| **Multi-Turn Context** | ✅ | State persistence across clarification cycles |
| **Impacted Metrics** | ✅ | Plausible ecosystem outcome mapping |
| **Monitoring Horizons** | ✅ | Short, medium, and long-term indicator tracking |
| **Structured Output** | ✅ | Pydantic-validated JSON contract outputs |
| **Numerical Claim Validation** | ✅ | Automated regex matching and non-grounded token stripping |
| **Deterministic Evidence Validation** | ✅ | Lexical evidence verification |
| **Live Deployment** | ✅ | Vercel frontend + Render backend |

---

### **Strategic Roadmap & Future Extensions**

1. **Geographic Coordinates:** Integrating spatial overlays to map retrieval results to specific geographic bounds.
2. **Earth Observation Integration:** Supplementing user inputs with satellite-derived vegetative indices and land-cover data.
3. **Localized Species Inventories:** Incorporating regional biodiversity datasets to refine ecological impact assessments.
4. **Expanded Graph Traversal:** Broadening ecological node definitions to encompass macro-climate and hydrology models.
5. **Richer Data Fusion:** Blending structured geospatial datasets into the scientific vector layer.

---

### **Resource Links**

* **GitHub Repository:** [https://github.com/Anas-Shaikh546/darukaa](https://github.com/Anas-Shaikh546/darukaa)
* **Live Deployment:** [https://darukaa-rho.vercel.app/](https://darukaa-rho.vercel.app/)