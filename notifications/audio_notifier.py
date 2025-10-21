"""
Audio Notifier

Riproduce segnali sonori per eventi di trading
"""

import pygame
from pathlib import Path
from loguru import logger


class AudioNotifier:
    """
    Notifiche audio per eventi di trading
    """

    def __init__(self, sounds_dir='sounds/', volume=0.7):
        """
        Args:
            sounds_dir: Directory contenente file audio
            volume: Volume audio (0.0 - 1.0)
        """
        self.sounds_dir = Path(sounds_dir)
        self.volume = volume

        # Inizializza pygame mixer
        try:
            pygame.mixer.init()
            logger.info("Audio Notifier inizializzato")
        except Exception as e:
            logger.error(f"Errore inizializzazione audio: {e}")
            self.enabled = False
            return

        self.enabled = True

        # Carica suoni
        self.sounds = {}
        self._load_sounds()

    def _load_sounds(self):
        """Carica file audio in memoria"""
        sound_files = {
            'buy': 'order_filled_buy.wav',
            'sell': 'order_filled_sell.wav',
            'alert': 'alert.wav',
            'success': 'success.wav',
            'error': 'error.wav',
        }

        for name, filename in sound_files.items():
            filepath = self.sounds_dir / filename

            if filepath.exists():
                try:
                    sound = pygame.mixer.Sound(str(filepath))
                    sound.set_volume(self.volume)
                    self.sounds[name] = sound
                    logger.debug(f"Caricato suono: {name}")
                except Exception as e:
                    logger.warning(f"Errore caricamento {filename}: {e}")
            else:
                logger.warning(f"File audio non trovato: {filepath}")

    def play(self, sound_name):
        """
        Riproduci un suono

        Args:
            sound_name: Nome del suono ('buy', 'sell', 'alert', etc.)
        """
        if not self.enabled:
            return

        if sound_name in self.sounds:
            self.sounds[sound_name].play()
            logger.debug(f"Riprodotto suono: {sound_name}")
        else:
            logger.warning(f"Suono non trovato: {sound_name}")

    # Metodi di convenienza

    def play_buy_filled(self):
        """Suono per ordine BUY eseguito"""
        self.play('buy')

    def play_sell_filled(self):
        """Suono per ordine SELL eseguito"""
        self.play('sell')

    def play_alert(self):
        """Suono per alert generico"""
        self.play('alert')

    def play_success(self):
        """Suono per operazione riuscita"""
        self.play('success')

    def play_error(self):
        """Suono per errore"""
        self.play('error')

    def set_volume(self, volume):
        """
        Imposta volume audio

        Args:
            volume: Volume (0.0 - 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))

        for sound in self.sounds.values():
            sound.set_volume(self.volume)

        logger.info(f"Volume impostato a {self.volume}")

    def stop_all(self):
        """Ferma tutti i suoni in riproduzione"""
        pygame.mixer.stop()


# ============================================================================
# ESEMPIO DI UTILIZZO
# ============================================================================

if __name__ == '__main__':
    import time

    notifier = AudioNotifier()

    print("Test audio notifier...")

    print("Buy filled...")
    notifier.play_buy_filled()
    time.sleep(2)

    print("Sell filled...")
    notifier.play_sell_filled()
    time.sleep(2)

    print("Alert...")
    notifier.play_alert()
