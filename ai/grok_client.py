import os, logging
from openai import OpenAI
from ai.base_client import BaseAIClient


class GrokClient(BaseAIClient):
    provider = 'grok'

    def __init__(self, api_key: str, model: str = None):
        super().__init__()
        self.client = OpenAI(api_key=api_key, base_url='https://api.x.ai/v1', timeout=60)
        self.model = model or GrokClient._working_model or os.environ.get('GROK_MODEL', 'grok-3-mini')
        self._discovered = False

    _working_model = None

    def _generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}],
        )
        text = response.choices[0].message.content if response.choices else None
        if text:
            GrokClient._working_model = self.model
        return text

    def _on_error(self, exc: Exception) -> bool:
        """If the configured model is gone, discover an available Grok chat model."""
        msg = str(exc).lower()
        if self._discovered or not ('404' in msg or 'not found' in msg or 'does not exist' in msg):
            return False
        self._discovered = True
        try:
            ids = [m.id for m in self.client.models.list() if m.id.startswith('grok')]
            ids = [i for i in ids if not any(x in i for x in ('image', 'vision', 'imagine'))]
            if ids:
                logging.warning('Grok model %s unavailable, switching to %s', self.model, ids[0])
                self.model = ids[0]
                return True
        except Exception as e:
            logging.error('Grok model discovery failed: %s', e)
        return False
