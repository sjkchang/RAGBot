from flask import Flask
from flask import request
import redis
import os
import redis_vector_db.vector_db as vector_db
import ingest.ingest_pdf as ingest
import openai
import json
import sqlite3
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI()

app = Flask(__name__)

redis_connection = vector_db.getConnection()
print(ingest.ingest(redis_connection))

@app.route('/query/related-docs')
def related_docs():
    query = request.args.get('query', type=str)
    print(query)
    if(query):
        results = vector_db.search_pdf_redis(redis_connection, query, vector_field="content_embedding", k=10)
        return results
    else:
        return {"error": "No query provided"}, 400


'''
POST /query
{
    "query": {
        type: string,
        required: true,
    }
    "messages": [
        {
            role: {
                type: string, (ex. user, system, assistant)
                required: true
            },
            content: {
                type: string
                required: true
            }
        }
    ],
    required: false
    
}
'''
@app.route('/query', methods=['POST'])
def chatbot_query():
    body = request.get_json()
    print(body)
    if(body['query']):
        related_documents = vector_db.search_pdf_redis(redis_connection, body["query"], vector_field="content_embedding", k=10)
        
        # Prepare the messages and documents for the chat model
        documents = []
        for i in range(3):
            documents.append({'role': 'system', 'content': "Use this in section of a document to aid in your responses: " + related_documents["documents"][i]["content"]})
        
        if("messages" not in body):
            messages = [{'role': 'system', 'content': "You are a Macro Economics Assistant with expertise in Indias budget"}]
        else:
            messages = []
        if 'messages' in body:
            for message in body['messages']:
                messages.append(message)
        messages.append({'role': 'user', 'content': body['query']})

        response = client.chat.completions.create(
            model="gpt-4",
            messages=documents + messages,
            max_tokens=200
        )

        # Store the query and the response in the database
        conn = sqlite3.connect('queries_responses.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS queries_responses (
                query TEXT,
                response TEXT
            )
        ''')
        c.execute('''
            INSERT INTO queries_responses (query, response) VALUES (?, ?)
        ''', (body['query'], response.choices[0].message.content))
        conn.commit()
        conn.close()

        return {
            "response": response.choices[0].message.content,
            "messages": messages + [{"role": "assistant", "content": response.choices[0].message.content}]
        }
    else:
        return {"error": "No query provided"}, 400

@app.route('/get-queries-responses', methods=['GET'])
def get_queries_responses():
    conn = sqlite3.connect('queries_responses.db')
    c = conn.cursor()
    c.execute('SELECT * FROM queries_responses')
    data = c.fetchall()
    conn.close()

    # Convert the data to a list of dictionaries for easier JSON serialization
    data_dict = [{"query": row[0], "response": row[1]} for row in data]

    return {"data": data_dict}

if __name__ == '__main__':
    app.run(debug=True)