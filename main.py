import os
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.schema.runnable import RunnablePassthrough
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
import requests
import json
import requests
import json
import datetime
from dotenv import load_dotenv


load_dotenv(".env")


def item_API(word):
    url = 'https://service.api.metro.tokyo.lg.jp/api/t131091d0000000161-7a38c2dfdaab09be511867924a4ad330-0/json'
    params = {
        'limit': 5
    }
    payload = {
    "searchCondition": {
        "stringAndSearch": [
        {
            "column": "ゴミの品目",
            "relationship": "contains",
            "condition": word
        }
        ]
    }
    }
    headers = {
    'accept': 'application/json',
    'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, params=params, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return json.dumps(data, indent=2, ensure_ascii=False)

    except requests.exceptions.HTTPError as errh:
        print(f"Http Error: {errh}")
        print(f"Response Body: {response.text}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Oops: Something Else: {err}")


def when_API(locate, category):
    url = 'https://service.api.metro.tokyo.lg.jp/api/t131091d0000000007-a4331d1df483d520922d04477412ad13-0/json'
    params = {
        'limit': 100
    }
    payload = {
    "searchCondition": {
        "stringAndSearch": [
        {
            "column": "ゴミ分類区分",
            "relationship": "contains",
            "condition": category
        },
        {
            "column": "地区名",
            "relationship": "contains",
            "condition": locate
        }
        ]
    }
    }

    headers = {
    'accept': 'application/json',
    'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, params=params, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return json.dumps(data, indent=2, ensure_ascii=False)

    except requests.exceptions.HTTPError as errh:
        print(f"Http Error: {errh}")
        print(f"Response Body: {response.text}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Oops: Something Else: {err}")


def RGA(comment):
    url = "https://api.openai.iniad.org/api/v1/"
    api_key = os.getenv("key")
    os.environ["OPENAI_API_KEY"] = api_key

    embeddings_model = OpenAIEmbeddings(
        openai_api_base=url,
        openai_api_key=api_key
    )

    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        openai_api_base=url,
        openai_api_key=api_key
    )

    persist_directory = "chroma_db"
    db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings_model
    )
    retriever = db.as_retriever(search_kwargs={'k': 3})
    template = """
    なるべく詳細に。必要な場合は、電話番号やURLの記載も行え。
    参考情報:
    {context}

    質問:
    {question}
    """
    prompt = ChatPromptTemplate.from_template(template)
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    answer_2 = rag_chain.invoke(comment)
    return answer_2

def SINAGAWA_trash_info(where, question):
        answer = question
        API_result = item_API(answer)
        hits_list = json.loads(API_result)
        try:
            item = []
            when = []
            for i in hits_list['hits']:
                item.append(i["分別区分"])
                when.append(when_API("豊町5丁目", i["分別区分"]))
            print("情報", item)
        except IndexError as e:
            print(e)
        

        answer_2 = RGA(f"""ユーザーは{answer}のゴミ出しに関数情報を知りたいようです。
                        以下の情報の中にそれに関する情報があったら教えてください。
                        {answer}やほかの検索結果の分別区分や、料金、捨てる際の注意点などを教えてください。
                        ほかにも{item}のすべてにおいて、それを捨てる際の注意点などについても詳しく教えてください。
                        また、{answer}やほかの検索結果の次回の収集日についても教えてください。
                        ちなみに、ユーザーは{where}に住んでいて、今日は{datetime.datetime.now()}です。
                        以下のAPI情報と、参考情報から参上して回答しろ。
                        全く情報が無い場合、わからないと述べてください。
                        
                        
                        「{answer}に関するAPI情報」 
                        {API_result}
                        「関連するAPI情報」
                        {when}
                        """)
        print("回答:")
        print(answer_2)
        print("\n\n\n")

question = input("質問を入力:\n")
SINAGAWA_trash_info("豊町5丁目", question)