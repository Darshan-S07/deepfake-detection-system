 // audioWorkletProcessor.js
class DeepfakeAudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._buf = [];
    this._bufLimit = 16000 * 0.5; // 0.5s at 16kHz
  }

  process(inputs /*, outputs, parameters */) {
    try {
      if (inputs && inputs[0] && inputs[0][0]) {
        const ch = inputs[0][0];
        for (let i = 0; i < ch.length; i++) this._buf.push(ch[i]);
        if (this._buf.length >= this._bufLimit) {
          const chunk = new Float32Array(this._buf);
          this._buf = [];
          // post structured clone
          this.port.postMessage({ type: 'AUDIO_CHUNK', pcm: chunk });
        }
      }
    } catch (e) {
      // avoid crashing
    }
    return true;
  }
}

registerProcessor('deepfake-audio-processor', DeepfakeAudioProcessor);
