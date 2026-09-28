import { useEffect, useState } from "react";
import "../styles/fill.css";
import { mediaApi } from "../api/media";

/**
 * Shows a stored answer file inside the Submission detail panel:
 * voice notes get a player, photos and signatures get an image.
 */
export function MediaAnswer({ reference }: { reference: string }) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [mime, setMime] = useState<string>("");
  const [status, setStatus] = useState<"loading" | "ready" | "missing" | "notUploaded">("loading");

  useEffect(() => {
    // Files that were captured on a phone but never uploaded only have a local path.
    if (!reference.startsWith("/api/media/")) {
      setStatus("notUploaded");
      return;
    }
    let cancelled = false;
    let created: string | null = null;
    setStatus("loading");
    mediaApi
      .fetchBlob(reference)
      .then((blob) => {
        if (cancelled) return;
        created = URL.createObjectURL(blob);
        setMime(blob.type || "");
        setObjectUrl(created);
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("missing");
      });
    return () => {
      cancelled = true;
      if (created) URL.revokeObjectURL(created);
    };
  }, [reference]);

  if (status === "loading") return <span className="media-note">Loading file…</span>;
  if (status === "notUploaded") {
    return <span className="media-note">File not uploaded yet (the phone has not finished syncing it).</span>;
  }
  if (status === "missing" || !objectUrl) {
    return <span className="media-note media-note-bad">File is missing from the server storage.</span>;
  }
  if (mime.startsWith("audio/") || mime.startsWith("video/")) {
    return <audio className="media-audio" controls preload="metadata" src={objectUrl} />;
  }
  if (mime.startsWith("image/")) {
    return (
      <a href={objectUrl} target="_blank" rel="noreferrer">
        <img className="media-image" src={objectUrl} alt="Captured answer" />
      </a>
    );
  }
  return (
    <a href={objectUrl} download>
      Download file
    </a>
  );
}
