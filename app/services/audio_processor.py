import structlog
from typing import Optional
import os
import speech_recognition as sr
from pydub import AudioSegment
import tempfile

logger = structlog.get_logger()

class AudioProcessor:
    """
    Service for processing audio files and converting them to text.
    Supports multiple audio formats and provides transcription services.
    """
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
        # Configure recognizer settings
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        # Supported audio formats
        self.supported_formats = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
        
        # Maximum file size (50MB)
        self.max_file_size = 50 * 1024 * 1024
        
        # Maximum duration (5 minutes)
        self.max_duration_seconds = 300
    
    async def transcribe_audio(self, audio_file_path: str, language: Optional[str] = None) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file_path: Path to audio file
            language: Language code for transcription (optional)
            
        Returns:
            Transcribed text
        """
        try:
            logger.info("Starting audio transcription", file_path=audio_file_path)
            
            # Validate file
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Check file size
            file_size = os.path.getsize(audio_file_path)
            if file_size > self.max_file_size:
                raise ValueError(f"Audio file too large: {file_size} bytes (max: {self.max_file_size})")
            
            # Convert to WAV format if needed
            wav_path = await self._convert_to_wav(audio_file_path)
            
            try:
                # Check duration
                duration = await self.get_audio_duration(wav_path)
                if duration > self.max_duration_seconds:
                    raise ValueError(f"Audio too long: {duration} seconds (max: {self.max_duration_seconds})")
                
                # Perform transcription
                with sr.AudioFile(wav_path) as source:
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    
                    # Record audio
                    audio_data = self.recognizer.record(source)
                
                # Try different recognition methods
                transcript = await self._transcribe_with_fallbacks(audio_data, language)
                
                logger.info(
                    "Audio transcription completed",
                    duration=duration,
                    transcript_length=len(transcript)
                )
                
                return transcript
                
            finally:
                # Clean up temporary WAV file
                if wav_path != audio_file_path and os.path.exists(wav_path):
                    os.unlink(wav_path)
                    
        except Exception as e:
            logger.error("Audio transcription failed", error=str(e), file_path=audio_file_path)
            raise
    
    async def _convert_to_wav(self, audio_file_path: str) -> str:
        """
        Convert audio file to WAV format for processing.
        """
        try:
            file_extension = os.path.splitext(audio_file_path)[1].lower()
            
            if file_extension == '.wav':
                return audio_file_path
            
            # Convert using pydub
            audio = AudioSegment.from_file(audio_file_path)
            
            # Create temporary WAV file
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_wav.close()
            
            # Export as WAV
            audio.export(temp_wav.name, format='wav', parameters=['-ar', '16000'])  # 16kHz sample rate
            
            logger.info("Audio converted to WAV", original=audio_file_path, wav_path=temp_wav.name)
            
            return temp_wav.name
            
        except Exception as e:
            logger.error("Audio conversion failed", error=str(e))
            raise ValueError(f"Failed to convert audio to WAV: {str(e)}")
    
    async def _transcribe_with_fallbacks(self, audio_data, language: Optional[str] = None) -> str:
        """
        Attempt transcription with multiple fallback methods.
        """
        # Try Google Speech Recognition first
        try:
            if language:
                transcript = self.recognizer.recognize_google(audio_data, language=language)
            else:
                transcript = self.recognizer.recognize_google(audio_data)
            
            if transcript.strip():
                return transcript
                
        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            logger.warning("Google Speech Recognition service error", error=str(e))
        
        # Try Sphinx (offline)
        try:
            transcript = self.recognizer.recognize_sphinx(audio_data)
            if transcript.strip():
                logger.info("Used Sphinx as fallback for transcription")
                return transcript
                
        except sr.UnknownValueError:
            logger.warning("Sphinx could not understand audio")
        except sr.RequestError as e:
            logger.warning("Sphinx error", error=str(e))
        
        # Return empty string if all methods fail
        logger.warning("All transcription methods failed")
        return ""
    
    async def get_audio_duration(self, audio_file_path: str) -> float:
        """
        Get duration of audio file in seconds.
        """
        try:
            audio = AudioSegment.from_file(audio_file_path)
            duration_seconds = len(audio) / 1000.0  # Convert milliseconds to seconds
            return duration_seconds
            
        except Exception as e:
            logger.error("Failed to get audio duration", error=str(e))
            return 0.0
    
    def is_supported_format(self, file_path: str) -> bool:
        """
        Check if audio format is supported.
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        return file_extension in self.supported_formats
    
    def get_supported_formats(self) -> list:
        """
        Get list of supported audio formats.
        """
        return self.supported_formats.copy()
    
    async def validate_audio_file(self, audio_file_path: str) -> dict:
        """
        Validate audio file and return metadata.
        """
        try:
            if not os.path.exists(audio_file_path):
                return {"valid": False, "error": "File not found"}
            
            if not self.is_supported_format(audio_file_path):
                return {
                    "valid": False,
                    "error": f"Unsupported format. Supported formats: {', '.join(self.supported_formats)}"
                }
            
            file_size = os.path.getsize(audio_file_path)
            if file_size > self.max_file_size:
                return {
                    "valid": False,
                    "error": f"File too large: {file_size} bytes (max: {self.max_file_size})"
                }
            
            # Get audio metadata
            duration = await self.get_audio_duration(audio_file_path)
            
            if duration > self.max_duration_seconds:
                return {
                    "valid": False,
                    "error": f"Audio too long: {duration} seconds (max: {self.max_duration_seconds})"
                }
            
            return {
                "valid": True,
                "duration_seconds": duration,
                "file_size_bytes": file_size,
                "format": os.path.splitext(audio_file_path)[1].lower()
            }
            
        except Exception as e:
            logger.error("Audio validation failed", error=str(e))
            return {"valid": False, "error": str(e)}
