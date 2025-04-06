import streamlit as st
import pandas as pd
import google.generativeai as genai

try:
    key = st.secrets["gemini_api_key"]
    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    st.title("📊 Gemini AI Analyst: Ask, Execute, and Understand Your Data")

    # Upload 2 CSV files
    transaction_file = st.file_uploader("📁 Upload Transaction CSV", type=["csv"], key="trans")
    dict_file = st.file_uploader("📘 Upload Data Dictionary CSV", type=["csv"], key="dict")

    if transaction_file and dict_file:
        df = pd.read_csv(transaction_file)
        df_dict = pd.read_csv(dict_file)

        st.subheader("🔍 Transaction Data")
        st.dataframe(df)

        st.subheader("📚 Data Dictionary")
        st.dataframe(df_dict)

        df_name = "df"
        data_dict_text = df_dict.to_string(index=False)
        example_record = df.head(2).to_string(index=False)

        question = st.text_input("💬 Ask a question about your data:")

        if question:
            with st.spinner("🤖 Generating Python code from Gemini..."):

                # Force Gemini to return exec() block only
                prompt = f"""
You are a Python code-writing assistant.
Return Python code ONLY inside an exec() block — no explanation, no markdown.

---

🔍 User Question:
{question}

📦 DataFrame Name: {df_name}

📘 Data Dictionary:
{data_dict_text}

📊 Sample Data:
{example_record}

---

🛠 Instructions:
- The DataFrame '{df_name}' is already loaded.
- DO NOT import pandas.
- Use pd.to_datetime() to convert dates.
- Store result in variable 'ANSWER'.
- Output only Python code inside exec(\\\"\\\"\\\"...\\\"\\\"\\\").
"""

                response = model.generate_content(prompt)
                generated_code = response.text.strip().replace("```python", "").replace("```", "")

                st.subheader("🧠 Generated Python Code")
                st.code(generated_code, language="python")

                try:
                    local_vars = {"df": df, "pd": pd}
                    exec(generated_code, {}, local_vars)

                    if "ANSWER" in local_vars:
                        answer_data = local_vars["ANSWER"]

                        st.subheader("✅ Result (ANSWER)")
                        st.write(answer_data)

                        # ✨ Explain + Opinion from Gemini
                        explain_prompt = f"""
The user asked:
**{question}**

The following is the output of the executed Python code:
{str(answer_data)}

Please do the following:
1. Summarize the result in plain English/Thai
2. Provide your analysis and interpretation
3. Give your professional opinion or business insight based on the result
Make your explanation easy to understand and business-friendly.
"""
                        explain_response = model.generate_content(explain_prompt)

                        st.subheader("🗣️ Gemini Summary + Opinion")
                        st.write(explain_response.text)

                        # 🔁 Follow-up prompt
                        followup = st.chat_input("🔁 Ask a follow-up question:")
                        if followup:
                            context_followup = f"""
User previously asked:
**{question}**

Result:
{str(answer_data)}

Now they follow-up with:
**{followup}**

Please respond based on the context and data above, including reasoning and opinion if helpful.
"""
                            followup_response = model.generate_content(context_followup)
                            with st.chat_message("assistant"):
                                st.markdown(followup_response.text)

                    else:
                        st.warning("⚠️ No variable named 'ANSWER' found.")
                except Exception as e:
                    st.error(f"❌ Error executing code: {e}")
    else:
        st.info("📌 Please upload both CSV files to continue.")

except Exception as e:
    st.error(f"❗ Application error: {e}")
