# Landing Page Generation Pipeline

This project generates personalized landing pages for Tofu clients based on background information collected from the **company_info.json** and **target_info.json** about account, industry, and persona descriptions. The entire process is divided into three main stages where OpenAI's API is utilized for content generation and personalization. Below is a breakdown of the workflow:

To better understand the entities:
Company --- Tofu's client Stampli YMCA, Apex Oil...
Industry --- The target industries of Stampli's marketing service
Persona --- The target personas of Stampli's marketing persona

---

### **Setup and Usage Instructions:**

To run this project, you need to install the necessary dependencies and set up OpenAI API access. Please follow these steps:

1. Clone this repository:
2.

### **Workflow Overview:**

1. **Initial Account Description Generation:**

   - The first OpenAI API call is made when the user initiates a landing page generation request.
   - Using the provided **Account URL**, the system queries OpenAI to extract and summarize the account’s relevant information, such as the account's mission, services, and key features.
2. **Industry and Persona Classification:**

   - The second API call is to classify the account into its **Industry** and **Persona** based on the extracted **industry descriptions** and **persona descriptions** from the playbook.
   - The generated account description combined with these playbook elements ensure that the content is properly aligned with the account's industry and persona context.
   - OpenAI generates a **2000-word marketing pitch** tailored to the specific account, incorporating the persona's needs, challenges, and industry-specific context.
3. **HTML Content Replacement:**

   - The third API call involves the generation of personalized content for specific HTML placeholders within the provided landing page template.
   - The system sends the all the information, including: **marketing pitch**, **tag positions**, **HTML tag structure**, and **content length** information, to OpenAI with well-designed prompt instruction.
   - OpenAI uses this information to generate personalized replacement content for each placeholder, ensuring that the final output remains engaging, relevant, and consistent with the account's needs.
4. **HTML Page Rendering:**

   - Once all content is generated, the **`page_render`** function is invoked to update the HTML page with the generated content.
   - The function is to preserve the original layout and tag structure, ensuring that the personalized content is inserted correctly without breaking the page's formatting. （Still have some bugs in rendering the pages）

---

### **Handling Token Limitations:**

- Due to the **token limitations** in OpenAI models (e.g., `gpt-3.5-turbo` with a limit of 4096 tokens), the system optimizes the data passed to the model by chunking large pieces of text, focusing only on the most relevant content for each stage of the process.
- If necessary, only the essential context from the playbook (such as key persona details and industry information) is sent to ensure that the generated content stays within the model's token limits.
