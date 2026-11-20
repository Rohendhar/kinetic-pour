# Kinetic Pour: Automated Beverage Dispensing Table

**Course:** MECH5051 Senior Design I (2026–2027)  
**Department:** Mechanical Engineering, College of Engineering and Applied Science (CEAS), University of Cincinnati  
**Team W07:** FNU Rohendhar (Lead), Eli Radabaugh, Aron Joseph, Shyam Patel  
**Course Instructor & Advisor:** Dr. Jacob Cress, PE  

---

## 1. Project Overview

Kinetic Pour is an automated, user-influenced beverage dispensing table engineered for commercial hospitality venues, craft taprooms, and boutique lounge suites. The system packages eight food-grade diaphragm pumps, certified NSF-51 fluid lines, an angled convergent dispensing head, and a 24V linear vertical elevator within a clean, finished furniture chassis. 

Customers select and customize beverages using an integrated 7-inch touchscreen HMI. When a pour is commanded, the cup elevator carriage lowers into the table enclosure, dispenses the recipe accurately, and returns the finished glass smoothly to the tabletop surface.

---

## 2. Team Roster & Roles

| Team Member | Major / Course | Primary Responsibilities | Contact |
| :--- | :--- | :--- | :--- |
| **FNU Rohendhar** | Mechanical Engineering (`MECH5051`) | **Team Lead:** Project management, fluidics manifold design, table chassis packaging, and formal proposal coordination. | `rohendrr@mail.uc.edu` |
| **Eli Radabaugh** | Mechanical Engineering (`MECH5051`) | **Electrical Lead:** Arduino Opta micro-PLC ladder logic, 24V/12V power distribution, relay wiring, and safety interlocks. | `radabaer@mail.uc.edu` |
| **Aron Joseph** | Mechanical Engineering (`MECH5051`) | **Procurement Lead:** Bill of Materials (BOM) management, parts ordering, CEAS Innovation Challenge budget reconciliation, and fluid line seals. | `josepha7@mail.uc.edu` |
| **Shyam Patel** | Mechanical Engineering (`MECH5051`) | **Kinematics & Scheduling Lead:** Linear actuator mounting, vertical carriage guide limits, structural analysis, and master project schedule. | `patel8s7@mail.uc.edu` |

---

## 3. Project Directory Structure

The repository is organized into the following standardized structure:

```text
Senior Design/
├── BOM/                                           <-- Official Procurement Lists & Spreadsheets
│   ├── Kinetic_Pour_Procurement_Material_List.xlsx
│   ├── Kinetic_Pour_Procurement_Material_List.csv
│   └── bottling_system_bom.xlsx
│
├── Budget/                                        <-- Grant Applications, Pitch Decks & Funding
│   ├── procurement_and_funding.md
│   ├── CEAS_Innovation_Challenge_Fall2026_Guide.md
│   └── Kinetic_Pour_Innovation_Challenge_Pitch.pptx
│
├── Ideation/                                      <-- Early Brainstorming, Research & Strategy
│   ├── Research/ (ai_and_features.md)
│   ├── Organization/ (Project_Rules.md, Academic Honesty Policy)
│   └── Business/ (commercialization_and_market_strategy.md)
│
├── Design/                                        <-- Engineering Drawings, Models & Schematics
│   ├── CAD/ (nozzle_swing_mechanism_assembly_11x17.pdf / .png)
│   ├── Electrical Design/ (hydraulic_schematic_engineering.png)
│   ├── Lift Mechanism/ (elevator layout drawings, trade studies, system overview)
│   └── Sketches/ (Reserved for concept sketches)
│
├── Meeting Notes/                                 <-- Weekly Team Meeting Agendas & Minutes
│   ├── 2026-08-27_Kickoff_Meeting_Minutes.docx
│   ├── 2026-09-02_Team_Meeting_Minutes.md
│   └── 2026-09-09_Team_Meeting_Minutes.md
│
├── Timeline/                                      <-- Master Schedule, Gantt Charts & Milestones
│   ├── kinetic_pour_gantt_chart.png
│   ├── Master_Gantt_Chart_Fall2026.xlsx
│   └── milestones.md
│
├── Tools/                                         <-- Build Scripts, Utilities & Archives
│   ├── build_capstone_proposal.py
│   ├── generate_gantt_chart.py
│   └── Archive/
│
└── Submissions/                                   <-- Formal Course Deliverables & Peer Reviews
    ├── Innovation Challenge/                      <-- Pitch Deck Presentations & Media
    │   ├── Kinetic_Pour_Innovation_Challenge_Pitch.pptx
    │   ├── Kinetic_Pour_Clean_Pitch_Deck.pptx
    │   ├── Kinetic_Pour_Master_Deck.pptx
    │   ├── Kinetic_Pour_Master_Deck.pdf
    │   └── Innovation Challenge Promotion Slide.pptx
    │
    └── Senior Design Class/                       <-- Course Proposals & Peer Reviews
        ├── Kinetic_Pour_MECH5051_Capstone_Proposal.docx
        ├── Kinetic_Pour_MECH5051_Capstone_Proposal.pdf
        ├── Humiditune_Peer_Review_Team_W08_Tracked.docx
        └── Humiditune_Peer_Review_Team_W08_Tracked.pdf
```
