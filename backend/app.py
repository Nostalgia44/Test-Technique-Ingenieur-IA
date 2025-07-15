# Main Flask app file
# Handles routes, requests and Qwen model integration

# Flask for web app creation
from flask import Flask, request, jsonify
from flask_cors import CORS

import config # To use get_client()
from duckduckgo_search import DDGS # For web search
import requests
from bs4 import BeautifulSoup # For reading web pages

from prompt import system_prompt, query_generation_prompt
from datetime import datetime
import json

# For the VLM
import base64
import time
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
CORS(app)  

client = config.get_client()

# Image upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_image_with_vlm(image_path, question="Describe this image in details."):
    """Analyze an image with QwenVL via OpenRouter"""
    
    try:
        # Encode image to base64 for API consumption
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        print(f"[VLM] Analyzing image with question: {question}")
        
        # Call vision-language model via OpenRouter
        response = client.chat.completions.create(
            model="qwen/qwen2.5-vl-32b-instruct:free",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            max_tokens=800
        )
        
        result = response.choices[0].message.content
        return result
        
    except Exception as e:
        print(f"[VLM] Error: {e}")
        return f"Error analyzing image: {e}"

def get_complete_page_content(url):
    """Scrape full content from a webpage"""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove scripts and styles to keep only readable content
        for element in soup(["script", "style",]):
            element.decompose()
        
        # Extract all visible text
        full_text = soup.get_text(separator="\n", strip=True)
        
        # Basic cleanup and limit to 10k chars
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        clean_text = '\n'.join(lines)
        
        return clean_text[:9500]  
    except Exception as e:
        return f"[Loading error: {e}]"

def search_web(query, max_results=12):
    """Search the web and scrape full content from results"""
    full_results = []
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=max_results)
        for r in results:
            url = r["href"]
            title = r.get("title", "")
            summary = r.get("body", "")
            content = get_complete_page_content(url)
            full_results.append({
                "title": title, 
                "url": url,
                "summary": summary,
                "content": content
            })
    return full_results

def generate_search_query(user_query):
    """
    AI-driven decision: search the web OR respond directly
    Returns JSON with action type and content
    """
    print(f"[QUERY_GEN] Processing query: '{user_query}'")
    
    try:
        response = client.chat.completions.create(
            model="qwen/qwen-2.5-coder-32b-instruct:free",
            messages=[
                {"role": "system", "content": query_generation_prompt},
                {"role": "user", "content": f"User question: {user_query}"}
            ],
            max_tokens=200,
            temperature=0.3
        )
        
        llm_response = response.choices[0].message.content.strip()
        
        # Parse JSON response from AI
        try:
            decision_json = json.loads(llm_response)
            print(f"[QUERY_GEN] Parsed JSON: {decision_json}")
            
            if "search_web" in decision_json:
                search_query = decision_json["search_web"]
                print(f"[QUERY_GEN] Decision: SEARCH with query '{search_query}'")
                return {"action": "search", "query": search_query}
            
            elif "direct_response" in decision_json:
                direct_answer = decision_json["direct_response"]
                print(f"[QUERY_GEN] Decision: DIRECT RESPONSE")
                return {"action": "direct", "response": direct_answer}
            
            else:
                print("[QUERY_GEN] Invalid JSON format, defaulting to search")
                return {"action": "search", "query": user_query}
                
        except json.JSONDecodeError:
            print(f"[QUERY_GEN] JSON parsing error, defaulting to search: {llm_response}")
            return {"action": "search", "query": user_query}
            
    except Exception as e:
        print(f"[QUERY_GEN] Error: {e}")
        return {"action": "search", "query": user_query}



@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint with AI-driven decision making"""
    try:
        data = request.get_json()
        user_query = data.get('message', '')
        
        if not user_query:
            return jsonify({'error': 'Empty message'}), 400
        
        print(f"[DEBUG] User question: {user_query}")
        
        # Step 1: AI decides whether to search or respond directly
        decision = generate_search_query(user_query)
        
        if decision["action"] == "direct":
            # Return direct response without web search
            print("[DEBUG] Direct response without web search")
            return jsonify({
                'response': decision["response"],
                'sources': [],
                'search_query_used': None,
                'web_search_performed': False
            })
        
        else:
            # Perform web search and generate response
            print("[DEBUG] Web search required")
            search_query = decision["query"]
            
            # Step 2: Execute web search
            search_results = search_web(search_query)
            
            # Step 3: Build context from search results
            context_parts = []
            for i, result in enumerate(search_results):
                part = (
                    f"{i+1}. {result['title']}\n"
                    f"URL: {result['url']}\n"
                    f"Summary: {result['summary']}\n"
                    f"Content: {result['content']}"
                )
                # Debug: show first 50 chars of content and title
                #print(result['content'][:50])
                print(result['title'])
                context_parts.append(part)
            
            context = f"Web sources (query: '{search_query}'):\n\n" + "\n\n".join(context_parts)
            sources_used = [{'title': r['title'], 'url': r['url']} for r in search_results]
            
            # Step 4: Build final prompt with search context
            user_context = (
                f"SEARCH CONTEXT: Current date: {datetime.now().strftime('%B %d, %Y')}\n"
                f"Search query used: '{search_query}'\n"
                f"User question: \"{user_query}\"\n"
                f"Number of sources analyzed: {len(search_results)}\n\n"
                f"TASK: Answer the user's question using the web data below.\n"
                f"WEB SOURCES:\n{context}"
            )

            # Step 5: Generate final response using search context
            system_message = {"role": "system", "content": system_prompt}
            user_message = {"role": "user", "content": user_context}

            response = client.chat.completions.create(
                model="qwen/qwen-2.5-coder-32b-instruct:free",
                messages=[system_message, user_message],
                max_tokens=800
            )

            return jsonify({
                'response': response.choices[0].message.content,
                'sources': sources_used, # Give all the sources read 
                'search_query_used': search_query,
                'web_search_performed': True
            })
        
    except Exception as e:
        print(f"[ERROR] Error in chat(): {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-image', methods=['POST'])
def analyze_image():
    """Endpoint for image analysis using VLM"""
    try:
        # Validate image upload
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        image_file = request.files['image']
        question = request.form.get('question', 'Describe this image in detail in French')
        
        if image_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(image_file.filename):
            return jsonify({'error': 'Unsupported file format. Use PNG, JPG, JPEG, GIF or WEBP'}), 400
        
        # Save image temporarily with timestamp to avoid conflicts
        filename = secure_filename(image_file.filename)
        timestamp = str(int(time.time()))
        filename = f"{timestamp}_{filename}"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)
        
        print(f"[DEBUG] Image saved: {image_path}")
        print(f"[DEBUG] Question: {question}")
        
        # Analyze image with VLM
        analysis_result = analyze_image_with_vlm(image_path, question)
        
        # Clean up temporary file
        try:
            os.remove(image_path)
        except:
            pass
        
        return jsonify({
            'analysis': analysis_result,
            'question_asked': question,
            'image_processed': True
        })
        
    except Exception as e:
        print(f"[ERROR] Error in analyze_image(): {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint for monitoring"""
    return jsonify({'status': 'OK'})

if __name__ == "__main__":
    app.run(debug=True, port=5000)