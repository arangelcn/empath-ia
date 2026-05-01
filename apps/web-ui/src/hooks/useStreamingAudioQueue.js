import { useCallback, useEffect, useRef, useState } from 'react';

const base64ToArrayBuffer = (base64) => {
  const binary = window.atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
};

const pcm16ToFloat32 = (arrayBuffer) => {
  const input = new Int16Array(arrayBuffer);
  const output = new Float32Array(input.length);
  for (let i = 0; i < input.length; i += 1) {
    output[i] = Math.max(-1, Math.min(1, input[i] / 32768));
  }
  return output;
};

export const useStreamingAudioQueue = () => {
  const [isStreamingPlaying, setIsStreamingPlaying] = useState(false);
  const audioContextRef = useRef(null);
  const nextStartTimeRef = useRef(0);
  const activeSourcesRef = useRef(new Set());

  const getAudioContext = useCallback(async (sampleRate) => {
    if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      audioContextRef.current = new AudioContextClass({ sampleRate });
      nextStartTimeRef.current = audioContextRef.current.currentTime;
    }

    if (audioContextRef.current.state === 'suspended') {
      await audioContextRef.current.resume();
    }

    return audioContextRef.current;
  }, []);

  const enqueueAudioChunk = useCallback(async ({ audio, sample_rate_hz: sampleRate = 24000, encoding = 'PCM' }) => {
    if (!audio || encoding !== 'PCM') return;

    const context = await getAudioContext(sampleRate);
    const floatData = pcm16ToFloat32(base64ToArrayBuffer(audio));
    const audioBuffer = context.createBuffer(1, floatData.length, sampleRate);
    audioBuffer.copyToChannel(floatData, 0);

    const source = context.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(context.destination);

    const startAt = Math.max(context.currentTime + 0.02, nextStartTimeRef.current);
    source.start(startAt);
    nextStartTimeRef.current = startAt + audioBuffer.duration;
    activeSourcesRef.current.add(source);
    setIsStreamingPlaying(true);

    source.onended = () => {
      activeSourcesRef.current.delete(source);
      if (activeSourcesRef.current.size === 0) {
        setIsStreamingPlaying(false);
      }
    };
  }, [getAudioContext]);

  const stopStreamingAudio = useCallback(() => {
    activeSourcesRef.current.forEach((source) => {
      try {
        source.stop();
      } catch {
        // Source may already have ended.
      }
    });
    activeSourcesRef.current.clear();
    setIsStreamingPlaying(false);
    if (audioContextRef.current) {
      nextStartTimeRef.current = audioContextRef.current.currentTime;
    }
  }, []);

  useEffect(() => {
    return () => {
      stopStreamingAudio();
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
    };
  }, [stopStreamingAudio]);

  return {
    enqueueAudioChunk,
    stopStreamingAudio,
    isStreamingPlaying,
  };
};
