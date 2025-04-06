import streamlit as st
import pandas as pd
import google.generativeai as genai
from io import StringIO

try:
    # Setup API
    key = st.secrets["gemini_api_key"]
    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    st.title("🤖 Gemini: Ask Your Data (with Executable Code)")

    # Upload CSV Files
    transaction_file = st.file_uploader("📥 Upload Transaction CSV", type=["csv"], key="trans")
    dict_file = st.file_uploader("📘 Upload Data Dictionary CSV", type=["csv"], key="dict")

    if transaction_file and dict_file:
        df = pd.read_csv(transaction_file)
        df_dict = pd.read_csv(dict_file)

        st.subheader("🧾 Transaction Data")
        st.dataframe(df)

        st.subheader("📚 Data Dictionary")
        st.dataframe(df_dict)

        # Prepare context for prompting
        df_name = "df"
        data_dict_text = df_dict.to_string(index=False)
        example_record = df.head(2).to_string(index=False)

        # Prompt input
        question = st.text_input("💬 Ask your question about the data:")
        if question:
            with st.spinner("🤖 Generating code..."):
                # Construct the prompt
                prompt = f"""
You are a helpful Python code generator.
Your goal is to write Python code snippets based on the user's question and the provided DataFrame information.

---

📌 User Question:
{question}

📦 DataFrame Name:
{df_name}

📘 Data Dictionary:
{data_dict_text}

📊 Sample Data (Top 2 Rows):
{example_record}

---

🎯 Instructions:
1. Write Python code that answers the user's question by manipulating or filtering the DataFrame.
2. The DataFrame is already loaded as `{df_name}`.
3. Do NOT import pandas.
4. Convert date columns to datetime first if needed.
5. Use `exec()` to run the code.
6. Store the answer in a variable called `ANSWER`.
7. Only generate code inside the `exec()` — do not explain.

---
"""

                response = model.generate_content(prompt)
                st.subheader("🧠 Generated Code")
                generated_code = response.text.strip().replace("```python", "").replace("```", "")
                st.code(generated_code, language="python")

                # Execute the generated code
                try:
                    local_vars = {"df": df}
                    exec(generated_code, {}, local_vars)

                    # Show result
                    if "ANSWER" in local_vars:
                        st.subheader("✅ Answer")
                        st.write(local_vars["ANSWER"])
                    else:
                        st.warning("No variable named 'ANSWER' was found in the executed code.")

                except Exception as e:
                    st.error(f"⚠️ Error executing code: {e}")
    else:
        st.info("📌 Please upload both CSV files to begin.")

except Exception as e:
    st.error(f"🔴 An error occurred: {e}")
