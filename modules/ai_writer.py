import json
import urllib.request
import urllib.error
import threading  # For running API calls in background

class AIWriter:
    """
    Handles interaction with compatible AI APIs (DeepSeek) to generate text copy.
    """
    
    # API Key should be provided by instance
    API_KEY = None
    API_URL = "https://api.deepseek.com/chat/completions"
    
    def __init__(self, api_key=None):
        if api_key:
            self.API_KEY = api_key
        else:
            self.API_KEY = None
            
    def generate_copy_async(self, topic, style="随机", callback=None, error_callback=None):
        """
        Run generation in a separate thread to avoid blocking UI.
        
        Args:
            topic (str): User topic or keywords.
            style (str): Copy style ("随机", "温柔干货", "趣味测评", "走心文案").
            callback (func): Called with list of strings on success.
            error_callback (func): Called with error message string on failure.
        """
        def _run():
            try:
                result = self.generate_copy(topic, style)
                if callback:
                    callback(result)
            except Exception as e:
                if error_callback:
                    error_callback(str(e))
                    
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def generate_copy(self, topic, style="随机"):
        """
        Synchronous generation call.
        """
        
        # Style Definitions
        style_prompts = {
            "温柔干货": "风格要求：温柔亲切、干货满满、逻辑清晰、让人有收获感。多用✨📝💡等表情。",
            "趣味测评": "风格要求：幽默风趣、个人体验感强、犀利点评、生动活泼。多用🤔👀🔥等表情。",
            "走心文案": "风格要求：情感细腻、引发共鸣、治愈系、富有哲理。多用❤️🌙💭等表情。",
            "随机": "风格要求：口语化、情绪化、多用emoji表情、吸引眼球、根据主题自由发挥。"
        }
        
        style_desc = style_prompts.get(style, style_prompts["随机"])
        
        # Internal Defaults (as per requirement)
        count = 1
        length_desc = "50-100字"
            
        system_prompt = (
            "你是一个小红书爆款文案专家。请根据用户的主题，写出{num}条吸引人的文案。\n"
            "要求：\n"
            "1. 严格围绕用户提供的主题关键词来写，不要擅自改变主题含义。\n"
            "2. 如果主题是缩写或专业术语，请保持原意（如'SCL90'是心理测试量表，不是手机）。\n"
            "3. {style_desc}\n"
            "4. 长度：每条文案控制在{len_desc}。\n"
            "5. 格式：直接返回文案内容，不要带序号，不要带其他解释性文字。\n"
            "6. 关键词：自然融入相关热门话题标签。"
        ).format(num=count, style_desc=style_desc, len_desc=length_desc)
        
        user_prompt = f"主题：{topic}"
        
        # Request Payload
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "max_tokens": 1024,
            "temperature": 1.3  # High creativity
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.API_KEY}"
        }
        
        try:
            req = urllib.request.Request(
                self.API_URL, 
                data=json.dumps(payload).encode('utf-8'), 
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status != 200:
                    raise Exception(f"API Error {response.status}")
                    
                data = json.loads(response.read().decode('utf-8'))
                
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0]['message']['content'].strip()
                    # Clean up if AI adds ### despite instruction (for robustness)
                    if "###" in content:
                        options = [s.strip() for s in content.split("###") if s.strip()]
                        return options
                    else:
                        return [content]
                else:
                    raise Exception("No content in response")
                    
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"HTTP Error {e.code}: {error_body}")
        except Exception as e:
            raise Exception(f"Request Failed: {str(e)}")

# Test usage
if __name__ == "__main__":
    writer = AIWriter()
    print("Testing AI Writer...")
    try:
        res = writer.generate_copy("夏日冰美式", style="趣味测评")
        print("Result:", res)
    except Exception as e:
        print("Error:", e)
