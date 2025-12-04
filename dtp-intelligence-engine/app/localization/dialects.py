from typing import Dict

class DialectManager:
    """
    Maps simplified language codes (ar-EG) to vendor-specific configurations.
    """
    
    # Deepgram Model Mapping
    STT_MODELS = {
        "en-US": "nova-2-phone",
        "ar-EG": "nova-2-general", # Deepgram general model supports dialects better
        "ar-SA": "nova-2-general",
        "ar-AE": "nova-2-general"
    }
    
    # Azure/ElevenLabs Voice Mapping
    TTS_VOICES = {
        "en-US": {"provider": "elevenlabs", "voice_id": "21m00Tcm4TlvDq8ikWAM"}, # Rachel
        "ar-EG": {"provider": "azure", "voice_id": "ar-EG-SalmaNeural"},
        "ar-SA": {"provider": "azure", "voice_id": "ar-SA-ZariyahNeural"},
        "ar-AE": {"provider": "azure", "voice_id": "ar-AE-FatimaNeural"}
    }

    @staticmethod
    def get_stt_config(language_code: str) -> Dict[str, str]:
        model = DialectManager.STT_MODELS.get(language_code, "nova-2-general")
        # Deepgram needs specific language codes for Arabic
        lang = language_code if "ar" in language_code else "en-US"
        return {"model": model, "language": lang}

    @staticmethod
    def get_tts_config(language_code: str, preferred_gender: str = "female") -> Dict[str, str]:
        """
        Returns the best voice provider and ID for the dialect.
        Arabic is often better on Azure Neural than ElevenLabs (currently).
        """
        return DialectManager.TTS_VOICES.get(language_code, DialectManager.TTS_VOICES["en-US"])