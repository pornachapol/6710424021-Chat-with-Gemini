import streamlit as st
import pandas as pd
import google.generativeai as genai

try:
    key = st.secrets["gemini_api_key"]
    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    st.title("📊 Gemini: Ask Your Data, See the Code, Understand the Answer")

    # Upload files
    transaction_file = st.file_uploader("📁 Upload Transaction CSV", type=["csv"], key="trans")
    dict_file = st.file_uploader("📘 Upload Data Dictionary CSV", type=["csv"], key="dict")

    if transaction_file and dict_file:
        df = pd.read_csv(transaction_file)
        df_dict = pd.read_csv(dict_file)

        st.subheader("🔍 Transaction Data")
        st.dataframe(df)

        st.subheader("📚 Data Dictionary")
        st.dataframe(df_dict)

        # Prepare context
        df_name = "df"
        data_dict_text = df_dict.to_string(index=False)
        example_record = df.head(2).to_string(index=False)

        # Step 1: Ask Question
        question = st.text_input("💬 Ask a question about your data:")

        if question:
            with st.spinner("🤖 Generating Python code..."):

                prompt = f"""
You are a Python code-writing assistant.
Your ONLY job is to generate Python code inside an exec() block — no explanation, no markdown, no text.

User Question:
{question}

DataFrame Name: {df_name}
Data Dictionary:
{data_dict_text}
Sample Data:
{example_record}

Instructions:
- Assume df is already loaded.
- DO NOT import pandas.
- Use pd.to_datetime() for date conversion.
- Store the result in a variable named ANSWER.
- Wrap code in exec(\\\"\\\"\\\"...\\\"\\\"\\\")
"""
                response = model.generate_content(prompt)
                generated_code = response.text.strip().replace("```python", "").replace("```", "")
                st.subheader("🧠 Generated Code")
                st.code(generated_code, language="python")

                try:
                    local_vars = {"df": df, "pd": pd}
                    exec(generated_code, {}, local_vars)

                    if "ANSWER" in local_vars:
                        answer_data = local_vars["ANSWER"]

                        st.subheader("✅ Result from Code (ANSWER)")
                        st.write(answer_data)

                        # Step 2: Ask Gemini to explain the result
                        explanation_prompt = f"""
Below is the result from a Python data query based on the user question:
**{question}**

Here is the output:
{str(answer_data)}

Please summarize or interpret the result in plain language as if you were explaining to a business user.
"""

                        explain_response = model.generate_content(explanation_prompt)
                        st.subheader("🗣️ Gemini Summary")
                        st.write(explain_response.text)

                        # Step 3: Allow user to follow up
                        followup = st.chat_input("🔁 Ask follow-up question (based on the result above):")
                        if followup:
                            context_followup = f"""
You previously answered the question:
**{question}**

Here was the result:
{str(answer_data)}

User follow-up question:
**{followup}**

Answer in plain language, or write Python code if necessary.
"""
                            followup_response = model.generate_content(context_followup)
                            with st.chat_message("assistant"):
                                st.markdown(followup_response.text)

                    else:
                        st.warning("⚠️ No variable named 'ANSWER' found in the executed code.")
                except Exception as e:
                    st.error(f"❌ Error executing code: {e}")
    else:
        st.info("📌 Please upload both CSV files to begin.")

except Exception as e:
    st.error(f"❗ Application error: {e}")
