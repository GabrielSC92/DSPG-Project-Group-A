---
config:
  layout: elk
---
flowchart LR
    subgraph Dashboard["🖥️ Dashboard Layer"]
        subgraph Auth["🔐 Authentication"]
            Login[1. Login/Auth]
            LoginFailed[1a. Incorrect Login]
            DBAccess[2. DB Quant. Access Check]
        end
        
        subgraph EndUserView["👤 End-User View"]
            UserInput[3. User Input]
            UserOutput[4. Response Display]
            SatisfactionPrompt[4a. Satisfaction Prompt 1-10]
            FeedbackBtnUser[💬 Send Feedback Button]
        end
        
        subgraph ResearcherView["🔬 Researcher View"]
            subgraph Sidebar["🗂️ Sidebar Navigation"]
                NavTable[📊 Data Table]
                NavViz[📈 Visualizations]
                NavExport[💾 Export]
            end
            
            FeedbackBtnResearcher[💬 Send Feedback Button]
            
            subgraph TablePage["Page 1: 📊 Data Table"]
                subgraph TableControls["Filters & Controls"]
                    DateFilter[Date Range Filter]
                    TopicFilter[Topic Filter]
                    UserFilter[User ID Filter]
                    SearchBox[Search Box]
                end
                AgGrid[AgGrid Table]
                subgraph DataColumns["Viewable Data"]
                    ColID[ID]
                    ColUserID[User ID]
                    ColDate[Date]
                    ColTopic[Summary - Categorical/Varchar]
                    ColSatisfactionRaw[Satisfaction Raw 1-10]
                    ColSatisfactionNorm[Satisfaction Normalized]
                    ColCorrelation[Correlation Index]
                    ColFlag[Verification Flag]
                    ColOther[Other Metrics]
                end
            end
            
            subgraph VizPage["Page 2: 📈 Visualizations"]
                subgraph VizControls["Visualization Controls"]
                    ChartSelector[Select Chart Type]
                    MetricSelector[Select Metrics]
                    DateRangeViz[Date Range]
                    GroupBy[Group By Options]
                end
                subgraph Charts["Interactive Charts"]
                    TimeSeriesChart[Time Series: Satisfaction Trends]
                    TopicDistChart[Bar/Pie: Topic Distribution]
                    CorrelationHeatmap[Heatmap: Correlation Matrix]
                    UserEngagement[Line: User Engagement Metrics]
                    SatisfactionHist[Histogram: Satisfaction Distribution]
                    BoxPlot[Box Plot: Satisfaction by Topic]
                end
            end
            
            subgraph ExportPage["Page 3: 💾 Export"]
                ExportFormat[Select Format: CSV, Excel, PNG, SVG]
                ExportScope[Select Data/Charts to Export]
                DownloadBtn[Download Button]
            end
            
            PrivacyNote[/"⚠️ No access to raw chat content"/]
        end
        
        subgraph FeedbackModal["📝 Feedback Pop-up Modal"]
            FeedbackTitle[/"Send Feedback to Developers"/]
            FeedbackTextBox[Open Text Box - Multiline]
            FeedbackSubmit[Submit Button]
            FeedbackCancel[Cancel Button]
        end
    end
    
    Login --> DBAccess
    Login --> LoginFailed
    DBAccess --> EndUserView
    DBAccess --> ResearcherView
    
    UserInput -.-> UserOutput
    UserOutput -.-> SatisfactionPrompt
    SatisfactionPrompt -.-> UserInput
    
    FeedbackBtnUser -.-> FeedbackModal
    FeedbackBtnResearcher -.-> FeedbackModal
    
    NavTable -.-> TablePage
    NavViz -.-> VizPage
    NavExport -.-> ExportPage
    
    TableControls --> AgGrid
    DataColumns --> AgGrid
    VizControls --> Charts
    ExportScope --> DownloadBtn
    
    UserInput -.-o BE1(("→ Back-End"))
    BE3(("← Back-End")) o-.- UserOutput
    BE5(("← Back-End: DB Quant")) o-.- AgGrid
    BE6(("← Back-End: DB Quant")) o-.- Charts
    BE7(("← Back-End: Export")) o-.- DownloadBtn
    FeedbackSubmit -.-o BE8(("→ Back-End: Feedback"))
    
    style Dashboard fill:#E3F2FD,stroke:#1976D2,stroke-width:2px
    style Auth fill:#FFF3E0,stroke:#F57C00
    style EndUserView fill:#E8F5E9,stroke:#388E3C
    style ResearcherView fill:#F3E5F5,stroke:#7B1FA2
    style Sidebar fill:#B39DDB,stroke:#673AB7,stroke-width:3px
    style TablePage fill:#E1BEE7,stroke:#7B1FA2,stroke-width:2px
    style VizPage fill:#E1BEE7,stroke:#7B1FA2,stroke-width:2px
    style ExportPage fill:#E1BEE7,stroke:#7B1FA2,stroke-width:2px
    style FeedbackModal fill:#FFF9C4,stroke:#F57F17,stroke-width:3px
    style TableControls fill:#D1C4E9,stroke:#9C27B0
    style VizControls fill:#D1C4E9,stroke:#9C27B0
    style DataColumns fill:#F3E5F5,stroke:#9C27B0
    style Charts fill:#F3E5F5,stroke:#9C27B0
    style LoginFailed fill:#FFCDD2,stroke:#D32F2F
    style DBAccess fill:#FFE0B2,stroke:#F57C00
    style SatisfactionPrompt fill:#C8E6C9,stroke:#388E3C
    style AgGrid fill:#CE93D8,stroke:#7B1FA2
    style PrivacyNote fill:#FFECB3,stroke:#FFA000
    style NavTable fill:#B39DDB,stroke:#673AB7
    style NavViz fill:#B39DDB,stroke:#673AB7
    style NavExport fill:#B39DDB,stroke:#673AB7
    style FeedbackBtnUser fill:#FFF59D,stroke:#F57F17,stroke-width:2px
    style FeedbackBtnResearcher fill:#FFF59D,stroke:#F57F17,stroke-width:2px
    style FeedbackTitle fill:#FFECB3,stroke:#F57F17
    style FeedbackTextBox fill:#FFF9C4,stroke:#FBC02D
    style FeedbackSubmit fill:#AED581,stroke:#689F38,stroke-width:2px
    style FeedbackCancel fill:#FFCDD2,stroke:#D32F2F,stroke-width:2px
    style ColID fill:#E1BEE7
    style ColUserID fill:#E1BEE7
    style ColDate fill:#E1BEE7
    style ColTopic fill:#E1BEE7
    style ColSatisfactionRaw fill:#E1BEE7
    style ColSatisfactionNorm fill:#FFECB3
    style ColCorrelation fill:#B3E5FC
    style ColFlag fill:#FFCDD2
    style ColOther fill:#E1BEE7
    style TimeSeriesChart fill:#E1BEE7
    style TopicDistChart fill:#E1BEE7
    style CorrelationHeatmap fill:#B3E5FC
    style UserEngagement fill:#E1BEE7
    style SatisfactionHist fill:#E1BEE7
    style BoxPlot fill:#E1BEE7
    style DateFilter fill:#D1C4E9
    style TopicFilter fill:#D1C4E9
    style UserFilter fill:#D1C4E9
    style SearchBox fill:#D1C4E9
    style ChartSelector fill:#D1C4E9
    style MetricSelector fill:#D1C4E9
    style DateRangeViz fill:#D1C4E9
    style GroupBy fill:#D1C4E9
    style ExportFormat fill:#D1C4E9
    style ExportScope fill:#D1C4E9
    style DownloadBtn fill:#B39DDB,stroke:#673AB7
    style BE1 fill:#FFE0B2,stroke:#FF9800
    style BE3 fill:#FFE0B2,stroke:#FF9800
    style BE5 fill:#FFE0B2,stroke:#FF9800
    style BE6 fill:#FFE0B2,stroke:#FF9800
    style BE7 fill:#FFE0B2,stroke:#FF9800
    style BE8 fill:#FFE0B2,stroke:#FF9800