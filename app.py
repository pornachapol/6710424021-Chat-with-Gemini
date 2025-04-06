import streamlit as st
import pandas as pd
import google.generativeai as genai

# Gemini Setup
key = st.secrets["gemini_api_key"]
genai.configure(api_key=key)
model = genai.GenerativeModel("gemini-2.0-flash-lite")

st.title("📊 Gemini Analyst: Execute + Explain + Chat")

# Upload CSVs
transaction_file = st.file_uploader("📁 Upload Transaction CSV", type=["csv"], key="trans")
dict_file = st.file_uploader("📘 Upload Data Dictionary CSV", type=["csv"], key="dict")

# Session history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if transaction_file and dict_file:
    df = pd.read_csv(transaction_file)
    df_dict = pd.read_csv(dict_file)

    st.subheader("🔍 Transaction Data")
    st.dataframe(df)

    st.subheader("📘 Data Dictionary")
    st.dataframe(df_dict)

    df_name = "df"
    data_dict_text = df_dict.to_string(index=False)
    example_record = df.head(2).to_string(index=False)

    # Show chat history
    for entry in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(entry["question"])
        with st.chat_message("assistant"):
            st.markdown("**🧠 Generated Code**")
            st.code(entry["code"], language="python")
            st.markdown("**✅ Result**")
            st.write(entry["result"])
            st.markdown("**🗣️ Gemini Opinion**")
            st.markdown(entry["summary"])

    # Main input
    user_input = st.chat_input("💬 Ask a question about your data")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.spinner("🤖 Generating Python code..."):
            # Prompt Gemini to generate Python code with exec()
            prompt = f"""
You are a helpful Python code generator and business analyst.

Your job is to:
1. Generate Python code to query or calculate the answer based on the user’s question and the provided DataFrame.
2. Run the code using `exec()` and return the result in a variable named `ANSWER`.
3. After the code is executed, analyze the result and provide:
    - A concise summary in plain English
    - A professional opinion or business insight based on the result

---

**User Question:**
{user_input}

**DataFrame Name:**
{df_name}

**DataFrame Details:**
{data_dict_text}

**Sample Data (Top 2 Rows):**
{example_record}

---

**Instructions for Code Generation:**
- Write Python code inside exec(\"\"\"...\"\"\")
- DO NOT import pandas
- DO NOT load files
- If the question involves a date/time column, use `pd.to_datetime()` to convert it before using `.dt`
- Store the final result in a variable called `ANSWER`
- The DataFrame is already loaded into a variable called {df_name}
- Return only valid Python code — no markdown or explanation
"""

            code_response = model.generate_content(prompt)
            generated_code = code_response.text.strip().replace("```python", "").replace("```", "")

            try:
                local_vars = {"df": df, "pd": pd}
                exec(generated_code, {}, local_vars)
                answer_data = local_vars.get("ANSWER", "No ANSWER found.")

                # Summarize + Opinion
                explain_prompt = f"""
The user asked: {user_input}

Here is the result of the executed code:
{str(answer_data)}

Please summarize the result in plain English and provide your professional opinion or insight based on the result.
"""

                summary_response = model.generate_content(explain_prompt)

                with st.chat_message("assistant"):
                    st.markdown("**🧠 Generated Code**")
                    st.code(generated_code, language="python")
                    st.markdown("**✅ Result**")
                    st.write(answer_data)
                    st.markdown("**🗣️ Gemini Opinion**")
                    st.markdown(summary_response.text)

                # Save to history
                st.session_state.chat_history.append({
                    "question": user_input,
                    "code": generated_code,
                    "result": answer_data,
                    "summary": summary_response.text
                })

            except Exception as e:
                st.error(f"❌ Error executing code: {e}")

else:
    st.info("📌 Please upload both CSV files to begin.")
