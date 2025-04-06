import streamlit as st
import pandas as pd
import google.generativeai as genai

# Setup
key = st.secrets["gemini_api_key"]
genai.configure(api_key=key)
model = genai.GenerativeModel("gemini-2.0-flash-lite")

st.title("📊 Gemini Analyst: Ask, Execute, and Understand Your Data")

# Upload
transaction_file = st.file_uploader("📁 Upload Transaction CSV", type=["csv"])
dict_file = st.file_uploader("📘 Upload Data Dictionary CSV", type=["csv"])

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if transaction_file and dict_file:
    df = pd.read_csv(transaction_file)
    df_dict = pd.read_csv(dict_file)

    st.subheader("📊 Transaction Data")
    st.dataframe(df)

    st.subheader("📘 Data Dictionary")
    st.dataframe(df_dict)

    df_name = "df"
    data_dict_text = df_dict.to_string(index=False)
    example_record = df.head(2).to_string(index=False)

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

    user_input = st.chat_input("💬 Ask a question about your data")

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.spinner("🤖 Generating Python code..."):
            prompt = f"""
You are a helpful Python code generator and business analyst.

Your job is to:
1. Generate Python code that queries or calculates the answer to the user’s question using the provided DataFrame.
2. Use `exec()` to execute the code and store the result in a variable named `ANSWER`.
3. After execution, provide:
   - A clear summary of the result
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

**Instructions:**
- Write Python code wrapped inside exec(\"\"\"...\"\"\")
- DO NOT import pandas or any external libraries
- Convert date columns using `pd.to_datetime()` if needed
- Store the final answer in `ANSWER`
- Only output code — no explanation, no markdown
- The code must be syntactically valid
"""

            code_response = model.generate_content(prompt)
            generated_code = (
                code_response.text
                .strip()
                .replace("```python", "")
                .replace("```", "")
            )

            with st.chat_message("assistant"):
                st.markdown("**🧠 Generated Code**")
                st.code(generated_code, language="python")

            try:
                # Safe exec with pre-converted datetime (optional fallback)
                local_vars = {"df": df.copy(), "pd": pd}

                # Try running exec
                exec(generated_code, {}, local_vars)

                if "ANSWER" in local_vars:
                    answer_data = local_vars["ANSWER"]
                else:
                    answer_data = "❗ 'ANSWER' variable was not defined."

                # Ask Gemini to explain the result
                explain_prompt = f"""
User asked: {user_input}

Here is the result of the executed code:
{str(answer_data)}

Please:
- Summarize this result clearly
- Give your business insight or opinion about the result
"""
                summary_response = model.generate_content(explain_prompt)

                with st.chat_message("assistant"):
                    st.markdown("**✅ Result**")
                    st.write(answer_data)
                    st.markdown("**🗣️ Gemini Opinion**")
                    st.markdown(summary_response.text)

                # Save to session
                st.session_state.chat_history.append({
                    "question": user_input,
                    "code": generated_code,
                    "result": answer_data,
                    "summary": summary_response.text
                })

            except SyntaxError as e:
                st.error(f"❌ Syntax Error: {e}")
                st.code(generated_code, language="python")
            except Exception as e:
                st.error(f"❌ Error executing code: {e}")
                st.code(generated_code, language="python")

else:
    st.info("📥 Please upload both Transaction and Data Dictionary CSV files to begin.")
