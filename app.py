import gradio as gr
import requests
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HRPolicyAssistant-Frontend")

API_URL = os.getenv("API_URL", "https://hr-assistant-rg-fkb4dxf2duguabae.centralus-01.azurewebsites.net/ask")

def chat_with_hr(user_message, chat_history):
    payload = {
        "messages": [
            {"role": "user", "content": u} if i % 2 == 0 else {"role": "assistant", "content": a}
            for i, (u, a) in enumerate(chat_history)
            for a in ([a] if a is not None else [""])
        ]
    }
    payload["messages"].append({"role": "user", "content": user_message})

    try:
        response = requests.post(API_URL, json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()
            assistant_message = data.get("answer", "No answer returned.")
            chat_history.append((user_message, assistant_message))
            return chat_history, chat_history, "" 
        else:
            error_message = f"❌ Error {response.status_code}: {response.text}"
            logger.error(error_message)
            chat_history.append((user_message, error_message))
            return chat_history, chat_history, "" 

    except Exception as e:
        error_message = f"⚠️ Request failed: {str(e)}"
        logger.exception("Exception in chat_with_hr")
        chat_history.append((user_message, error_message))
        return chat_history, chat_history, ""  

def reset_chat():
    return [], [], ""

# Gradio UI
with gr.Blocks(
    title="🏢 HR Policy Assistant",
    theme=gr.themes.Soft(),
    analytics_enabled=False
) as demo:
    with gr.Row():
        with gr.Column(scale=4):
            gr.Markdown(
                """
                # 🏢 HR Policy Assistant  
                Welcome! 👋  
                Ask me anything about **company HR policies**.  
                I will only answer from the official HR documents.  
                """
            )

            chatbot = gr.Chatbot(
                label="💬 Chat Window",
                height=450,
                bubble_full_width=False,
                show_copy_button=True,
                render_markdown=True
            )

            msg = gr.Textbox(
                placeholder="Type your HR question here and press Enter...",
                label="Your Question",
                lines=2
            )

            with gr.Row():
                clear = gr.Button("🗑️ Clear Chat", variant="secondary")
                submit = gr.Button("➡️ Send", variant="primary")

            state = gr.State([])

            submit.click(chat_with_hr, inputs=[msg, state], outputs=[chatbot, state, msg])
            msg.submit(chat_with_hr, inputs=[msg, state], outputs=[chatbot, state, msg])
            clear.click(reset_chat, None, [chatbot, state, msg])

        with gr.Column(scale=1, min_width=200):
            gr.Markdown(
                """
                ### ℹ️ About this Assistant
                - Only answers from **HR policies**.  
                - If info is missing, it will say so.  
                - Use the chat for follow-up questions.  

                ---
                ✅ Data Source: Company HR Docs  
                🔒 Secure API (Azure)  
                """
            )

# Queue for concurrency
demo.queue()

# Mount Gradio into FastAPI app for Azure
app = gr.mount_gradio_app(app=None, blocks=demo, path="/")

# Local run (useful before deploying to Azure)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
