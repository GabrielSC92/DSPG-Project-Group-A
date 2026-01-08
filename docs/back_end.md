---
config:
  layout: elk
---
flowchart LR
    FE1(("← Front-End")) o-.- Agent[Agent]
    
    subgraph AuthDB["Auth Database"]
        subgraph UsersSchema["Users Table"]
            AuthUserID[User ID - PK]
            AuthEmail[Email]
            AuthPasswordHash[Password Hash]
            AuthAccessLevel[Access Level - End-User/Researcher]
            AuthCreatedDate[Created Date]
            AuthSatisfactionBaseline[Satisfaction Baseline]
            AuthInteractionCount[Interaction Count]
        end
    end
    
    FELogin(("← Front-End: Login")) o-.- AuthDB
    AuthDB -.-o FELoginResult(("→ Front-End: Auth Result"))
    
    Agent --> Check[Check]
    
    Check --> ValidCheck{Valid Check ✅}
    Check --> FailedCheck{Failed Check ❌}
    ValidCheck --> SelectDB[Agent selects DBs based on user prompt]
    
    SelectDB --> DB1[(DB 1 ✅)]
    SelectDB --> DB2[(DB 2 ✅)]
    SelectDB --> DB3[(DB 3 ❌)]
    
    DB1 --> BuildPrompt[Back to Agent: Creates prompt from user query and context]
    DB2 --> BuildPrompt
    
    BuildPrompt --> LLMInput[LLM Receives Input]
    LLMInput --> LLMOutput[LLM Output]
    LLMOutput -.-o FE2(("→ Front-End"))
    FE5(("← Front-End: Satisfaction Score")) o-.- DBQuant
    LLMOutput --> SynthesisAPI[Separate Synthesis LLM/Agent API]
    SynthesisAPI --> Synthesize[Synthesize Topic Summary]
    Synthesize --> DBInsertAPI[DB Quant. Insert API]
    DBInsertAPI --> DBQuant[(DB Quant.)]
    DBQuant --> SimilarityCheck[Compute Correlation Index via Similarity Techniques]
    SimilarityCheck --> Verify{Verify: Correlation Above Threshold?}
    Verify --> VerifyPass[Valid ✅]
    Verify --> VerifyFail[Invalid ❌ - Retry/Flag]
    VerifyPass --> UpdateFlag[Update DB: Flag = True, Store Correlation Index]
    VerifyFail --> UpdateFlag2[Update DB: Flag = False, Store Correlation Index]
    UpdateFlag --> DBQuant
    UpdateFlag2 --> DBQuant
    PrivacyNote[/"⚠️ Raw chat content never stored - only synthesized summaries"/] -.-> Synthesize
    
    subgraph DBQuantSchema["DB Quant. Schema"]
        SchemaID[ID - PK]
        SchemaUserID[User ID - FK]
        SchemaDate[Date]
        SchemaTopic[Summary - Categorical/Varchar]
        SchemaSatisfactionRaw[Satisfaction Raw - Ordinal 1-10]
        SchemaSatisfactionNorm[Satisfaction Normalized - TBD]
        SchemaCorrelation[Correlation Index - Similarity Score]
        SchemaFlag[Verification Flag - Boolean]
        SchemaOther[Other Metrics - Ordinal]
    end
    AuthUserID -.->|FK| SchemaUserID
    
    DBQuant --> DBQuantSchema
    DBQuant -.-o FE3(("→ Front-End: AgGrid"))
    FailedCheck --> FailurePrompt[Failure Prompt for LLM]
    FailurePrompt --> ErrorMsg["LLM: Sorry, we cannot answer this query at this moment..."]
    ErrorMsg -.-o FE4(("→ Front-End"))
    LLMOutput -.-> PromptEng[/"Prompt Engineering: Quantify dissatisfaction (1-10), Synthesize context (50-250w), other metrics"/]
    style ValidCheck fill:#90EE90
    style FailedCheck fill:#FFB6C1
    style PromptEng fill:#FFFACD,stroke:#DAA520
    style DB1 fill:#E8F5E9
    style DB2 fill:#E8F5E9
    style DB3 fill:#FFEBEE
    style DBQuant fill:#E1BEE7
    style DBQuantSchema fill:#F3E5F5,stroke:#9C27B0
    style Synthesize fill:#CE93D8,stroke:#7B1FA2
    style SchemaID fill:#E1BEE7
    style SchemaUserID fill:#E1BEE7
    style SchemaDate fill:#E1BEE7
    style SchemaTopic fill:#E1BEE7
    style SchemaSatisfactionRaw fill:#E1BEE7
    style SchemaSatisfactionNorm fill:#FFECB3
    style SchemaCorrelation fill:#B3E5FC
    style SchemaFlag fill:#FFCDD2
    style SchemaOther fill:#E1BEE7
    style SimilarityCheck fill:#B3E5FC,stroke:#0288D1
    style FE1 fill:#BBDEFB,stroke:#1976D2
    style FE2 fill:#BBDEFB,stroke:#1976D2
    style FE3 fill:#BBDEFB,stroke:#1976D2
    style FE4 fill:#BBDEFB,stroke:#1976D2
    style FE5 fill:#BBDEFB,stroke:#1976D2
    style PrivacyNote fill:#FFECB3,stroke:#FFA000
    style SynthesisAPI fill:#B3E5FC,stroke:#0288D1
    style AuthDB fill:#FFF3E0,stroke:#F57C00
    style UsersSchema fill:#FFE0B2,stroke:#F57C00
    style AuthUserID fill:#FFE0B2
    style AuthEmail fill:#FFE0B2
    style AuthPasswordHash fill:#FFE0B2
    style AuthAccessLevel fill:#C8E6C9,stroke:#388E3C
    style AuthCreatedDate fill:#FFE0B2
    style AuthSatisfactionBaseline fill:#FFECB3
    style AuthInteractionCount fill:#FFE0B2
    style FELogin fill:#FFE0B2,stroke:#FF9800
    style FELoginResult fill:#FFE0B2,stroke:#FF9800
    style DBInsertAPI fill:#B3E5FC,stroke:#0288D1
    style Verify fill:#FFF9C4,stroke:#F9A825
    style VerifyPass fill:#C8E6C9,stroke:#388E3C
    style VerifyFail fill:#FFCDD2,stroke:#D32F2F
    style UpdateFlag fill:#C8E6C9,stroke:#388E3C
    style UpdateFlag2 fill:#FFCDD2,stroke:#D32F2F