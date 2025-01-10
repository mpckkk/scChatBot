import gradio as gr
import time
from zhipuai import ZhipuAI


class ChatBot:
    def __init__(self):
        self.client = ZhipuAI(api_key="") #change to your own zhipu API

    def query_zhipuai(self, query):
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
        print(f"Message {x.index} was {'liked' if x.liked else 'disliked'}: {x.value}")

    def add_message(self, history, message):
        if isinstance(message, dict):
            for x in message.get("files", []):
                history = history + [({"path": x}, None)]
            if message.get("text"):
                history = history + [(message["text"], None)]
        else:
            history = history + [(message, None)]
        return history, gr.MultimodalTextbox(value=None, interactive=False)

    def generate_response(self, history):
        if not history:
            return history

        user_message = history[-1][0]
        if isinstance(user_message, dict):
            content = "I see you've shared a file!"
        else:
            if "search:" in user_message.lower():
                query = user_message.lower().replace("search:", "").strip()
                content = self.query_zhipuai(query)
            else:
                content = self.query_zhipuai(user_message)

        if not content:
            content = "I apologize, but I couldn't process that properly."

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
