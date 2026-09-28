import { useEffect, useState } from "react";
import type { CapturedFile } from "../api/media";

/** Takes a photo with the phone camera (or picks an image on a computer). */
export function PhotoCapture({
  value,
  onChange,
}: {
  value: CapturedFile | undefined;
  onChange: (v: CapturedFile | null) => void;
}) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!value) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(value.blob);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [value]);

  return (
    <div className="voice-box">
      {value && previewUrl ? <img className="media-image" src={previewUrl} alt="Captured" /> : null}
      <div className="voice-row">
        <label className="btn btn-primary photo-button">
          {value ? "Retake / choose another" : "📷 Take or choose photo"}
          <input
            type="file"
            accept="image/*"
            capture="environment"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) onChange({ blob: file, filename: file.name });
              e.target.value = "";
            }}
          />
        </label>
        {value && (
          <button type="button" className="btn btn-icon" onClick={() => onChange(null)}>
            Remove
          </button>
        )}
      </div>
    </div>
  );
}
