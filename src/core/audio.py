import pygame
import numpy as np

class AudioManager:
    def __init__(self):
        self.sample_rate = 44100
        
        # Pre-synthesize the sound buffers so there is zero latency during gameplay
        self.snd_star = self._create_sound(freq=880.0, duration=0.1, wave_type='sine', release=0.08)
        self.snd_mark = self._create_sound(freq=150.0, duration=0.05, wave_type='square', release=0.04, vol=0.2)
        
        # A fast, sweeping C Major arpeggio (C5, E5, G5, C6) for the win state
        self.snd_win = self._generate_arpeggio([523.25, 659.25, 783.99, 1046.50], step_duration=0.12)

    def _create_sound(self, freq: float, duration: float, wave_type='sine', release=0.1, vol=0.5):
        # 1. Generate discrete time array
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # 2. Generate raw oscillator waveform
        if wave_type == 'sine':
            wave = np.sin(2 * np.pi * freq * t)
        elif wave_type == 'square':
            wave = np.sign(np.sin(2 * np.pi * freq * t))
        else:
            wave = np.sin(2 * np.pi * freq * t)
            
        # 3. Apply ADSR Envelope (10ms Attack to prevent clicking, dynamic Release)
        attack_samples = int(self.sample_rate * 0.01)
        release_samples = int(self.sample_rate * release)
        
        envelope = np.ones_like(t)
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        if release_samples > 0:
            envelope[-release_samples:] = np.linspace(1, 0, release_samples)
            
        wave = wave * envelope * vol
        
        # 4. Convert to 16-bit PCM stereo (Pygame's expected buffer format)
        audio_array = np.int16(wave * 32767)
        stereo_array = np.column_stack((audio_array, audio_array))
        
        try:
            return pygame.sndarray.make_sound(stereo_array)
        except pygame.error:
            return None

    def _generate_arpeggio(self, frequencies: list, step_duration: float):
        """Synthesizes a sequence of notes into one continuous buffer."""
        arrays = []
        for freq in frequencies:
            t = np.linspace(0, step_duration, int(self.sample_rate * step_duration), False)
            wave = np.sin(2 * np.pi * freq * t)
            
            envelope = np.ones_like(t)
            attack = int(self.sample_rate * 0.01)
            decay = int(self.sample_rate * (step_duration - 0.01))
            envelope[:attack] = np.linspace(0, 1, attack)
            envelope[-decay:] = np.linspace(1, 0, decay)
            
            arrays.append(wave * envelope * 0.4)
            
        full_wave = np.concatenate(arrays)
        audio_array = np.int16(full_wave * 32767)
        stereo_array = np.column_stack((audio_array, audio_array))
        try:
            return pygame.sndarray.make_sound(stereo_array)
        except pygame.error:
            return None

    def play_star(self):
        if self.snd_star: self.snd_star.play()
        
    def play_mark(self):
        if self.snd_mark: self.snd_mark.play()
        
    def play_win(self):
        if self.snd_win: self.snd_win.play()