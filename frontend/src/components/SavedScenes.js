import React from 'react';
import { styles } from '../styles';

export default function SavedScenes({ savedConfigs, playConfig, loadConfigForEditing, deleteSavedConfig }) {
  if (savedConfigs.length === 0) return null;

  return (
    <div style={{...styles.section, backgroundColor: '#252525'}}>
      <h3 style={{ marginTop: '0', fontSize: '16px', color: '#fff' }}>Saved Scenes</h3>
      <div style={{ display: 'flex', flexWrap: 'wrap' }}>
        {savedConfigs.map((config, index) => (
          <div key={index} style={{ display: 'flex', margin: '5px', borderRadius: '8px', overflow: 'hidden' }}>
            <button style={styles.savedButtonPlay} onClick={() => playConfig(config)} title={`Play ${config.name}`}>
              Play {config.name}
            </button>
            <button style={styles.savedButtonEdit} onClick={() => loadConfigForEditing(config)} title="Edit Scene">
              Edit
            </button>
            <button style={styles.savedButtonDelete} onClick={() => deleteSavedConfig(config.name)} title="Delete Scene">
              Delete
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}