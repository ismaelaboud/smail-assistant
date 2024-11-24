from TTS.trainer import Trainer
from TTS.config import load_config
from TTS.utils.audio import AudioProcessor

def train_voice_model(config_path, voice_data_path):
    # Load training configuration
    config = load_config(config_path)
    
    # Initialize audio processor
    ap = AudioProcessor(**config.audio)
    
    # Initialize trainer
    trainer = Trainer(
        config,
        output_path='custom_voice_model/',
        audio_processor=ap,
        data_path=voice_data_path
    )
    
    # Start training
    trainer.fit() 