# Landing Page Generation Pipeline

This project generates personalized landing pages for Tofu clients based on background information collected from the **company_info.json** and **target_info.json** about account, industry, and persona descriptions. The entire process is divided into three main stages where OpenAI's API is utilized for content generation and personalization. Below is a breakdown of the workflow:

To better understand the entities:
Company --- Tofu's client Stampli YMCA, Apex Oil.
Industry --- The target industries of Stampli's marketing service. 
Persona --- The target personas of Stampli's marketing persona. 

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


### **Integrate LangChain Memory**

To reduce redundant API calls and improve performance, we integrated** ****LangChain's memory module**. This allows the system to** ****cache previously generated summaries** (e.g., company or account descriptions), so they can be reused in subsequent steps or requests without re-generating, improving efficiency and consistency across the content pipeline.


### **Handling Token Limitations**

To handle OpenAI’s token limits (e.g., 4096 tokens for** **`gpt-3.5-turbo`), this system splits long texts through multi OpenAI API calls—like company or industry descriptions, into chunks, summarizes each proportionally, and then combines the results into a final concise summary. This ensures essential content is preserved while staying within the model’s limits.


### **Setup and Usage Instructions:****

To run this project, you need to install the necessary dependencies and set up OpenAI API access. Please follow these steps:

```bash


# Clone the project
git clone https://github.com/pinxiang-wang/tofu-take-home.git
cd tofu-take-home

# Install required Python packages
pip install -r requirements.txt

export OPENAI_API_KEY="your-api-key-here"

# Run the pipeline demo:
python content_gen_pipeline_demo.py

# Run the newest pipeline demo:
python content_gen_gemo_with_planner.py

```
