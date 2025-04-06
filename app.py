import streamlit as st
import pandas as pd

try:
    key = st.secrets['gemini_api_key']
    configure(api_key=key)
    model = GenerativeModel('gemini-2.0-flash-lite')

    st.title('Gemini with Sales Data')

    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        # Show preview
        st.subheader("Data Preview")
        st.dataframe(df)

        # Generate Data Dictionary
        st.subheader("Data Dictionary")
        data_dict = pd.DataFrame({
            "Column Name": df.columns,
            "Data Type": [df[col].dtype for col in df.columns],
            "Example Value": [df[col].dropna().unique()[:3] for col in df.columns]
        })
        st.dataframe(data_dict)

        # Prepare context for the model
        context_info = f"The uploaded CSV contains the following data dictionary:\n{data_dict.to_markdown(index=False)}\n\nNow use this as context to answer user questions."

        if "chat" not in st.session_state:
            st.session_state.chat = model.start_chat(history=[
                {"role": "user", "parts": [context_info]}
            ])

        def role_to_streamlit(role: str) -> str:
            return 'assistant' if role == 'model' else role

        for message in st.session_state.chat.history:
            with st.chat_message(role_to_streamlit(message.role)):
                st.markdown(message.parts[0].text)

        if prompt := st.chat_input("Ask a question about your data"):
            st.chat_message('user').markdown(prompt)

            full_prompt = f"{context_info}\n\nUser Question: {prompt}\nAnswer based on the data."
            response = st.session_state.chat.send_message(full_prompt)

            with st.chat_message('assistant'):
                st.markdown(response.text)

    else:
        st.info("Please upload a CSV file to begin.")

except Exception as e:
    st.error(f'An error occurred: {e}')
