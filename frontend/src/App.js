import React, { useState, useEffect, useRef } from 'react';
import { API_BASE, ANIMATION_PRESETS } from './constants';
import { styles } from './styles';

import MainControls from './components/MainControls';
import BrightnessSlider from './components/BrightnessSlider';
import QuickPresets from './components/QuickPresets';
import SavedScenes from './components/SavedScenes';
import ConfigBuilder from './components/ConfigBuilder';

export default function App() {
  const [brightness, setBrightness] = useState(100);
  const [isOn, setIsOn] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  
  const [configList, setConfigList] = useState([]);
  const [configName, setConfigName] = useState('');
  const [savedConfigs, setSavedConfigs] = useState([]);
  
  const debounceTimer = useRef(null);

  const fetchSavedConfigs = async () => {
    try {
      const response = await fetch(`${API_BASE}/configs`);
      const data = await response.json();
      if (data.status === 'success') setSavedConfigs(data.data); 
    } catch (error) { console.error("Could not fetch saved configs:", error); }
  };

  useEffect(() => {
    document.body.style.backgroundColor = '#000000';
    document.body.style.color = '#e0e0e0';

    const fetchStatus = async () => {
      try {
        const response = await fetch(`${API_BASE}/status`);
        const data = await response.json();
        if (data.status === 'success') {
          setBrightness(data.data.brightness * 100 || 100);
          setIsOn(data.data.power || false);
          setIsPlaying(data.data.current_animation !== 'none'); 
        }
      } catch (error) { console.error("Could not reach LED API:", error); }
    };

    fetchStatus();
    fetchSavedConfigs();
  }, []);

  const handleBrightnessChange = (e) => {
    const newLevel = parseInt(e.target.value, 10);
    setBrightness(newLevel); 
    if (debounceTimer.current) clearTimeout(debounceTimer.current);

    debounceTimer.current = setTimeout(async () => {
      try {
        await fetch(`${API_BASE}/brightness`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: "brightness", data: { value: newLevel / 100 } })
        });
      } catch (error) { console.error("Error setting brightness:", error); }
    }, 50); 
  };

  const togglePlayPause = async () => {
    const newState = !isPlaying;
    setIsPlaying(newState);
    await fetch(`${API_BASE}/pause`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: "pause", data: { "value": newState ? "on" : "off" } })
    });
  };

  const togglePower = async () => {
    const newState = !isOn;
    setIsOn(newState);
    await fetch(`${API_BASE}/power`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: "power", data: { value: newState ? "on" : "off" } })
    });
  };

  const triggerPreset = async (presetKey) => {
    const presetData = ANIMATION_PRESETS[presetKey];
    if (!presetData) return;
    try {
      await fetch(`${API_BASE}/config`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: "config", data: presetData })
      });
      setIsOn(true); setIsPlaying(true);
    } catch (error) { console.error(`Error setting preset:`, error); }
  };

  const playConfig = async (configData) => {
    try {
      await fetch(`${API_BASE}/config`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: "config", data: configData })
      });
      setIsOn(true); setIsPlaying(true);
    } catch (error) { console.error(`Error sending config:`, error); }
  };

  const loadConfigForEditing = (config) => {
    setConfigName(config.name);
    setConfigList([...config.animations]); 
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
  };

const deleteSavedConfig = async (name) => {
    if (!window.confirm(`Are you sure you want to delete '${name}'?`)) return;
    try {
      const response = await fetch(`${API_BASE}/configs/${encodeURIComponent(name)}`, { method: 'DELETE' });
      
      // Check if the network request was successful before trying to parse JSON
      if (response.ok) {
        fetchSavedConfigs(); 
      } else {
        const text = await response.text();
        console.error("Failed to delete. Server said:", text);
      }
    } catch (error) { console.error("Error deleting config:", error); }
  };

  const saveCurrentConfig = async () => {
    if (!configName || configList.length === 0) {
      alert("Please provide a name and add at least one animation.");
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/configs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: configName, animations: configList })
      });
      
      if (response.ok) {
        fetchSavedConfigs();
        setConfigList([]);
        setConfigName('');
      } else {
        const text = await response.text();
        console.error("Save failed. Server said:", text);
      }
    } catch (error) { console.error("Error saving config:", error); }
  };

  const fetchConfigFromDatabase = (name) => {
    // FIX: Changed /config/ to /configs/ to match your other API endpoints
    fetch(`${API_BASE}/config/${encodeURIComponent(name)}`)
      .then(async res => {
        const text = await res.text(); // Read the raw text first
        
        if (!res.ok) {
          throw new Error(`Server error ${res.status}: ${text}`);
        }
        if (!text) {
          throw new Error("Server returned an empty response.");
        }
        
        return JSON.parse(text); // Safely parse it now that we know it's good
      })
      .then(data => {
        // Adjust these variables depending on exactly how Flask formats the returned dictionary
        setConfigList(data.animations || data.data.animations);
        setConfigName(data.name || data.data.name);
      })
      .catch(err => {
        console.error("Failed to fetch config:", err);
        alert("Could not load the scene from the server. Check the console!");
      });
  };

  return (
    <div style={styles.container}>
      <h2 style={{ color: '#fff' }}>LED Flux Control</h2>
      
      <MainControls 
        isOn={isOn} isPlaying={isPlaying} 
        togglePower={togglePower} togglePlayPause={togglePlayPause} 
      />
      
      <BrightnessSlider 
        brightness={brightness} handleBrightnessChange={handleBrightnessChange} 
      />
      
      <QuickPresets triggerPreset={triggerPreset} />
      
      <SavedScenes 
        savedConfigs={savedConfigs} 
        playConfig={playConfig} 
        loadConfigForEditing={loadConfigForEditing} 
        deleteSavedConfig={deleteSavedConfig} 
      />
      
      <ConfigBuilder 
        configList={configList} setConfigList={setConfigList}
        configName={configName} setConfigName={setConfigName}
        playConfig={playConfig} saveCurrentConfig={saveCurrentConfig}
        reloadCurrentConfig={fetchConfigFromDatabase}
      />
    </div>
  );
}