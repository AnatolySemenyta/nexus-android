import os
import json
import subprocess
import time
import hashlib

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
    
    def check_password(self, pwd):
        if pwd == "исток":
            self.mode = "echo"
            self.authenticated = True
            return True
        return False
    
    def is_echo_mode(self):
        return self.mode == "echo"
    
    def think(self, prompt):
        try:
            termux_path = "/data/data/com.termux/files/usr/bin/llama-cli"
            if not os.path.exists(termux_path):
                return "❌ Termux не найден. Установите Termux."
            
            cmd = [
                termux_path,
                "-m", self.model_path,
                "-p", prompt,
                "--temp", "0.7",
                "-c", "256",
                "-t", "2",
                "-n", "60"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                return "Ошибка модели."
            return result.stdout.strip() or "Не могу ответить."
        except subprocess.TimeoutExpired:
            return "Слишком долго."
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
            "модель_загружена": True
        }
    
    def clear_memory(self):
        self.memory = []
        self.save_memory()
        return "Память очищена"
