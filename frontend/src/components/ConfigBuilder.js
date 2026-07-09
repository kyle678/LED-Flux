import React, { useState } from 'react';
import { styles } from '../styles';
import { hexToRgb, rgbToHex } from '../constants';

export default function ConfigBuilder({ 
  configList, 
  setConfigList, 
  configName, 
  setConfigName, 
  playConfig, 
  saveCurrentConfig,
  reloadCurrentConfig // --- NEW: Prop to trigger a database fetch from the parent ---
}) {
  // Animation Parameters
  const [builderType, setBuilderType] = useState('static');
  const [builderAnimName, setBuilderAnimName] = useState('new animation');
  const [builderPixels, setBuilderPixels] = useState(100);
  const [builderStart, setBuilderStart] = useState(0);
  const [builderBrightness, setBuilderBrightness] = useState(1.0);
  const [builderLoopDuration, setBuilderLoopDuration] = useState(5.0);
  const [builderTargetFps, setBuilderTargetFps] = useState(30);
  
  // Color Parameters
  const [builderColor, setBuilderColor] = useState('#ff6400'); 
  const [builderColorList, setBuilderColorList] = useState(['#ff6400', '#00ff64', '#6400ff']);
  
  const [editingAnimIndex, setEditingAnimIndex] = useState(null);
  const [clipboardHasItem, setClipboardHasItem] = useState(!!localStorage.getItem('led_anim_clipboard'));

  const checkOverlap = (newAnim, ignoreIndex = null) => {
    const newStart = newAnim.start_index;
    const newEnd = newStart + newAnim.num_pixels;

    return configList.some((existingAnim, idx) => {
      if (idx === ignoreIndex) return false; 
      
      const existingStart = existingAnim.start_index;
      const existingEnd = existingStart + existingAnim.num_pixels;
      
      return newStart < existingEnd && existingStart < newEnd;
    });
  };

  const handleColorListChange = (index, newColor) => {
    const newList = [...builderColorList];
    newList[index] = newColor;
    setBuilderColorList(newList);
  };
  
  const addColorToList = () => {
    setBuilderColorList([...builderColorList, '#ffffff']);
  };

  const removeColorFromList = (indexToRemove) => {
    setBuilderColorList(builderColorList.filter((_, index) => index !== indexToRemove));
  };

  const addOrUpdateAnimation = () => {
    const newAnim = {
      animation_type: builderType,
      name: builderAnimName,
      num_pixels: parseInt(builderPixels, 10),
      start_index: parseInt(builderStart, 10),
      brightness: parseFloat(builderBrightness),
      loop_duration: parseFloat(builderLoopDuration),
      target_fps: parseInt(builderTargetFps, 10),
      hide: false
    };
    
    if (builderType === 'static') {
      newAnim.colors = [hexToRgb(builderColor)]
    } else if (builderType === 'rotating') {
      newAnim.colors = builderColorList.map(hex => hexToRgb(hex));
    }

    const hasCollision = checkOverlap(newAnim, editingAnimIndex);
    if (hasCollision) {
      const proceed = window.confirm("Warning: This animation overlaps with another one already in your scene. Add it anyway?");
      if (!proceed) return; 
    }

    if (editingAnimIndex !== null) {
      newAnim.hide = configList[editingAnimIndex].hide || false; 
      
      const updatedList = [...configList];
      updatedList[editingAnimIndex] = newAnim;
      setConfigList(updatedList);
      setEditingAnimIndex(null); 
    } else {
      setConfigList([...configList, newAnim]);
    }
  };

  const loadAnimForEditing = (index) => {
    const anim = configList[index];
    
    setBuilderType(anim.animation_type || 'static');
    setBuilderAnimName(anim.name || 'new animation');
    setBuilderPixels(anim.num_pixels || 10);
    setBuilderStart(anim.start_index || 0);
    setBuilderBrightness(anim.brightness !== undefined ? anim.brightness : 1.0);
    setBuilderLoopDuration(anim.loop_duration || 5.0);
    setBuilderTargetFps(anim.target_fps || 30);
    
    if (anim.animation_type === 'static' && anim.colors) {
      setBuilderColor(rgbToHex(anim.colors[0][0], anim.colors[0][1], anim.colors[0][2]));
    } else if (anim.animation_type === 'rotating' && anim.colors) {
      setBuilderColorList(anim.colors.map(c => rgbToHex(c[0], c[1], c[2])));
    }
    
    setEditingAnimIndex(index);
  };

  const cancelEdit = () => setEditingAnimIndex(null);

  const removeFromConfig = (indexToRemove) => {
    setConfigList(configList.filter((_, index) => index !== indexToRemove));
    if (editingAnimIndex === indexToRemove) setEditingAnimIndex(null);
  };

  const toggleHide = (index) => {
    const updatedList = [...configList];
    updatedList[index].hide = !updatedList[index].hide;
    setConfigList(updatedList);
  };

  const copyAnimation = (anim) => {
    localStorage.setItem('led_anim_clipboard', JSON.stringify(anim));
    setClipboardHasItem(true);
  };

  const pasteAnimation = () => {
    const savedAnim = localStorage.getItem('led_anim_clipboard');
    if (savedAnim) {
      try {
        const parsedAnim = JSON.parse(savedAnim);
        
        const hasCollision = checkOverlap(parsedAnim);
        if (hasCollision) {
          const proceed = window.confirm("Warning: The pasted animation overlaps with another one already in your scene. Paste it anyway?");
          if (!proceed) return;
        }

        parsedAnim.name = `${parsedAnim.name} (Copy)`;
        setConfigList([...configList, parsedAnim]);
      } catch (e) {
        console.error('Failed to parse clipboard data', e);
      }
    }
  };

  const moveUp = (index) => {
    if (index === 0 || editingAnimIndex !== null) return;
    const newList = [...configList];
    [newList[index - 1], newList[index]] = [newList[index], newList[index - 1]];
    setConfigList(newList);
  };

  const moveDown = (index) => {
    if (index === configList.length - 1 || editingAnimIndex !== null) return;
    const newList = [...configList];
    [newList[index + 1], newList[index]] = [newList[index], newList[index + 1]];
    setConfigList(newList);
  };

  const clearScene = () => {
    const proceed = window.confirm("Are you sure you want to clear all staged animations? This cannot be undone.");
    if (proceed) {
      setConfigList([]);
      setConfigName(''); 
      setEditingAnimIndex(null);
    }
  };

  // --- NEW: Revert to Saved Function ---
  const handleRevert = () => {
    if (!configName) return; // Shouldn't happen if button is conditionally rendered, but safe to check
    const proceed = window.confirm(`Are you sure you want to discard unsaved changes and reload "${configName}"?`);
    if (proceed && reloadCurrentConfig) {
      reloadCurrentConfig(configName);
      setEditingAnimIndex(null);
    }
  };

  return (
    <div style={{...styles.section, backgroundColor: '#222'}}>
      <h3 style={{ marginTop: '0', fontSize: '16px', color: '#fff' }}>Build Custom Scene</h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px' }}>
        
        <div style={styles.inputGroup}>
          <label>Type</label>
          <select style={styles.input} value={builderType} onChange={(e) => setBuilderType(e.target.value)}>
            <option value="static">Static</option>
            <option value="rotating">Rotating</option>
          </select>
        </div>

        <div style={styles.inputGroup}>
          <label>Anim Name</label>
          <input type="text" style={styles.input} value={builderAnimName} onChange={(e) => setBuilderAnimName(e.target.value)} />
        </div>

        <div style={styles.inputGroup}>
          <label>Pixels</label>
          <input type="number" style={styles.input} value={builderPixels} onChange={(e) => setBuilderPixels(e.target.value)} />
        </div>

        <div style={styles.inputGroup}>
          <label>Start Index</label>
          <input type="number" style={styles.input} value={builderStart} onChange={(e) => setBuilderStart(e.target.value)} />
        </div>

        <div style={styles.inputGroup}>
          <label>Brightness (0.0 - 1.0)</label>
          <input type="number" step="0.1" min="0" max="1" style={styles.input} value={builderBrightness} onChange={(e) => setBuilderBrightness(e.target.value)} />
        </div>

        <div style={styles.inputGroup}>
          <label>Loop Duration (s)</label>
          <input type="number" step="0.5" min="0" style={styles.input} value={builderLoopDuration} onChange={(e) => setBuilderLoopDuration(e.target.value)} />
        </div>

        <div style={styles.inputGroup}>
          <label>Target FPS</label>
          <input type="number" style={styles.input} value={builderTargetFps} onChange={(e) => setBuilderTargetFps(e.target.value)} />
        </div>
        
        {builderType === 'static' && (
          <div style={styles.inputGroup}>
            <label>Color</label>
            <input type="color" style={{...styles.input, height: '34px', padding: '2px', cursor: 'pointer'}} value={builderColor} onChange={(e) => setBuilderColor(e.target.value)} />
          </div>
        )}
      </div>

      {builderType === 'rotating' && (
        <div style={{...styles.inputGroup, marginTop: '10px'}}>
          <label>Colors</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '4px' }}>
            {builderColorList.map((color, index) => (
              <div key={index} style={{ display: 'flex', alignItems: 'center', backgroundColor: '#333', padding: '2px', borderRadius: '4px' }}>
                <input 
                  type="color" 
                  style={{ width: '30px', height: '30px', padding: '0', border: 'none', cursor: 'pointer', background: 'none' }} 
                  value={color} 
                  onChange={(e) => handleColorListChange(index, e.target.value)} 
                />
                {builderColorList.length > 1 && (
                  <button 
                    style={{ background: 'none', border: 'none', color: '#dc3545', cursor: 'pointer', padding: '0 4px', fontWeight: 'bold' }} 
                    onClick={() => removeColorFromList(index)}
                    title="Remove Color"
                  >
                    X
                  </button>
                )}
              </div>
            ))}
            <button 
              style={{...styles.button, backgroundColor: '#444', color: '#fff', margin: '0', padding: '4px 10px', fontSize: '12px'}} 
              onClick={addColorToList}
            >
              + Add Color
            </button>
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
        <button 
          style={{...styles.button, flex: 1, backgroundColor: editingAnimIndex !== null ? '#ffc107' : '#0dcaf0', color: '#000', fontWeight: 'bold', margin: 0}} 
          onClick={addOrUpdateAnimation}
        >
          {editingAnimIndex !== null ? '✓ Update Animation' : '+ Add to Scene'}
        </button>
        
        {clipboardHasItem && editingAnimIndex === null && (
          <button 
            style={{...styles.button, backgroundColor: '#20c997', color: '#000', fontWeight: 'bold', margin: 0}} 
            onClick={pasteAnimation}
          >
            📋 Paste
          </button>
        )}

        {editingAnimIndex !== null && (
          <button style={{...styles.button, backgroundColor: '#6c757d', margin: 0}} onClick={cancelEdit}>Cancel</button>
        )}
      </div>

      {configList.length > 0 && (
        <div style={{ marginTop: '15px', backgroundColor: '#1a1a1a', padding: '10px', borderRadius: '6px', border: '1px solid #333' }}>
          <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#fff' }}>
            {configName ? `Editing: ${configName}` : 'Staged Animations:'}
          </h4>
          {configList.map((anim, index) => (
            <div key={index} style={{...styles.listItem, backgroundColor: editingAnimIndex === index ? '#333' : 'transparent'}}>
              
              <span style={{ color: anim.hide ? '#666' : '#ddd', flex: 1, textDecoration: anim.hide ? 'line-through' : 'none' }}>
                <strong style={{ color: anim.hide ? '#888' : '#fff' }}>{anim.name}</strong> ({anim.animation_type} | {anim.num_pixels}px @ idx {anim.start_index})
              </span>
              
              <div style={{ display: 'flex' }}>
                <button 
                  onClick={() => toggleHide(index)} 
                  style={{...styles.button, backgroundColor: anim.hide ? '#495057' : '#17a2b8', padding: '4px 8px', margin: '0 5px 0 0'}} 
                  title={anim.hide ? "Show Animation" : "Hide Animation"}
                >
                  {anim.hide ? '🙈' : '👁️'}
                </button>

                <button 
                  onClick={() => moveUp(index)} 
                  disabled={index === 0 || editingAnimIndex !== null}
                  style={{...styles.button, backgroundColor: '#495057', padding: '4px 8px', margin: '0 5px 0 0', opacity: (index === 0 || editingAnimIndex !== null) ? 0.3 : 1}} 
                  title="Move Up"
                >
                  ↑
                </button>
                <button 
                  onClick={() => moveDown(index)} 
                  disabled={index === configList.length - 1 || editingAnimIndex !== null}
                  style={{...styles.button, backgroundColor: '#495057', padding: '4px 8px', margin: '0 10px 0 0', opacity: (index === configList.length - 1 || editingAnimIndex !== null) ? 0.3 : 1}} 
                  title="Move Down"
                >
                  ↓
                </button>

                <button onClick={() => copyAnimation(anim)} style={{...styles.button, backgroundColor: '#6f42c1', padding: '4px 8px', margin: '0 5px 0 0'}} title="Copy">📄</button>
                <button onClick={() => loadAnimForEditing(index)} style={{...styles.button, backgroundColor: '#0d6efd', padding: '4px 8px', margin: '0 5px 0 0'}} title="Edit">✏️</button>
                <button onClick={() => removeFromConfig(index)} style={{...styles.button, backgroundColor: '#dc3545', padding: '4px 8px', margin: '0'}} title="Delete">X</button>
              </div>
            </div>
          ))}
          
          {/* --- NEW: Revert Button added to action row --- */}
          <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
            <button style={{...styles.actionButton, flex: 1, backgroundColor: '#198754', margin: 0}} onClick={() => playConfig({ name: "unsaved-test", animations: configList })}>
              ▶️ Test Current Scene
            </button>
            
            {reloadCurrentConfig && configName && (
              <button 
                style={{...styles.actionButton, width: 'auto', padding: '0 15px', backgroundColor: '#fd7e14', margin: 0}} 
                onClick={handleRevert} 
                title="Revert to saved version in database"
              >
                🔄 Revert
              </button>
            )}

            <button style={{...styles.actionButton, width: 'auto', padding: '0 15px', backgroundColor: '#dc3545', margin: 0}} onClick={clearScene} title="Clear all staged animations">
              🗑️ Clear
            </button>
          </div>

          <div style={{...styles.inputGroup, marginTop: '15px', borderTop: '1px solid #444', paddingTop: '15px'}}>
            <label><strong style={{ color: '#fff' }}>Save to Database</strong></label>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input type="text" placeholder="e.g., 'Party Mode'" style={{...styles.input, flex: 1}} value={configName} onChange={(e) => setConfigName(e.target.value)} />
              <button style={{...styles.button, backgroundColor: '#6f42c1', margin: 0, marginTop: '4px'}} onClick={saveCurrentConfig}>
                💾 Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}