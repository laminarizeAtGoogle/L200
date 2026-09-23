**Ai in 5 Days Assessment Agent**

This Assessment Agent is an opportunity for you to apply what you've learned during the course and immediately get feedback from an agent on what you have built. You can submit your agent for review and feedback as many times as you would like and as soon as you are ready.&nbsp;&nbsp;&nbsp;

&nbsp;

| Tldr; Create a new GitHub project and make it 🚨public 🚨 Make sure it is a 🚨root project 🚨you can clone, not a sub folder Develop and publish your agent Log into this [site](https://fde-project-evaluator-510868799189.us-central1.run.app/), enter your Git URL and hit ‘Evaluate Project’ \[Optional\] Record a public youtube video walking through the code, architecture and agent demo. Include the youtube video URL in the submission. ![][image1] |
| :---- |

&nbsp;

**The Process**

1. Formulate a problem and solution to which you will build your agent. This will hone the objective of your project.  
   * Example: Writing blogs is too manual and time intensive. I will be building an Automated Blog Writer Agent to scale my blog production and blog quality.  
2. Develop and publish the code for your agent publicly.  
   * Example: Publish the agent code to GitHub.  
3. Publish a short video demonstrating the working code and explaining the problem and your solution. (Optional)  
4. Submit your Code and Video following the submission guidelines below.

&nbsp;

**Sample Agents:**

* **Agents for Good**

Agents that tackle problems in education, healthcare, or sustainability.

* **Enterprise Agents**

Agents designed to improve business workflows, analyze data, or automate customer support.

* **Concierge Agents**

Agents useful for individuals in their own lives, to automate meal planning, streamline shopping, plan travel, etc.

* **Freestyle Track**

The open category for innovative agents that don't fit neatly into the other tracks. This is your space to experiment, explore, and build something truly unique or unclassifiable.

### 

### Submission Process & Automated Review

#### Agent Assessor

Participants need to submit the code for their agent and a video explanation demonstrating how it works and why you built it. Both assets will be reviewed by an agent, and you will receive an automatic score based on your implementation.

### 

### Evaluation

Your submission will be evaluated on the below criteria with a maximum score of 95:&nbsp;

* **Tool & Interface Design**&nbsp;  
* **Context & Memory**&nbsp;  
* **Orchestration & Logic**&nbsp;  
* **Observability & Tracing**&nbsp;  
* **Infrastructure & CI/CD**&nbsp;

&nbsp;

### 

**To Submit**:&nbsp;

You must sign in with your Google account.

* https://fde-project-evaluator-510868799189.us-central1.run.app/login  
  &nbsp;

**Resources**

* Development  
  * ADK-Docs ([link](https://google.github.io/adk-docs/)) https://google.github.io/adk-docs/  
  * ADK-Python ([link](https://github.com/google/adk-python)) https://github.com/google/adk-python  
  * ADK-Go ([link](https://github.com/google/adk-go)) https://github.com/google/adk-go  
  * ADK-Java ([link](https://github.com/google/adk-java)) https://github.com/google/adk-java  
  * ADK-Sample Agents ([link](https://github.com/google/adk-samples)) https://github.com/google/adk-samples  
  * Agent Starter Pack ([link](https://github.com/google/adk-samples)) https://github.com/google/adk-samples  
  * A2A-Docs ([link](https://github.com/GoogleCloudPlatform/agent-starter-pack)) https://github.com/GoogleCloudPlatform/agent-starter-pack  
  * A2A-Python ([link](https://a2a-protocol.org/latest/)) https://a2a-protocol.org/latest/  
  * Google AI Studio ([link](https://github.com/a2aproject/a2a-python)) https://github.com/a2aproject/a2a-python  
* Community  
  * Reddit Agent Development Kit ([link](https://www.reddit.com/r/agentdevelopmentkit/)) https://www.reddit.com/r/agentdevelopmentkit/  
* Documentation  
  * Vertex AI Agent Engine Documentation ([link](https://docs.cloud.google.com/agent-builder/agent-engine/overview)) https://docs.cloud.google.com/agent-builder/agent-engine/overview  
  * Introduction to Agents Whitepaper ([link](https://drive.google.com/file/d/1C-HvqgxM7dj4G2kCQLnuMXi1fTpXRdpx/view)) https://drive.google.com/file/d/1C-HvqgxM7dj4G2kCQLnuMXi1fTpXRdpx/view

### F.A.Q.

**Q: Can I make a submission multiple times?**

Yes, you can resubmit as many times as you would like.

**Q: If I use ADK, can I choose another language (Java or Go), or do I need to stick with Python?**

You can use ADK-Python, ADK-Go or ADK-Java.

**Q: Can I make a submission using Colab or Notebooks instead of Github?**

Yes, you can either submit a Github repo or a notebook.

**Q: Can I still submit even though my code isn’t working or is not complete?**

Yes, however, this assessment is to help you understand how well you have understood the core components covered in this course, the same core components will be required for the L300.

**Q: Do I need to submit my video in English?**

Yes. Our agent is looking for English language videos:  Please reach out to fde-enablement@ if you want to make an agent assessor in another language as a great tool for other nooglers\!

&nbsp;

&nbsp;

&nbsp;

### **AgentOps Code Review Matrix**

| Category | Criteria | Code Evidence | Points |
| :---- | :---- | :---- | :---- |
| **1\. Tool & Interface Design** | **Comprehensive Tool Docstrings** | Tool functions include clear, human-readable descriptions of their purpose and all parameters. | 5 |
|  | **Descriptive Naming** | Tool names are highly specific and clear (e.g., create\_critical\_bug instead of update\_jira). | 5 |
|  | **Explicit JSON Schemas** | The code utilizes strict input and output schemas to validate tool arguments and constrain LLMs. | 5 |
|  | **Guided Error Handling** | Tool error returns provide descriptive recovery instructions back to the LLM instead of just crashing. | 5 |
| **2\. Context & Memory** | **Robust System Instructions** | A clear "constitution" is defined in the system prompt for persona, domain knowledge, and constraints. | 5 |
|  | **History Compaction** | Code implements context bloat management (e.g., token-based truncation, sliding windows, summarization) via mechanisms and tools such as adk compaction, memory bank or context caching on google cloud | 5 |
|  | **Persistent Session State** | The agent connects to a persistent database, be it vector store or vertex ai search.  to  efficiently retrieve information ot manage conversational history across turns. | 5 |
|  | **Async Memory Operations** | Expensive memory generation and consolidation are coded as background or async tasks to prevent UI blocking. | 5 |
| **3\. Orchestration & Logic** | **Multi-Agent Patterns** | Complex tasks utilize proven design patterns (e.g., Coordinator, Sequential) rather than monolithic agents implemented in ADK | 5 |
|  | **Strategic Model Routing** | The codebase routes specific requests to the most appropriate model (e.g., Flash for fast tasks, Pro for planning). | 5 |
|  | **Guardrails & Policy Plugins** | Security  and evaluation guardrails ( i.e. self eval) implemented via existing google cloud or ADk or agentic tech | 5 |
|  | **Human-in-the-Loop Hooks** | High-stakes actions include explicit code stops requiring human confirmation before execution. | 5 |
| **4\. Observability & Tracing** | **Structured JSON Logging** | The codebase utilizes structured logging libraries to capture rich metadata rather than simple prints. | 5 |
|  | **Intent vs. Outcome Capture** | Logs explicitly record both the agent's *intended* action before execution and the *actual* outcome after. | 5 |
|  | **Distributed Tracing** | Implementation of OpenTelemetry (or equivalent) to link spans and trace a request from query to answer. | 5 |
|  | **PII Redaction** | Logging and memory pipelines include active scrubbing mechanisms to redact sensitive data before storage possibly using google cloud APIs | 5 |
| **5\. Infrastructure & CI/CD** | **Automated Evaluation Suites** | The repository contains a testing harness (e.g., against a golden dataset) to statically measure agent regressions. | 5 |
|  | **Infrastructure as Code** | The project includes IaC configurations (like Terraform) to programmatically provision necessary resources. Usage of tools such as Agent cli present in the documentation | 5 |
|  | **Secure Secret Management** | No hardcoded API keys; all tools and clients leverage a secure injection method like Secret Manager. | 5 |
| **Total** |  |  | **95** |

&nbsp;

&nbsp;
