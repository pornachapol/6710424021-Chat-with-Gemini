import streamlit as st
import pandas as pd
import google.generativeai as genai

try:
    # Setup Gemini API
    key = st.secrets["gemini_api_key"]
    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    st.title("📊 Gemini: Ask Your Data with Executable Code")

    # Step 1: Upload CSV files
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

        # Step 2: User enters question
        question = st.text_input("💬 Ask a question about your data:")

        if question:
            with st.spinner("🤖 Generating code..."):

                # Step 3: Construct safe prompt (escaped triple quotes)
                prompt = f"""
You are a Python code-writing assistant.
Your ONLY job is to generate Python code inside an exec() block — no explanation, no markdown, no text.

---

🔍 User Question:
{question}

📦 DataFrame Name:
{df_name}

📘 Data Dictionary:
{data_dict_text}

📊 Sample Data (Top 2 Rows):
{example_record}

---

🛠 Instructions:
1. The DataFrame '{df_name}' is already loaded in memory.
2. DO NOT import pandas or load any files.
3. If the question involves dates, convert the date column to datetime first.
4. Store the result in a variable called 'ANSWER'.
5. Your response MUST be a valid Python exec(\\\"\\\"\\\"...\\\"\\\"\\\") string. No other text is allowed.
6. The answer can be a value, filtered dataframe, or summary.
"""

                response = model.generate_content(prompt)
                generated_code = response.text.strip().replace("```python", "").replace("```", "")

                st.subheader("🧠 Generated Code")
                st.code(generated_code, language="python")

                try:
                    # Step 4: Execute code
                    local_vars = {"df": df}
                    exec(generated_code, {}, local_vars)

                    # Step 5: Show result
                    if "ANSWER" in local_vars:
                        st.subheader("✅ Result (from variable 'ANSWER')")
                        st.write(local_vars["ANSWER"])
                    else:
                        st.warning("⚠️ No variable named 'ANSWER' found in the executed code.")
                except Exception as e:
                    st.error(f"❌ Error executing code: {e}")
    else:
        st.info("📌 Please upload both CSV files to begin.")

except Exception as e:
    st.error(f"❗ Application error: {e}")
