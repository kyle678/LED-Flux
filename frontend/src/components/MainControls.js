import React from 'react';
import { styles } from '../styles';

export default function MainControls({ isOn, isPlaying, togglePower, togglePlayPause }) {
  return (
    <div>
      <button style={styles.button} onClick={togglePower}>
        {isOn ? 'Turn Off' : 'Turn On'}
      </button>
      <button style={styles.button} onClick={togglePlayPause}>
        {isPlaying ? 'Pause' : 'Play'}
      </button>
    </div>
  );
}