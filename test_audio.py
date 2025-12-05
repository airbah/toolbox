"""
Test script to verify audio capture is working correctly.
Run this while playing some audio (music, video, etc.) to test.
"""
import time
import os

def test_audio():
    print("=== Test de capture audio ===\n")
    
    # Test 1: Check if pyaudiowpatch is installed
    print("1. Vérification de pyaudiowpatch...")
    try:
        import pyaudiowpatch as pyaudio
        print("   [OK] pyaudiowpatch est installe")
    except ImportError:
        print("   [ERREUR] pyaudiowpatch n'est pas installe!")
        print("   Exécutez: pip install pyaudiowpatch")
        return
    
    # Test 2: Find loopback device
    print("\n2. Recherche du périphérique audio loopback...")
    p = pyaudio.PyAudio()
    
    try:
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        print(f"   WASAPI API trouvée: index {wasapi_info['index']}")
        
        default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        print(f"   Haut-parleurs par défaut: {default_speakers['name']}")
        print(f"   Sample rate: {int(default_speakers['defaultSampleRate'])} Hz")
        
        # Find loopback device
        loopback_device = None
        print("\n   Périphériques loopback disponibles:")
        for loopback in p.get_loopback_device_info_generator():
            print(f"   - {loopback['name']}")
            if default_speakers["name"] in loopback["name"]:
                loopback_device = loopback
                print(f"     ^ Correspondance trouvée!")
        
        if not loopback_device:
            print("   [ERREUR] Aucun peripherique loopback trouve!")
            p.terminate()
            return
        
        print(f"\n   [OK] Peripherique loopback selectionne: {loopback_device['name']}")
        
    except Exception as e:
        print(f"   [ERREUR] {e}")
        p.terminate()
        return
    
    # Test 3: Record a few seconds of audio
    print("\n3. Enregistrement de 5 secondes d'audio...")
    print("   *** Jouez de la musique ou une vidéo maintenant! ***")
    
    try:
        sample_rate = int(loopback_device["defaultSampleRate"])
        channels = int(loopback_device["maxInputChannels"])
        frames_per_buffer = int(sample_rate * 0.02)
        
        stream = p.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=sample_rate,
            frames_per_buffer=frames_per_buffer,
            input=True,
            input_device_index=loopback_device["index"],
        )
        
        frames = []
        for i in range(int(sample_rate / frames_per_buffer * 5)):  # 5 seconds
            data = stream.read(frames_per_buffer, exception_on_overflow=False)
            frames.append(data)
            if i % 50 == 0:
                print(f"   Enregistrement... {i * frames_per_buffer / sample_rate:.1f}s")
        
        stream.stop_stream()
        stream.close()
        
        audio_data = b''.join(frames)
        print(f"\n   [OK] Audio capture: {len(audio_data)} bytes")
        
        # Check if audio has any actual sound (not just silence)
        import struct
        samples = struct.unpack(f'{len(audio_data)//2}h', audio_data)
        max_amplitude = max(abs(s) for s in samples)
        avg_amplitude = sum(abs(s) for s in samples) / len(samples)
        
        print(f"   Amplitude max: {max_amplitude} / 32767")
        print(f"   Amplitude moyenne: {avg_amplitude:.1f}")
        
        if max_amplitude < 100:
            print("\n   [ATTENTION] L'audio semble etre silencieux!")
            print("   Verifiez que:")
            print("   - Une source audio est en cours de lecture")
            print("   - Le volume n'est pas a zero")
            print("   - Les haut-parleurs/casque sont le peripherique par defaut")
        else:
            print("\n   [OK] Audio detecte avec du son!")
        
    except Exception as e:
        print(f"   [ERREUR] Erreur d'enregistrement: {e}")
        p.terminate()
        return
    
    # Test 4: Save to WAV file
    print("\n4. Sauvegarde en fichier WAV de test...")
    import wave
    test_file = os.path.join(os.path.expanduser("~"), "test_audio.wav")
    
    try:
        with wave.open(test_file, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)
        
        file_size = os.path.getsize(test_file)
        print(f"   [OK] Fichier sauvegarde: {test_file}")
        print(f"   Taille: {file_size} bytes")
        print(f"\n   Écoutez ce fichier pour vérifier que l'audio est correct!")
        
    except Exception as e:
        print(f"   [ERREUR] Erreur de sauvegarde: {e}")
    
    p.terminate()
    print("\n=== Test terminé ===")

if __name__ == "__main__":
    test_audio()

