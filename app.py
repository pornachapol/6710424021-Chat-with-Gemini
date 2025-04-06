import streamlit as st
import pandas as pd
import google.generativeai as genai

# Gemini Setup
key = st.secrets["gemini_api_key"]
genai.configure(api_key=key)
model = genai.GenerativeModel("gemini-2.0-flash-lite")

st.title("📊 Gemini Analyst: Execute + Explain + Chat")

# Upload
transaction_file = st.file_uploader("📁 Upload Transaction CSV", type=["csv"], key="trans")
dict_file = st.file_uploader("📘 Upload Data Dictionary CSV", type=["csv"], key="dict")

# Session state for history
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

    # Show history
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

    # Input
    user_input = st.chat_input("💬 Ask a question about your data")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.spinner("🤖 Generating Python code..."):
            # Prompt Gemini to generate code
            prompt = f"""
You are a helpful Python code generator.
Your goal is to write Python code snippets based on the user'squestionand the provided DataFrame information.
Here's the context:
**User Question:**
{question}
**DataFrame Name:**
{df_name}
**DataFrame Details:**
{data_dict_text}
**Sample Data (Top 2 Rows):**
{example_record}

**Instructions:**
1. Write Python code that addresses the user's question by querying or
manipulating the DataFrame.
2. **Crucially, use the `exec()` function to execute the generated
code.**
3. Do not import pandas
4. Change date column type to datetime
5. **Store the result of the executed code in a variable named
`ANSWER`.**
This variable should hold the answer to the user's question (e.g.,
a filtered DataFrame, a calculated value, etc.).
6. Assume the DataFrame is already loaded into a pandas DataFrame object
named `{df_name}`. Do not include code to load the DataFrame.
7. Keep the generated code concise and focused on answering the question.
8. If the question requires a specific output format (e.g., a list, a
single value), ensure the `query_result` variable holds that format.

**Example:**
If the user asks: "Show me the rows where the 'age' column is
greater than 30."
And the DataFrame has an 'age' column.
The generated code should look something like this (inside the
`exec()` string):
```python
query_result = {df_name}[{df_name}['age'] > 30]
"""
            code_response = model.generate_content(prompt)
            generated_code = code_response.text.strip().replace("```python", "").replace("```", "")

            # Execute
            try:
                local_vars = {"df": df, "pd": pd}
                exec(generated_code, {}, local_vars)
                answer_data = local_vars.get("ANSWER", "No ANSWER found.")

                # Ask Gemini to explain the result
                explain_prompt = f"""
User asked:
{user_input}

Executed Python code:
{generated_code}

Result:
{str(answer_data)}

Now:
1. Summarize the result in plain English.
2. Provide analysis and interpretation.
3. Add your opinion or business insight based on the result.
"""
                summary_response = model.generate_content(explain_prompt)

                with st.chat_message("assistant"):
                    st.markdown("**🧠 Generated Code**")
                    st.code(generated_code, language="python")
                    st.markdown("**✅ Result**")
                    st.write(answer_data)
                    st.markdown("**🗣️ Gemini Opinion**")
                    st.markdown(summary_response.text)

                # Save to session history
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
