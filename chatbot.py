import gradio as gr
import time
import os
import speech_recognition as sr
from zhipuai import ZhipuAI
from docx import Document
from PyPDF2 import PdfReader
class ChatBot:
    def __init__(self):
        # Replace with your ZhipuAI API key
        self.client = ZhipuAI(api_key="API HERE")

    def read_file_content(self, file_path):
        """Reads the content of supported file types (TXT, DOC/DOCX, PDF, WAV)."""
        try:
            if file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

            elif file_path.endswith(('.doc', '.docx')):
                doc = Document(file_path)
                return '\n'.join([para.text for para in doc.paragraphs])

            elif file_path.endswith('.pdf'):
                with open(file_path, 'rb') as f:
                    pdf = PdfReader(f)
                    text = []
                    for page in pdf.pages:
                        text.append(page.extract_text())
                return '\n'.join(text)

            elif file_path.endswith('.wav'):
                recognizer = sr.Recognizer()
                with sr.AudioFile(file_path) as source:
                    audio = recognizer.record(source)
                    text = recognizer.recognize_google(audio)  # Use Google Speech-to-Text
                return f"AUDIO CONTENT:\n{text}"

            else:
                return f"Unsupported file type: {os.path.splitext(file_path)[1]}"

        except Exception as e:
            return f"Error reading file: {str(e)}"

    def query_zhipuai(self, query):
        """Sends the query to the ZhipuAI API and returns the response."""
        try:
            response = self.client.chat.completions.create(
                model="glm-4-flash",
                messages=[{"role": "user", "content": query}],
                top_p=0.7,
                temperature=0.1,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def print_like_dislike(self, x: gr.LikeData):
        """Handles like/dislike feedback from the user."""
        print(f"Message {x.index} was {'liked' if x.liked else 'disliked'}: {x.value}")
    def add_message(self, history, message):
        """Adds a user message (text or file) to the chat history."""
        final_query = ""

        if isinstance(message, dict):
            # Combine text input and file contents
            text_content = message.get("text", "")
            file_contents = []

            for file_path in message.get("files", []):
                content = self.read_file_content(file_path)
                # Remove prefixes like "FILE CONTENT:" and "AUDIO CONTENT:"
                if content.startswith("FILE CONTENT:") or content.startswith("AUDIO CONTENT:"):
                    content = content.split(":", 1)[-1].strip()  # Remove the prefix
                file_contents.append(content)

            final_query = '\n\n'.join([text_content] + file_contents)

        else:
            final_query = message

        history = history + [(final_query, None)]
        return history, gr.MultimodalTextbox(value=None, interactive=False)
    def generate_response(self, history):
        """Generates a response from the chatbot and streams it to the UI."""
        if not history:
            return history

        user_message = history[-1][0]
        content = self.query_zhipuai(user_message)

        history[-1] = (history[-1][0], "")
        for char in content:
            history[-1] = (history[-1][0], history[-1][1] + char)
            time.sleep(0.02)
            yield history


def create_demo():
    chatbot = ChatBot()
    with gr.Blocks(css="""
        .title {
            font-size: 2em;
            text-align: center;
            margin: 20px;
            color: #4A90E2;
            display: inline-block;
        }
        .title span {
            animation: bling 1.5s infinite;
            display: inline-block;
        }
        .title span:nth-child(1) { animation-delay: 0s; }
        .title span:nth-child(2) { animation-delay: 0.1s; }
        .title span:nth-child(3) { animation-delay: 0.2s; }
        .title span:nth-child(4) { animation-delay: 0.3s; }
        .title span:nth-child(5) { animation-delay: 0.4s; }
        .title span:nth-child(6) { animation-delay: 0.5s; }
        .title span:nth-child(7) { animation-delay: 0.6s; }
        @keyframes bling {
            0%, 100% { opacity: 0.6; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.2); }
        }
    """) as demo:
        gr.HTML(
            "<div class='title'>" + "".join(f"<span>{char}</span>" for char in "🌟 ZHIPU AI Chatbot 🌟") + "</div>")

        chat_interface = gr.Chatbot(
            height=600,
            bubble_full_width=False,
            avatar_images=[
                "https://api.dicebear.com/7.x/adventurer/svg?seed=user",
                "https://api.dicebear.com/7.x/bottts/svg?seed=bot"
            ]
        )

        chat_input = gr.MultimodalTextbox(
            interactive=True,
            file_count="multiple",
            placeholder="Enter message or upload file...",
            show_label=False,
            sources=["microphone", "upload"]
        )

        chat_msg = chat_input.submit(
            fn=chatbot.add_message,
            inputs=[chat_interface, chat_input],
            outputs=[chat_interface, chat_input]
        ).then(
            fn=chatbot.generate_response,
            inputs=chat_interface,
            outputs=chat_interface,
            api_name="bot_response"
        )

        chat_msg.then(
            lambda: gr.MultimodalTextbox(interactive=True),
            None,
            [chat_input]
        )

        chat_interface.like(
            chatbot.print_like_dislike,
            None,
            None,
            like_user_message=True
        )

    return demo


if __name__ == "__main__":
    demo = create_demo()
    demo.launch(share=True)
