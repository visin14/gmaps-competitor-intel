import os, re, logging
import google.generativeai as genai
from ai.base_client import BaseAIClient


class GeminiClient(BaseAIClient):
    provider = 'gemini'

    _working_model = None  # remembered across requests once a model is known to work

    def __init__(self, api_key: str, model: str = None):
        super().__init__()
        genai.configure(api_key=api_key)
        self.model_name = model or GeminiClient._working_model or os.environ.get('GEMINI_MODEL', 'gemini-flash-latest')
        self.model = genai.GenerativeModel(self.model_name)
        self._discovered = False
        self._queue, self._tried = [], set()

    def _generate(self, prompt: str) -> str:
        text = self.model.generate_content(prompt).text
        GeminiClient._working_model = self.model_name
        return text

    @staticmethod
    def _version(name: str):
        m = re.search(r'(\d+(?:\.\d+)?)', name)
        return float(m.group(1)) if m else 0.0

    def _switch_to(self, name: str):
        logging.warning('Gemini model %s unavailable, trying %s', self.model_name, name)
        self.model_name = name
        self.model = genai.GenerativeModel(name)

    def _on_error(self, exc: Exception) -> bool:
        """Model retired/unavailable (404)? Follow the API's suggested model, then try the newest flash models."""
        msg = str(exc)
        if '404' not in msg and 'not found' not in msg.lower() and 'no longer available' not in msg.lower():
            return False
        if not self._discovered:
            self._discovered = True
            self._tried = {self.model_name}
            suggested = re.findall(r'models/([\w.\-]+)', msg)
            self._queue = [s for s in suggested if s not in self._tried][-1:]
            try:
                names = [m.name.replace('models/', '') for m in genai.list_models()
                         if 'generateContent' in m.supported_generation_methods]
                flash = [n for n in names if 'flash' in n and not any(x in n for x in ('exp', 'preview', 'thinking', 'image', 'tts', 'live', 'lite', '8b'))]
                self._queue += sorted(flash, key=self._version, reverse=True)
            except Exception as e:
                logging.error('Gemini model discovery failed: %s', e)
        while self._queue:
            name = self._queue.pop(0)
            if name not in self._tried:
                self._tried.add(name)
                self._switch_to(name)
                return True
        return False
