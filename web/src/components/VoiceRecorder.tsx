import { useEffect, useRef, useState } from "react";
import type { CapturedFile } from "../api/media";

const MIME_CANDIDATES = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];

function pickMime(): string | undefined {
  if (typeof MediaRecorder === "undefined" || typeof MediaRecorder.isTypeSupported !== "function") return undefined;
  return MIME_CANDIDATES.find((m) => MediaRecorder.isTypeSupported(m));
}

function extensionFor(mime: string): string {
  if (mime.includes("mp4")) return "m4a";
  if (mime.includes("ogg")) return "ogg";
  if (mime.includes("mpeg")) return "mp3";
  if (mime.includes("wav")) return "wav";
  return "webm";
}

function formatTime(total: number): string {
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

/** Records a voice note in the browser (or accepts an audio file) and lets the person play it back. */
export function VoiceRecorder({
  value,
  onChange,
}: {
  value: CapturedFile | undefined;
  onChange: (v: CapturedFile | null) => void;
}) {
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    if (!value) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(value.blob);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [value]);

  useEffect(() => {
    return () => {
      if (timerRef.current !== null) window.clearInterval(timerRef.current);
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  async function start() {
    setError(null);
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError("This browser cannot record audio. Choose an audio file instead.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mime = pickMime();
      const recorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e: BlobEvent) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        const type = (recorder.mimeType || mime || "audio/webm").split(";")[0];
        const blob = new Blob(chunksRef.current, { type });
        if (blob.size > 0) {
          onChange({ blob, filename: `voice-${Date.now()}.${extensionFor(type)}` });
        }
      };
      recorder.start();
      recorderRef.current = recorder;
      setSeconds(0);
      setRecording(true);
      timerRef.current = window.setInterval(() => setSeconds((s) => s + 1), 1000);
    } catch {
      setError("Microphone permission was denied, or no microphone was found.");
    }
  }

  function stop() {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    recorderRef.current?.stop();
    setRecording(false);
  }

  function handleFile(file: File | undefined) {
    if (!file) return;
    onChange({ blob: file, filename: file.name });
  }

  return (
    <div className="voice-box">
      {recording ? (
        <div className="voice-row">
          <span className="voice-dot" />
          <strong>Recording… {formatTime(seconds)}</strong>
          <button type="button" className="btn btn-danger" onClick={stop}>
            Stop
          </button>
        </div>
      ) : value && previewUrl ? (
        <div>
          <audio className="media-audio" controls preload="metadata" src={previewUrl} />
          <div className="voice-row">
            <button type="button" className="btn btn-secondary" onClick={start}>
              Record again
            </button>
            <button type="button" className="btn btn-icon" onClick={() => onChange(null)}>
              Remove
            </button>
          </div>
        </div>
      ) : (
        <div className="voice-row">
          <button type="button" className="btn btn-primary" onClick={start}>
            ● Start recording
          </button>
          <label className="voice-file">
            or choose an audio file
            <input type="file" accept="audio/*" onChange={(e) => handleFile(e.target.files?.[0])} />
          </label>
        </div>
      )}
      {error && <p className="q-error-text">{error}</p>}
    </div>
  );
}
