import { useEffect, useRef } from "react";
import type { CapturedFile } from "../api/media";

const WIDTH = 720;
const HEIGHT = 240;

function paintWhite(canvas: HTMLCanvasElement) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
}

/** Draw-your-signature pad. The picture is captured automatically after every stroke. */
export function SignatureCanvas({
  value,
  onChange,
}: {
  value: CapturedFile | undefined;
  onChange: (v: CapturedFile | null) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const drawingRef = useRef(false);

  useEffect(() => {
    if (canvasRef.current) paintWhite(canvasRef.current);
  }, []);

  function pointFor(e: React.PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    return {
      x: ((e.clientX - rect.left) * canvas.width) / rect.width,
      y: ((e.clientY - rect.top) * canvas.height) / rect.height,
    };
  }

  function down(e: React.PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    canvas.setPointerCapture(e.pointerId);
    drawingRef.current = true;
    const p = pointFor(e);
    ctx.lineWidth = 3;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#16212b";
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
  }

  function move(e: React.PointerEvent<HTMLCanvasElement>) {
    if (!drawingRef.current) return;
    const ctx = canvasRef.current?.getContext("2d");
    if (!ctx) return;
    const p = pointFor(e);
    ctx.lineTo(p.x, p.y);
    ctx.stroke();
  }

  function up() {
    if (!drawingRef.current) return;
    drawingRef.current = false;
    canvasRef.current?.toBlob((blob) => {
      if (blob) onChange({ blob, filename: `signature-${Date.now()}.png` });
    }, "image/png");
  }

  function clear() {
    if (canvasRef.current) paintWhite(canvasRef.current);
    onChange(null);
  }

  return (
    <div>
      <canvas
        ref={canvasRef}
        className="signature-canvas"
        width={WIDTH}
        height={HEIGHT}
        onPointerDown={down}
        onPointerMove={move}
        onPointerUp={up}
        onPointerCancel={up}
      />
      <div className="voice-row">
        <span className="media-note">{value ? "Signature captured ✓" : "Sign above with your finger or mouse."}</span>
        <button type="button" className="btn btn-icon" onClick={clear}>
          Clear
        </button>
      </div>
    </div>
  );
}
