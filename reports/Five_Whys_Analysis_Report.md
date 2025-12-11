# Five Whys Analysis Report
## Root Cause Analysis: Public Trust in Dutch Government

**Project:** DSPG Project Group A - Quality of Government  
**Date:** December 2024  
**Methodology:** Five Whys Root Cause Analysis

---

## Executive Summary

This report documents our Five Whys analysis conducted to understand the root causes of declining public trust in the Dutch government. This analysis informed our "How Might We" question and shaped our proposed solution approach.

---

## Background

### The Problem Statement

From the vision document *"Visie Instituut Kwaliteit van de Overheid"*:

> *"De afgelopen jaren is er heel veel kritiek geweest op 'de' overheid en op de resultaten van 'het' overheidsbeleid. Ten dele is dat volkomen terecht."*
>
> *(In recent years there has been a lot of criticism of 'the' government and the results of 'the' government policy. To some extent, this is completely justified.)*

### Methodology

The Five Whys is a root cause analysis technique where each answer prompts a follow-up "why" question, drilling down from symptoms to underlying causes. The final "why" reveals the root cause to be addressed.

---

## Five Whys Analysis

### Main Issue
**People are not satisfied with / do not trust the government.**

---

### Why 1: Dissatisfaction with Solutions

**Question:** Why are people not satisfied with the government?

**Answer:** Because they are **not satisfied with the solutions for the problems in society**.

**Evidence:** According to SCP research (April 2023), 6 out of 10 Dutch citizens are dissatisfied with politics.

> *"Mensen zijn negatief over wat de politiek bereikt: men verwijt politici (vooral de regering) gebrek aan daadkracht en visie bij het oplossen van de problemen die in Nederland spelen."*
>
> *(People are negative about what politics achieves: politicians (especially the government) are blamed for a lack of decisiveness and vision in solving the problems facing the Netherlands.)*

**Source:** [SCP Research - 6 op de 10 Nederlanders ontevreden over politiek](https://www.scp.nl/actueel/nieuws/2023/04/20/scp-6-op-de-10-nederlanders-ontevreden-over-politiek)

---

### Why 2: Citizens Feel Unheard

**Question:** Why are people not satisfied with the solutions?

**Answer:** **People don't feel heard** — politicians don't listen well enough to understand the exact pain points in problems, leading to inefficient solutions.

**Key Insight:** There is a perceived large distance between "Den Haag" (the political center) and ordinary people.

> *"...vinden dat de politiek onbetrouwbaar is en dat politici blijven zitten, hoeveel fouten ze ook maken."*
>
> *(...they find politics unreliable and that politicians stay in their positions no matter how many mistakes they make.)*

**Evidence:**
- Structural disconnect between political representatives and constituents
- Dutch youth systematically feel unheard by politics

**Sources:**
- [Ipsos - Nederlandse jongeren voelen zich niet gehoord](https://www.ipsos-publiek.nl/actueel/nederlandse-jongeren-voelen-zich-structureel-niet-gehoord-door-de-politiek/)
- [SCP - Burgerperspectieven 2024](https://www.scp.nl/documenten/2024/04/25/burgerperspectieven-2024-bericht-1)

---

### Why 3: Short-Term Political Thinking

**Question:** Why don't politicians listen well enough to develop effective solutions?

**Answer:** **Political games and reelection concerns take priority** over developing long-term solutions. Short-term solutions that boost popularity are favored over long-term, effective solutions that might be initially unpopular.

**Key Insight:** The political incentive structure rewards short-term wins over sustainable policy development.

**Evidence:** Research from Utrecht University documents the prevalence of short-term thinking in Dutch politics.

> Short-term thinking in Dutch politics comes at the expense of the longer term.

**Sources:**
- [UU - Het kortetermijndenken in de Nederlandse politiek](https://www.uu.nl/nieuws/het-kortetermijndenken-in-de-nederlandse-politiek-gaat-ten-koste-van-de-langere-termijn)
- [UU Research Report - Short-termism in de Nederlandse politiek](https://www.uu.nl/sites/default/files/Short-termism%20in%20de%20Nederlandse%20politiek%20-%20The%20Politics%20and%20Society%20Lab.pdf)
- [PWC - Denken op korte termijn wint](https://www.pwc.nl/nl/themas/blogs/denken-op-korte-termijn-wint-het-van-langetermijnvisie.html)

---

### Why 4: One-Liners Over Nuance

**Question:** Why do politicians prioritize short-term popularity?

**Answer:** **Good one-liners have become more important/influential** than presenting a complete and nuanced picture of problems.

**Key Insight:** Political communication has shifted toward soundbites that resonate immediately rather than comprehensive explanations that require engagement and reflection.

**Evidence:** SCP research shows public frustration with the harsh tone and extreme statements in political and public debate.

**Source:** [SCP - Ergernis over harde toon](https://www.scp.nl/actueel/nieuws/2022/12/29/ergernis-over-harde-toon-en-extreme-uitingen-in-politieke-en-publieke-debat)

---

### Why 5: Media Incentive Structure (ROOT CAUSE)

**Question:** Why have one-liners become more influential than nuanced communication?

**Answer:** **Media is rewarded based on attention, not quality.** Doom and gloom sells better, so negative coverage dominates. This gives people a subjective, colored picture of problems rather than an objective understanding.

**Root Cause Identified:** The media ecosystem's incentive structure rewards sensationalism over accuracy, creating a distorted public perception of government performance.

**Key Insight:** The negativity bias in media coverage does not necessarily reflect the reality of the current state of government. Citizens receive a filtered view that emphasizes failures over successes.

---

## Visual Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FIVE WHYS ANALYSIS FLOW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  SYMPTOM: Low public trust in government                                │
│                          │                                              │
│                          ▼                                              │
│  WHY 1: Dissatisfaction with policy solutions                          │
│                          │                                              │
│                          ▼                                              │
│  WHY 2: Citizens feel unheard by politicians                           │
│                          │                                              │
│                          ▼                                              │
│  WHY 3: Short-term political thinking dominates                        │
│                          │                                              │
│                          ▼                                              │
│  WHY 4: One-liners valued over nuanced discourse                       │
│                          │                                              │
│                          ▼                                              │
│  WHY 5 (ROOT): Media rewards attention over quality                    │
│              → Doom & gloom sells                                       │
│              → Subjective, negative perception created                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## How Might We Question

Based on this root cause analysis, we formulated our guiding design question:

> **How might we present, explain and nuance the current government performance data and make it easily accessible, appealing and understandable to the voter?**

---

## Proposed Solution Concept

### Overview

A **RAG (Retrieval-Augmented Generation) model** trained on a database of government documents, including:
- Policy information
- Party plans
- Government performance reports

### Key Features

| Feature | Description |
|---------|-------------|
| **User Interface** | Simple, intuitive design similar to modern LLMs |
| **Input** | Users ask questions or express concerns about government policies |
| **Output** | Objective explanations of current government actions based on documented sources |
| **Feedback Loop** | Post-conversation reports summarizing user concerns for government feedback |

### Value Proposition

1. **Counter media bias** — Present objective, document-based information
2. **Make citizens feel heard** — Direct channel for questions and concerns
3. **Create feedback mechanism** — User concerns become performance indicators
4. **Increase accessibility** — Complex government data made understandable

### Target Outcomes

- Bridge the gap between "Den Haag" and citizens
- Provide nuanced information vs. media soundbites
- Help citizens understand what government is actually doing
- Generate actionable feedback for policymakers

---

## Supporting Data

### Dissatisfaction Statistics

**Source:** CBS Open Data - Ontevredenheidcijfers

[Dataset: Satisfaction with Democracy](https://opendata.cbs.nl/#/CBS/nl/dataset/84994NED/table)

### Key Research Sources Summary

| Topic | Source | Key Finding |
|-------|--------|-------------|
| Political dissatisfaction | SCP 2023 | 60% dissatisfied |
| Youth alienation | Ipsos | Structural disconnect |
| Short-termism | UU Research | Long-term neglected |
| Public debate quality | SCP 2022 | Frustration with tone |

---

## Guiding Questions for Development

### Core Problem Questions (Dutch)

| Question | Translation |
|----------|-------------|
| Waarom is kwaliteit van de overheid belangrijk? | Why is quality of government important? |
| Wie bepaald wat kwaliteit/goed is? | Who determines what quality/good is? |
| Wat is goed bestuur? | What is good governance? |
| Wie vind het belangrijk? | Who finds it important? |
| Wat maakt iets beter of slechter? | What makes something better or worse? |
| Voor wie doen we het? | For whom are we doing this? |
| Wat is het probleem? | What is the problem? |
| Hoe wordt het in andere landen gedaan? | How is it done in other countries? |

### Root Issue Identified

**Why no centralized place for data access?**
→ Many parties have their own insights  
→ Why are there many parties?  
→ Various institutional and historical reasons  

---

## Conclusion

The Five Whys analysis revealed that the **root cause** of public dissatisfaction with government is not primarily the government's actual performance, but rather the **media ecosystem's incentive structure** that rewards sensationalism over accuracy.

This insight shifts our solution focus from improving government performance measurement alone to **improving how government performance is communicated and understood** by citizens.

Our proposed solution — an accessible, document-based information system — directly addresses this root cause by:
1. Bypassing sensationalist media filters
2. Providing objective, source-backed information
3. Creating a two-way communication channel
4. Making complex data accessible and understandable

---

## Next Steps

1. Validate root cause analysis with stakeholders
2. Develop user personas for the information tool
3. Identify priority document sources for the RAG model
4. Design user interface prototypes
5. Establish metrics for measuring impact on user understanding

---

*Analysis conducted by DSPG Project Group A*  
*Methodology: Five Whys Root Cause Analysis*

