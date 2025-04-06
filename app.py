import streamlit as st
import pandas as pd
import google.generativeai as genai

try:
    key = st.secrets['gemini_api_key']
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')

    st.title('📊 Gemini - Sales Insight from CSV')

    # 1. Upload Transaction File
    transaction_file = st.file_uploader("📥 Upload Transaction CSV", type=["csv"], key="trans")

    # 2. Upload Data Dictionary File
    dict_file = st.file_uploader("📥 Upload Data Dictionary CSV", type=["csv"], key="dict")

    if transaction_file is not None and dict_file is not None:
        # Read files
        df_trans = pd.read_csv(transaction_file)
        df_dict = pd.read_csv(dict_file)

        # Show data preview
        st.subheader("🔍 Transaction Data Preview")
        st.dataframe(df_trans)

        st.subheader("📘 Data Dictionary Preview")
        st.dataframe(df_dict)

        # Combine into context
        context_info = f"""Here is the data dictionary for interpreting the transaction data:
{df_dict.to_markdown(index=False)}

Now use this context to help analyze or answer questions about the transaction data.
"""

        if "chat" not in st.session_state:
            st.session_state.chat = model.start_chat(history=[
                {"role": "user", "parts": [context_info]}
            ])

        def role_to_streamlit(role: str) -> str:
            return 'assistant' if role == 'model' else role

        for message in st.session_state.chat.history:
            with st.chat_message(role_to_streamlit(message.role)):
                st.markdown(message.parts[0].text)

        if prompt := st.chat_input("💬 Ask anything about your transaction data"):
            st.chat_message('user').markdown(prompt)

            full_prompt = f"{context_info}\n\nUser Question: {prompt}\nAnswer based on the data."
            response = st.session_state.chat.send_message(full_prompt)

            with st.chat_message('assistant'):
                st.markdown(response.text)

    else:
        st.info("📌 Please upload both the Transaction CSV and the Data Dictionary CSV to begin.")

except Exception as e:
    st.error(f'An error occurred: {e}')
