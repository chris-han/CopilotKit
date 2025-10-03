

# **Selecting the Optimal Visualization for a Data Story: Decision Processes and AI Automation**

The selection of an appropriate visualization for a data story is a multi-layered decision process that transforms raw data into actionable knowledge. This process is highly formalized, combining strategic communication objectives, empirical cognitive science principles, and structured classification frameworks. The evidence confirms that a standard decision process not only exists but operates hierarchically. Furthermore, sophisticated large language model (LLM) architectures are actively being developed and deployed to automate key stages of this historically manual selection and generation workflow.

## **I. The Imperative of Intent: Visual Selection as Storytelling Strategy**

Effective visualization selection is fundamentally a strategic communication exercise. It requires prioritizing the narrative goal over mere data presentation, ensuring that the chosen visual form effectively guides the audience to a pre-defined conclusion.1 A "data story" is defined as a cohesive narrative that connects data insights with qualitative context and domain expertise, painting a clear and actionable picture.2

### **A. Defining the Data Story: Narrative, Context, and Actionability**

The selection process must begin with a clear definition of purpose. The initial, critical step is to determine the specific question the visualization must answer.4 This focus shifts the goal from simply displaying data to communicating a finding, thereby prioritizing substance over visual novelty or "cute gauges".1

Visualization selection plays a crucial role in the "action funnel," which maps how audience engagement translates into decisive action.6 If the wrong visualization is chosen, the intended message can be obscured. For example, if a chart highlighting a 12-month trend is poorly designed, stakeholders may focus instead on a single data point, such as a record high in the most recent month, completely missing the larger trend that constitutes the story.1 The correct visual design must speak for itself, minimizing the effort required for the audience to decode the core insight.1

The visualization also requires sufficient context to prevent misinterpretation.4 Contextual information includes annotations, baselines, and supporting narrative elements.7 A visualization lacking this context is merely raw data rendered graphically, which can confuse stakeholders and undermine the analyst's credibility.7

### **B. Audience Centricity: Adapting Visuals to Domain Expertise and Cognitive Load**

The characteristics of the intended audience—their technical sophistication, domain expertise, and accessibility needs—must dictate the level of complexity used in the final visualization.8 Complex or innovative chart types, while visually appealing, can introduce unnecessary cognitive load, particularly for general audiences.10 The selection process must maintain simplicity for maximum comprehension.4

If the visual is integrated into an interactive dashboard, the design must also consider the interactivity features to appropriately manage audience engagement and exploration.10 Fundamentally, the ability of an analyst to drive action through data is dependent on the audience’s ability to make sense of the information provided.4

### **C. The Foundational Seven Steps: A Strategic Pre-Visualization Checklist**

A rigorous, standardized process helps transition chart selection from an intuitive process to a governable strategy.4 The selection failure, where the audience misses the intended narrative, often stems not from a technical failure in plotting the data but from a strategic failure to define the clear purpose (Step 1\) or accurately assess the audience (Step 2). If the strategic intent is ambiguous, the visual mapping will necessarily fail to communicate effectively.

This structured methodology provides a governance model for visualization professionals:

Table: Step-by-Step Visualization Design Process

| Step | Action / Goal | Strategic Consideration |
| :---- | :---- | :---- |
| 1 | Define Clear Purpose | What question must the visualization answer? (Actionable Insight) 4 |
| 2 | Know Your Audience | Determine necessary context, technical level, and accessibility needs 8 |
| 3 | Identify Data Relationship | Determine if the goal is Comparison, Distribution, Relationship, or Change over Time 11 |
| 4 | Choose Appropriate Visual | Select a chart type based on the relationship and perceptual hierarchy 4 |
| 5 | Declutter and Simplify | Eliminate non-data ink (chart junk) to minimize cognitive load 7 |
| 6 | Clarify with Color/Text | Use pre-attentive attributes strategically and label clearly to provide context 7 |
| 7 | Test and Iterate | Seek objective feedback to ensure the intended story is clearly discerned 16 |

A crucial element of integrity in this process is accuracy. Distorting the visual representation, such as manipulating the scale or starting the Y-axis at a value other than zero, can exaggerate trends, giving viewers a skewed understanding of the data.7 Similarly, cherry-picking data to fit a favorable narrative or forcing data into a predetermined, visually appealing chart type represents a fundamental breakdown in integrity.7 Since the goal of the process is actionability 4, any ethical misconduct immediately undermines credibility and guarantees a failure in communication.

## **II. Foundational Principles: Cognitive Science and Perceptual Accuracy**

The process of selecting a proper visualization must be scientifically grounded in the empirical reality of how the human brain visually processes graphic elements. This domain, known as Graphical Perception, dictates that effectiveness is achieved through cognitive efficiency, prioritizing charts that align with natural human visual decoding capabilities.17

### **A. The Science of Decoding: Graphical Perception and the Cleveland-McGill Hierarchy**

Effective visual design is described as "more science than art".1 The seminal research by Cleveland and McGill established an empirical ranking of visual variables, determining how accurately and efficiently humans extract quantitative information from graphs.17 This perceptual ranking provides a critical policy layer for chart selection, confirming that charts leveraging more accurate encoding types are inherently superior for quantitative data stories.13

The hierarchy demonstrates that humans excel at judging relative **position on a common scale**, performing better at this task than judging length, direction, angle, area, curvature, or volume.18 Conversely, visual encodings that require the estimation of angles, areas, or volumes are highly error-prone and impose higher cognitive demands.13

Table: The Perceptual Hierarchy of Visual Encoding Accuracy

| Visual Encoding Type | Perceptual Accuracy | Cognitive Efficiency | Associated Chart Examples |
| :---- | :---- | :---- | :---- |
| Position on a Common Scale | Highest | Easiest to judge magnitude and differences. | Scatter Plot, Dot Plot, Bar Chart (aligned axis) 17 |
| Length (Aligned) | High | Excellent for comparing quantitative values. | Bar Chart, Column Chart 13 |
| Angle, Slope, Area | Medium-Low | Requires high cognitive load; prone to estimation error. | Pie Chart, Stacked Area Chart, Bubble Chart 13 |
| Volume, Color Saturation/Hue | Lowest | Difficult to estimate quantitative differences. | 3D Visuals, Choropleth Maps (fine gradients) 13 |

### **B. Visual Encoding Effectiveness: Consequences for Chart Design**

The perceptual hierarchy directly governs the practical choice of chart type. For comparison across many categories, charts that encode value through position, such as Dot Plots (or Cleveland Dot Plots), are highly recommended. Dot plots minimize visual clutter and leverage the most accurate perceptual task, making them a preferred alternative to standard bar charts when emphasizing individual points.17

Conversely, charts relying on low-accuracy attributes are inherently limited. Pie charts, which rely on the estimation of angles, are perceptually inefficient for comparison.17 Bubble charts, which encode quantitative data through area, are similarly error-prone for precise comparisons.13 This difference in inherent perceptual accuracy creates a direct causal link: a choice of low-accuracy encoding increases the cognitive load required by the audience to extract data, which, in turn, detracts from their ability to process the narrative and make a swift, informed decision. This compromises the ultimate goal of making the visualization actionable.4 Organizations should therefore implement governance policies prioritizing charts utilizing position and length for core quantitative communication.

### **C. Harnessing Pre-Attentive Attributes for Immediate Insight**

To further minimize cognitive load, designers utilize pre-attentive attributes—visual properties processed unconsciously by the brain in less than 500 milliseconds.13 These attributes guide attention instantaneously:

1. **Color:** Differences in hue and intensity are highly effective pre-attentive signals for highlighting key data points or distinguishing between categories.13 Color strategically directs the viewer's focus to the most important elements.15  
2. **Size:** Variations in size naturally establish a visual hierarchy, drawing immediate attention to larger elements and intuitively representing magnitude or importance.21

However, the use of pre-attentive cues must be carefully regulated. Excessive, conflicting, or inconsistent use of color or other cues leads to visual clutter, confusion, and ultimately undermines the clarity of the message.13 Color consistency and coherence must be maintained across related visualizations to facilitate seamless interpretation.15

## **III. The Standard Decision Process: Taxonomies and Hierarchical Frameworks**

The selection of a proper visualization follows a structured, two-tiered decision process based on established taxonomies: first classifying the data based on the required *relationship* (technical data type) and then refining the choice based on the desired *narrative goal* (communication pattern).

### **A. The Classification Matrix: Mapping the Four Core Data Relationships (Abela's Model)**

Dr. Andrew Abela’s Chart Chooser, inspired by Gene Zelazny’s foundational work, provides a widely adopted methodology for initial data classification based on four fundamental objectives: Comparison, Distribution, Relationship, or Composition.16 This matrix is effective for beginner and corporate users due to its simplicity in helping identify the appropriate chart family based on the initial question and the number and type of variables involved.11

### **B. Strategic Selection via Narrative Goal: The Financial Times Visual Vocabulary**

The Financial Times Visual Vocabulary (FTVV) represents a more nuanced, narrative-driven framework, essential for data storytelling.24 It organizes charts not merely by data type but by the explicit pattern the visualization is intended to highlight.24 This approach moves beyond basic classification to focus on the subtleties of the communicative pattern, validating the centrality of the "data story" in professional visualization governance.

The FTVV categorizes visualizations into nine core narrative relationships:

1. **Change over Time:** Emphasizing evolving trends (e.g., Line Charts).26  
2. **Distribution:** Showing the frequency or spread of data across ranges (e.g., Histograms, Violin Plots).26  
3. **Magnitude/Comparison:** Showing size comparisons between items (e.g., Bar Charts).26  
4. **Relationship/Correlation:** Showing the connection between two or more variables (e.g., Scatter Plots).26  
5. **Part-to-Whole/Composition:** Breaking down a total entity into its component elements (e.g., Stacked Column Charts).26  
6. **Ranking:** Where the item's position in an ordered list is more important than its absolute value.26  
7. **Deviation:** Highlighting variance, often from a zero baseline or a target.24  
8. **Spatial:** Used exclusively when precise geographical location or patterns are the primary focus (e.g., Locator maps, Choropleths).26  
9. **Flow:** Illustrating volume or intensity of movement between states or conditions (e.g., Sankey Diagrams).26

The FTVV provides the necessary refinement layer for an expert decision process. While a generic comparison goal might be identified using Abela's matrix, the FTVV allows the designer to select the precise chart that articulates whether the story is about **Magnitude**, **Ranking**, or **Deviation** from a reference point. This synthesis of frameworks—using the data structure to narrow the options and the narrative goal to select the optimum visual—forms the most robust standard decision process.

## **IV. Mapping Data Relationships to Visual Form: A Detailed Guide**

The technical implementation of the standard decision process requires precise selection based on the four primary data relationships.

### **A. Change over Time (Temporal Trends)**

Visualizing temporal data typically involves placing time on the horizontal axis and the variable of interest on the vertical axis.12

* **Core Charts:** **Line charts** are the most common and versatile choice, providing excellent visualization of continuous trends and patterns over time.5  
* **Specialized Charts:** **Area charts** are useful for representing cumulative or stacked time-series data.27  
  **Column charts** are generally better for visualizing discrete, fewer intervals, such as monthly totals, rather than continuous trends.27 For showing specific movement between two dates (e.g., pre- and post-event),  
  **Arrow Plots** or **Range Bars** effectively communicate the magnitude and direction of the change.19

### **B. Distribution (Frequency and Spread)**

Distribution charts illustrate how data is spread across ranges or categories.30 The choice depends on the variable type.31

* **Single Numerical Variable:** A **Histogram** shows frequency distribution across binned quantitative values.12 A  
  **Density Plot** offers a smoothed estimate of the distribution, making it ideal for comparative distribution analysis.27  
* **Comparing Distributions between Groups:** **Box plots** summarize distributions using statistical measures (quartiles, median) and are excellent for identifying outliers.12  
  **Violin Plots** offer a more detailed view by plotting the density curve for each group, revealing the shape of the underlying distribution.12

### **C. Comparison (Magnitude and Ranking)**

Comparison charts visualize differences, trends, or patterns between categories.30

* **Categorical Variables:** **Bar charts** and **column charts** are the standard choice for comparing qualitative variables.12 If category names are extensive, horizontal bar charts enhance readability.14  
* **High-Fidelity Comparison:** **Dot Plots**, particularly in their Cleveland Dot Plot form, are superior to bar charts when comparing quantitative values across numerous categories. By relying on position (the highest-accuracy encoding) rather than length, they reduce visual clutter and improve precision in comparison.17  
* **Goal Tracking:** **Bullet charts** are highly effective, compact visuals for benchmarking a single metric against multiple performance targets (goals) using background shading and target markers.33  
* **Difference Comparison:** **Dumbbell charts** (Dot Plots connected by a line) display the span or interval between two connected points, explicitly highlighting the magnitude of the difference.19

### **D. Relationship (Correlation and Covariance)**

Relationship charts show how variables are connected or correlated.30

* **Two Variables:** **Scatter Plots** display trends, clusters, or outliers between two numerical variables.32 They are highly effective for presenting patterns in large datasets without specific regard to time.32  
* **Three Variables:** **Bubble Charts** extend scatter plots by encoding a third variable via the size of the points.32 However, caution is warranted: since size relies on the estimation of area, these charts are less suitable for comparing exact values and should be used primarily for pattern recognition.13

### **E. Composition (Part-to-Whole)**

Composition charts illustrate how individual components contribute to a total.30

* **Best Practice:** **Stacked column charts** (including 100% stacked column charts) are generally preferred for composition analysis, particularly when comparison is involved, as they rely on the superior positional and length encodings.13 Stacked bar charts should ideally be limited to two or three series to maintain clarity.14  
* **Managing Perceptual Risk:** While **Pie Charts** are used for simple share-of-total composition 11, they rely on low-accuracy angle judgment.13 Best practices recommend using a  
  **Donut Chart** instead of a pie chart, as the central hole mitigates some of the difficulty in seeing size variations.14 Pie charts should be avoided entirely for comparison or distribution tasks.32  
* **Hierarchical Composition:** **Treemaps** are effective for visualizing hierarchical composition using area to represent magnitude.28

## **V. The Future of Selection: Large Language Models and NL2VIS Systems**

The question of whether an LLM can automate visualization selection is answered by the active development of Natural Language to Visualization (NL2VIS) systems.35 These systems leverage the advanced code generation and language understanding capabilities of modern LLMs (e.g., GPT-3.5, GPT-4) to translate a user’s natural language request into a concrete visualization specification.35 Commercial tools and platforms like Metabase and Julius AI are rapidly integrating these AI-backed capabilities.38

### **A. Case Study: LIDA (Large Language Model-Agnostic Visualization) Architecture**

LIDA is a notable example of a structured, multi-stage LLM pipeline designed to generate grammar-agnostic visualizations and infographics automatically.40 It represents an algorithmic attempt to internalize the complex, multi-step human decision process described in Sections I and III.

The architecture comprises four critical modules:

1. **SUMMARIZER:** Because datasets can be massive, the summarizer first converts the raw data into a compact, information-dense natural language representation. This summary serves as the grounding context for subsequent LLM operations.40  
2. **GOAL EXPLORER:** This module automates the critical strategic step of identifying intent. It enumerates relevant data exploration goals based on the summarized data.40 This function directly mimics the human expert’s task of defining a clear purpose and identifying the data relationship (Steps 1 and 3 of the standard process).  
3. **VIS-GENERATOR:** Using the identified goals, this module generates visualization code in various languages and grammars (e.g., matplotlib, Altair). LIDA’s grammar-agnostic approach provides flexibility across different visualization libraries.40  
4. **INFOGRAPHER:** This optional module uses image generation models to create stylized, data-faithful graphics.40

### **B. Capabilities and Reliability: Limitations and Dependencies**

LIDA demonstrates high reliability in testing, reporting an error rate below 3.5% on generated visualizations, a significant improvement over baseline models.43

However, the technology introduces specific operational constraints:

* **LLM Dependence:** LIDA's performance is critically dependent on the choice and capability of the underlying LLM; smaller open-source models may not perform adequately, necessitating the use of larger models like GPT-4.43  
* **Knowledge Bottleneck:** The system's performance is affected by how well the specific visualization grammars or chart types are represented within the LLM's training data.42 The selection quality is therefore reliant on the LLM’s ability to recall and synthesize human-curated visualization knowledge, confirming that the LLM is automating the standard process rather than inventing new principles.  
* **Execution Risk:** Since NL2VIS systems generate and execute code to produce the final chart, a sandbox environment is strongly recommended to ensure safety and security during operation.40

The development of NL2VIS confirms that the standard decision process for visualization selection is robust enough to be formalized into an algorithmic pipeline. By introducing the Goal Explorer, LLMs attempt to automate the *strategic* stage of design—determining *why* to visualize—which is the most valuable contribution to date.

## **VI. Synthesis and Implementation: Building a Visualization Governance Model**

The integration of strategic intent, cognitive principles, and structured frameworks provides the definitive answer to how to select a proper visualization for a data story.

### **A. Integrating Structured Frameworks into the Workflow**

A robust visualization governance model requires a dual-layered selection process:

1. **Strategic Layer:** Use the Financial Times Visual Vocabulary's nine categories to define the exact narrative goal (e.g., Deviation, Ranking, Flow) and establish a common language for discussion with non-technical partners.25  
2. **Perceptual Layer:** Overlay the chart selection with the Cleveland-McGill perceptual hierarchy. For core quantitative messages (Comparison, Trend), prioritize charts that leverage position and length (e.g., Dot Plots, Line Charts) to ensure maximum perceptual accuracy and minimum cognitive load.13 If a popular chart type is selected (e.g., a Pie Chart), ensure its use is restricted to simple compositional tasks and that a perceptually superior alternative (e.g., a Donut Chart or Stacked Bar) is used whenever comparison is necessary.13

### **B. Best Practices for Accessibility, Context, and Decluttering**

Once the chart type is selected, governance must enforce clarity and integrity:

* **Maintaining Integrity:** The numerical axis, particularly the Y-axis for comparisons, must begin at zero, as human perception is highly sensitive to the distortion of length and area.7 If it is necessary to zoom in to show fine trends, that deviation from the zero-baseline must be explicitly noted for the user.14  
* **Simplicity and Focus:** Keep visualizations simple by adhering to a high data-ink ratio; cutting the clutter eliminates unnecessary visual elements that detract from the core message.7  
* **Strategic Encoding:** Utilize color strategically as a pre-attentive attribute to highlight key data points and ensure categories are clearly distinguished.7 Color palettes must be consistent, coherent, and checked for accessibility.15

### **C. Measuring Success: Evaluating Effectiveness and Comprehension**

The final, non-negotiable step in the decision process is validation. The visualization must be subjected to testing by an unfamiliar colleague to ensure the intended story is immediately and clearly understood without prior context.16 The true effectiveness of a visualization choice is measured by its impact on the audience's ability to quickly comprehend and interpret the information.44 By validating that the visual approach performs optimally for the specific data type and narrative, the analyst confirms the selection process was successful.

In conclusion, the proper visualization for a data story is determined by a highly formalized, expert-level process that systematically moves from defining the strategic narrative to applying constraints derived from cognitive science, before finally executing the design using established frameworks. While the emergence of LLMs in NL2VIS promises to automate the initial strategic exploration and technical generation, the fundamental decision structure—based on defining purpose, knowing the audience, and selecting a chart that maximizes perceptual accuracy—remains the essential standard for effective data communication.

#### **Works cited**

1. Data Story Visualization: A Decision Tree \- TDWI, accessed September 29, 2025, [https://tdwi.org/articles/2020/10/06/bi-all-data-story-visualization-decision-tree.aspx](https://tdwi.org/articles/2020/10/06/bi-all-data-story-visualization-decision-tree.aspx)  
2. Data Storytelling: How to Tell a Great Story with Data \- ThoughtSpot, accessed September 29, 2025, [https://www.thoughtspot.com/data-trends/best-practices/data-storytelling](https://www.thoughtspot.com/data-trends/best-practices/data-storytelling)  
3. Crafting Compelling Data Narratives:A Comprehensive Look at Chart Types in Power BI., accessed September 29, 2025, [https://dev.to/phylis/crafting-compelling-data-narrativesa-comprehensive-look-at-chart-types-in-power-bi-4740](https://dev.to/phylis/crafting-compelling-data-narrativesa-comprehensive-look-at-chart-types-in-power-bi-4740)  
4. Seven Steps to Better Data Visualization | Fontbonne University, accessed September 29, 2025, [https://www.fontbonne.edu/wp-content/uploads/2020/04/AA\_Data\_Visualization\_White\_Paper\_Proof\_1\_20.pdf](https://www.fontbonne.edu/wp-content/uploads/2020/04/AA_Data_Visualization_White_Paper_Proof_1_20.pdf)  
5. Data Storytelling: Key Factors for Chart Selection \- QuantHub, accessed September 29, 2025, [https://www.quanthub.com/data-storytelling-key-factors-for-chart-selection/](https://www.quanthub.com/data-storytelling-key-factors-for-chart-selection/)  
6. Data Storytelling: Why Numbers Need a Narrative \- ChartExpo, accessed September 29, 2025, [https://chartexpo.com/blog/data-storytelling](https://chartexpo.com/blog/data-storytelling)  
7. 10 Data Visualization Best Practices to Overcome Common Mistakes \- Golden Software, accessed September 29, 2025, [https://www.goldensoftware.com/data-visualization-best-practices/](https://www.goldensoftware.com/data-visualization-best-practices/)  
8. Selecting an effective data visualization | Looker \- Google Cloud, accessed September 29, 2025, [https://cloud.google.com/looker/docs/visualization-guide](https://cloud.google.com/looker/docs/visualization-guide)  
9. The Data Visualization Design Process: A Step-by-Step Guide for Beginners, accessed September 29, 2025, [https://communityscience.astc.org/resources/the-data-visualization-design-process-a-step-by-step-guide-for-beginners/](https://communityscience.astc.org/resources/the-data-visualization-design-process-a-step-by-step-guide-for-beginners/)  
10. Avoiding Common Pitfalls in Chart Design \- Playfair Data, accessed September 29, 2025, [https://playfairdata.com/avoiding-common-pitfalls-in-chart-design/](https://playfairdata.com/avoiding-common-pitfalls-in-chart-design/)  
11. Chart Suggestions—A Thought-Starter, accessed September 29, 2025, [https://extremepresentation.typepad.com/files/choosing-a-good-chart-09.pdf](https://extremepresentation.typepad.com/files/choosing-a-good-chart-09.pdf)  
12. How to Choose the Right Data Visualization | Atlassian, accessed September 29, 2025, [https://www.atlassian.com/data/charts/how-to-choose-data-visualization](https://www.atlassian.com/data/charts/how-to-choose-data-visualization)  
13. Visual Perception and Pre-Attentive Attributes in Oncological Data Visualisation \- PMC, accessed September 29, 2025, [https://pmc.ncbi.nlm.nih.gov/articles/PMC12292122/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12292122/)  
14. Visualization/Chart Best Practices \- MU Analytics \- University of Missouri, accessed September 29, 2025, [https://udair.missouri.edu/visualization-chart-best-practices/](https://udair.missouri.edu/visualization-chart-best-practices/)  
15. The Impact of Color Choices on Data Visualization Effectiveness, accessed September 29, 2025, [https://bigblue.academy/en/the-impact-of-color-choices-on-data-visualization-effectiveness](https://bigblue.academy/en/the-impact-of-color-choices-on-data-visualization-effectiveness)  
16. Andrew Abela's Chart Chooser \- Michael Sandberg's Data Visualization Blog, accessed September 29, 2025, [https://datavizblog.com/2013/04/29/andrew-abelas-chart-chooser/](https://datavizblog.com/2013/04/29/andrew-abelas-chart-chooser/)  
17. Graphical perception \- Wikipedia, accessed September 29, 2025, [https://en.wikipedia.org/wiki/Graphical\_perception](https://en.wikipedia.org/wiki/Graphical_perception)  
18. Graphical Perception \- AWS, accessed September 29, 2025, [http://rstudio-pubs-static.s3.amazonaws.com/342939\_d79a0160031d464f8a4cad3e20bbdbc4.html](http://rstudio-pubs-static.s3.amazonaws.com/342939_d79a0160031d464f8a4cad3e20bbdbc4.html)  
19. Comparative insights through Storytelling Charts in Power BI \- Inforiver, accessed September 29, 2025, [https://inforiver.com/blog/inforiver-analytics-plus/storytelling-charts-in-power-bi/](https://inforiver.com/blog/inforiver-analytics-plus/storytelling-charts-in-power-bi/)  
20. Preattentive Attributes Comparison \- Playfair Data, accessed September 29, 2025, [https://playfairdata.com/preattentive-attributes-comparison/](https://playfairdata.com/preattentive-attributes-comparison/)  
21. Pre-Attentive Attributes \- Turning Data Into Wisdom, accessed September 29, 2025, [https://www.turningdataintowisdom.com/pre-attentive-attributes/](https://www.turningdataintowisdom.com/pre-attentive-attributes/)  
22. Choosing a good chart \- The Extreme Presentation(tm) Method \- TypePad, accessed September 29, 2025, [https://extremepresentation.typepad.com/blog/2006/09/choosing\_a\_good.html](https://extremepresentation.typepad.com/blog/2006/09/choosing_a_good.html)  
23. Dr. Andrew Abella's Chart Chooser: The First Popularized Catalog | by Antonio Neto, accessed September 29, 2025, [https://medium.com/@antonioneto\_17307/dr-andrew-abellas-chart-chooser-the-first-popularized-catalog-7ca5ba55aa6f](https://medium.com/@antonioneto_17307/dr-andrew-abellas-chart-chooser-the-first-popularized-catalog-7ca5ba55aa6f)  
24. Financial Times Visual Vocabulary (PDF) \- Fountn, accessed September 29, 2025, [https://fountn.design/resource/financial-times-visual-vocabulary-pdf/](https://fountn.design/resource/financial-times-visual-vocabulary-pdf/)  
25. Choosing charts: the message \- data.europa.eu, accessed September 29, 2025, [https://data.europa.eu/apps/data-visualisation-guide/choosing-charts-the-message](https://data.europa.eu/apps/data-visualisation-guide/choosing-charts-the-message)  
26. Visual-vocabulary.pdf, accessed September 29, 2025, [https://journalismcourses.org/wp-content/uploads/2020/07/Visual-vocabulary.pdf](https://journalismcourses.org/wp-content/uploads/2020/07/Visual-vocabulary.pdf)  
27. Choosing the Right Chart: A Practical Guide for Data Storytelling | by Raghavan P | Medium, accessed September 29, 2025, [https://raghavan-p26.medium.com/choosing-the-right-chart-a-practical-guide-for-data-storytelling-a37feb8fcea2](https://raghavan-p26.medium.com/choosing-the-right-chart-a-practical-guide-for-data-storytelling-a37feb8fcea2)  
28. Telling Stories With Data: How to Choose the Right Data Visualization \- CMS Wire, accessed September 29, 2025, [https://www.cmswire.com/digital-marketing/how-to-choose-the-right-data-visualization/](https://www.cmswire.com/digital-marketing/how-to-choose-the-right-data-visualization/)  
29. Visual Vocabulary \- Tableau Public, accessed September 29, 2025, [https://public.tableau.com/app/profile/andy.kriebel/viz/VisualVocabulary/VisualVocabulary](https://public.tableau.com/app/profile/andy.kriebel/viz/VisualVocabulary/VisualVocabulary)  
30. Choosing the Right Chart Type: A Technical Guide \- GeeksforGeeks, accessed September 29, 2025, [https://www.geeksforgeeks.org/data-visualization/choosing-the-right-chart-type-a-technical-guide/](https://www.geeksforgeeks.org/data-visualization/choosing-the-right-chart-type-a-technical-guide/)  
31. 1 Data visualization \- R for Data Science (2e) \- Hadley Wickham, accessed September 29, 2025, [https://r4ds.hadley.nz/data-visualize.html](https://r4ds.hadley.nz/data-visualize.html)  
32. Data Visualization – How to Pick the Right Chart Type? \- eazyBI, accessed September 29, 2025, [https://eazybi.com/blog/data-visualization-and-chart-types](https://eazybi.com/blog/data-visualization-and-chart-types)  
33. Essential Chart Types for Data Visualization | Atlassian, accessed September 29, 2025, [https://www.atlassian.com/data/charts/essential-chart-types-for-data-visualization](https://www.atlassian.com/data/charts/essential-chart-types-for-data-visualization)  
34. 7 Goal Chart Templates for Insights-Driven Goal Setting \- ChartExpo, accessed September 29, 2025, [https://chartexpo.com/blog/goal-chart-templates](https://chartexpo.com/blog/goal-chart-templates)  
35. Visualization Generation with Large Language Models: An Evaluation \- arXiv, accessed September 29, 2025, [https://arxiv.org/html/2401.11255v1](https://arxiv.org/html/2401.11255v1)  
36. Natural Language Dataset Generation Framework for Visualizations Powered by Large Language Models \- arXiv, accessed September 29, 2025, [https://arxiv.org/html/2309.10245v4](https://arxiv.org/html/2309.10245v4)  
37. Synthesizing Natural Language to Visualization (NL2VIS) Benchmarks from NL2SQL Benchmarks \- Yuyu Luo, accessed September 29, 2025, [https://luoyuyu.vip/files/nvBench-SIGMOD21.pdf](https://luoyuyu.vip/files/nvBench-SIGMOD21.pdf)  
38. Open source Business Intelligence and Embedded Analytics, accessed September 29, 2025, [https://www.metabase.com/](https://www.metabase.com/)  
39. The list to AI data visualization tools in 2025, welcome to add new ones\! \- Reddit, accessed September 29, 2025, [https://www.reddit.com/r/datavisualization/comments/1jaumgw/the\_list\_to\_ai\_data\_visualization\_tools\_in\_2025/](https://www.reddit.com/r/datavisualization/comments/1jaumgw/the_list_to_ai_data_visualization_tools_in_2025/)  
40. LIDA | LIDA: Automated Visualizations with LLMs \- Microsoft Open Source, accessed September 29, 2025, [https://microsoft.github.io/lida/](https://microsoft.github.io/lida/)  
41. Are LLMs ready for Visualization? \- arXiv, accessed September 29, 2025, [https://arxiv.org/html/2403.06158v1](https://arxiv.org/html/2403.06158v1)  
42. How to Generate Visualizations with Large Language Models (ChatGPT, GPT4), accessed September 29, 2025, [https://newsletter.victordibia.com/p/lida-automatic-generation-of-grammar](https://newsletter.victordibia.com/p/lida-automatic-generation-of-grammar)  
43. microsoft/lida: Automatic Generation of Visualizations and Infographics using Large Language Models \- GitHub, accessed September 29, 2025, [https://github.com/microsoft/lida](https://github.com/microsoft/lida)  
44. (PDF) THE INFLUENCE OF VISUALIZATION STRATEGY ON READING COMPREHENSION ABILITY \- ResearchGate, accessed September 29, 2025, [https://www.researchgate.net/publication/338161080\_THE\_INFLUENCE\_OF\_VISUALIZATION\_STRATEGY\_ON\_READING\_COMPREHENSION\_ABILITY](https://www.researchgate.net/publication/338161080_THE_INFLUENCE_OF_VISUALIZATION_STRATEGY_ON_READING_COMPREHENSION_ABILITY)  
45. The Effectiveness of Visualization Techniques for Supporting Decision-Making \- ODU Digital Commons, accessed September 29, 2025, [https://digitalcommons.odu.edu/cgi/viewcontent.cgi?article=1025\&context=msvcapstone](https://digitalcommons.odu.edu/cgi/viewcontent.cgi?article=1025&context=msvcapstone)