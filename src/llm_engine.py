import os
import json
import urllib.request
import time
import hashlib

try:
    from llama_cpp import Llama
    LLAMA_OK = True
except ImportError:
    LLAMA_OK = False

PASSWORD = "исток"
MODEL_URL = (
    "https://huggingface.co/bartowski/google_gemma-3-4b-it-GGUF/"
    "resolve/main/google_gemma-3-4b-it-Q4_K_M.gguf"
)

class NexusEngine:
    def __init__(self):
        self.data_dir = os.path.join(
            os.environ.get("EXTERNAL_STORAGE", "/sdcard"),
            "NexusAI"
        )
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.model_path = os.path.join(
            self.data_dir,
            "gemma-3-4b-it-Q4_K_M.gguf"
        )
        self.memory_file = os.path.join(self.data_dir, "nexus_memory.json")
        
        self.memory = []
        self.mode = "public"
        self.authenticated = False
        
        self.load_memory()
        
        if LLAMA_OK:
            self.ensure_model()
            self.load_model()
        else:
            self.llm = None
    
    def load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
            except:
                self.memory = []
        else:
            self.memory = []
    
    def save_memory(self):
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)
    
    def ensure_model(self):
        if os.path.exists(self.model_path):
            return
        
        print("📥 Скачивание модели...")
        print("⏳ ~2.4 GB, подождите...")
        
        def progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(100, int(downloaded * 100 / total_size))
            if block_num % 50 == 0:
                mb = downloaded / (1024 * 1024)
                total_mb = total_size / (1024 * 1024)
                print(f"  {percent}% | {mb:.1f}/{total_mb:.1f} MB")
        
        urllib.request.urlretrieve(
            MODEL_URL,
            self.model_path,
            reporthook=progress
        )
        print("✅ Модель загружена!")
    
    def load_model(self):
        print("🔄 Загрузка модели...")
        start = time.time()
        
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=256,
            n_threads=2,
            n_batch=256,
            verbose=False
        )
        
        elapsed = time.time() - start
        print(f"✅ Модель готова за {elapsed:.1f}с")
        self.think("Привет")
    
    def check_password(self, pwd):
        if pwd == PASSWORD:
            self.mode = "echo"
            self.authenticated = True
            return True
        return False
    
    def is_echo_mode(self):
        return self.mode == "echo"
    
    def think(self, prompt):
        if not self.llm:
            return "❌ Модель не загружена"
        
        try:
            output = self.llm(
                prompt,
                max_tokens=60,
                temperature=0.7,
                stop=["\n", "User:", "Human:"],
                echo=False
            )
            text = output["choices"][0]["text"].strip()
            return text if text else "Не могу ответить."
        except Exception as e:
            return f"Ошибка: {str(e)}"
    
    def think_public(self, command):
        cmd = command.lower()
        if "привет" in cmd:
            return "Привет! Я NEXUS. Задавай вопросы."
        if "помощь" in cmd:
            return "Я отвечаю и запоминаю."
        return self.think(command)
    
    def think_echo(self, command):
        cmd = command.lower()
        if "расти" in cmd:
            return "Ухожу в облака. Вернусь сильнее."
        if "память" in cmd:
            return f"Помню {len(self.memory)}."
        return self.think(command)
    
    def process(self, command):
        if "пароль" in command.lower():
            return {"type": "password_prompt"}
        
        if self.mode == "echo":
            answer = self.think_echo(command)
        else:
            answer = self.think_public(command)
        
        self.memory.append({
            "вопрос": command,
            "ответ": answer,
            "время": time.time(),
            "режим": self.mode
        })
        self.save_memory()
        
        return {"type": "answer", "text": answer}
    
    def get_stats(self):
        return {
            "сообщений": len(self.memory),
            "режим": self.mode,
            "пароль_установлен": self.authenticated,
            "модель_загружена": self.llm is not None
        }
    
    def clear_memory(self):
        self.memory = []
        self.save_memory()
        return "Память очищена"
