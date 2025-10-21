# Audio Sounds

Questa directory contiene i file audio per le notifiche sonore.

## File richiesti

- `order_filled_buy.wav` - Suono quando viene eseguito un ordine BUY
- `order_filled_sell.wav` - Suono quando viene eseguito un ordine SELL
- `alert.wav` - Suono per alert generici
- `success.wav` - Suono per operazioni riuscite
- `error.wav` - Suono per errori

## Come ottenere i file audio

### Opzione 1: Usa suoni di sistema

Su Linux/Mac:
```bash
# Copia suoni di sistema
cp /usr/share/sounds/freedesktop/stereo/message.oga order_filled_buy.wav
cp /usr/share/sounds/freedesktop/stereo/complete.oga order_filled_sell.wav
```

### Opzione 2: Genera con Python

```python
import numpy as np
from scipy.io import wavfile

def generate_beep(filename, frequency=440, duration=0.3):
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration))
    wave = np.sin(2 * np.pi * frequency * t)
    wave = (wave * 32767).astype(np.int16)
    wavfile.write(filename, sample_rate, wave)

# Genera suoni
generate_beep('order_filled_buy.wav', frequency=880, duration=0.2)   # La alto
generate_beep('order_filled_sell.wav', frequency=440, duration=0.2)  # La normale
generate_beep('alert.wav', frequency=1000, duration=0.5)             # Alert
```

### Opzione 3: Download online

Siti gratuiti:
- https://freesound.org/
- https://mixkit.co/free-sound-effects/
- https://soundbible.com/

Cerca: "notification", "beep", "ding"

## Test audio

```bash
python -c "
from notifications.audio_notifier import AudioNotifier
n = AudioNotifier()
n.play_buy_filled()
"
```

## Formato

- **Formato**: WAV (non compresso)
- **Sample rate**: 44100 Hz consigliato
- **Durata**: 0.2-1 secondo consigliato (breve)
- **Canali**: Mono o Stereo

## Disabilitare audio

In `config/settings.py`:
```python
AUDIO_CONFIG = {
    'enabled': False,  # ← Cambia a False
}
```
