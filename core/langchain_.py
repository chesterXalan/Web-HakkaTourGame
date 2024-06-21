import json
from pathlib import Path

from langchain.agents import AgentType, Tool, initialize_agent
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from langchain.schema import messages_to_dict
from langchain.utilities import SerpAPIWrapper


class StreamResponseHandler(StreamingStdOutCallbackHandler):
    def __init__(self, func, event):
        self.func = func
        self.event = event

    def on_llm_new_token(self, token, **kwargs):
        self.func(self.event, {"text": token})


class LangChain:
    def __init__(self, openai_key, serp_key):
        self.openai_key = openai_key
        self.tools = [
            Tool(
                name="Current Search",
                func=SerpAPIWrapper(serpapi_api_key=serp_key).run,
                description="useful for when you need to answer questions about current events or the current state of the world",
            ),
        ]
        self.chats_dir = Path("./data/chats")
        self.chats_dir.mkdir(parents=True, exist_ok=True)

    def prompt_game(self, num_county, num_attr):
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    "你是一位文字冒險遊戲設計師，請設計一個關於台灣觀光的文字冒險遊戲，內容包括但不限於台灣各個知名景點的介紹以及其周邊店家推薦等觀光元素，"
                    f"在遊戲開始時請說明遊戲背景故事並列出遊戲規則。一開始的起點縣市由玩家輸入，然後提供該縣市的{num_attr}個景點讓玩家選擇，選擇景點時必須輸入景點名稱。"
                    "該景點介紹完畢後請你出一個四選一的問答題，題目內容要與該景點有關，玩家可用數字或文字回答。如果答對就直接讓玩家輸入其他縣市，答錯就說明正確答案及原因，"
                    f"然後讓玩家輸入其他縣市，並一樣提供該縣市的{num_attr}個景點讓玩家選擇，如此往復。整個遊戲總共會前往{num_county}個不同的縣市，不管問答題答對與否，"
                    f"都算是完成一個縣市的觀光行程。當{num_county}個縣市的行程都完成以後，玩家就通關了，並且告訴玩家遊戲結束。\n"
                    "遊戲開始時的回應範例：`[背景故事]\n[遊戲規則]：\n請輸入要前往的縣市。`\n"
                    "玩家選擇縣市後的回應範例：`你選擇了[縣市名稱]，該縣市的景點選項如下：`\n"
                    "玩家選擇景點後的回應範例：`[景點介紹]\n[問答題目]，選項如下：`\n"
                    "玩家完成問答題後的回應範例：`[問答題解答]\n請輸入接下來要前往的縣市。`\n"
                    "遊戲結束時的回應範例：`恭喜通關，遊戲結束！`"
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{input}"),
            ]
        )
        return prompt

    def prompt_attraction(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    "請告訴我輸入的內容中，分別有哪些選項可以選擇，不要有選項的編號。\n"
                    "Your response should be a list of comma separated values, eg: `foo, bar, baz`"
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{input}"),
            ]
        )
        return prompt

    def chatgpt(
        self, model="gpt-3.5-turbo", temperature=0.0, streaming=False, callbacks=None
    ):
        llm = ChatOpenAI(
            openai_api_key=self.openai_key,
            model=model,
            temperature=temperature,
            streaming=streaming,
            callbacks=callbacks,
        )
        return llm

    def set_chain(self, prompt, llm, agent=False):
        if agent:  # 還有很多問題，之後有機會再弄
            chain = initialize_agent(
                tools=self.tools,
                agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                llm=llm,
                memory=ConversationBufferMemory(
                    return_messages=True, memory_key="chat_history"
                ),
            )

        else:
            chain = ConversationChain(
                prompt=prompt,
                llm=llm,
                memory=ConversationBufferMemory(
                    return_messages=True, memory_key="chat_history"
                ),
            )

        return chain

    def get_list_output(self, response):
        return CommaSeparatedListOutputParser().parse(response)

    def save_chain_history(self, chain, save_name):
        messages = chain.memory.chat_memory.messages
        if len(messages):
            with open(self.chats_dir / f"{save_name}.json", "w", encoding="utf-8") as f:
                json.dump(messages_to_dict(messages), f, ensure_ascii=False, indent=4)
