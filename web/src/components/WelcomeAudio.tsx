import { useEffect, useRef, useState } from "react";

const WELCOME_KEY = "kbs_play_welcome";

export function markWelcomeAudioForNextVisit() {
  sessionStorage.setItem(WELCOME_KEY, "true");
}

export function WelcomeAudio() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [showPlayButton, setShowPlayButton] = useState(false);

  useEffect(() => {
    const shouldPlay = sessionStorage.getItem(WELCOME_KEY) === "true";

    if (!shouldPlay) {
      return;
    }

    sessionStorage.removeItem(WELCOME_KEY);

    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    audio.volume = 1;

    audio
      .play()
      .then(() => {
        setShowPlayButton(false);
      })
      .catch(() => {
        setShowPlayButton(true);
      });
  }, []);

  function playWelcome() {
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    audio.currentTime = 0;
    audio.play().then(() => {
      setShowPlayButton(false);
    }).catch(() => {
      setShowPlayButton(true);
    });
  }

  return (
    <>
      <audio
        ref={audioRef}
        src="/welcome.mp3"
        preload="auto"
        onEnded={() => setShowPlayButton(false)}
      />

      {showPlayButton && (
        <button
          type="button"
          onClick={playWelcome}
          className="btn btn-primary"
          style={{
            position: "fixed",
            right: 20,
            bottom: 20,
            zIndex: 9999,
            borderRadius: 999,
          }}
        >
          🔊 Tap to hear welcome
        </button>
      )}
    </>
  );
}
