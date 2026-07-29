import React, { useState, useEffect, useRef } from 'react';
import { Settings, Save, CheckCircle2, Key, Cpu, Server, Globe, X } from 'lucide-react';

interface SettingsPopoverProps {
  isOpen: boolean;
  onToggle: () => void;
  onClose: () => void;
  llmProvider: string;
  setLlmProvider: (val: string) => void;
  llmModel: string;
  setLlmModel: (val: string) => void;
  llmApiKey: string;
  setLlmApiKey: (val: string) => void;
  llmLanguage: string;
  setLmLanguage: (val: string) => void;
  modelOptions: Record<string, string[]>;
}

export const SettingsPopover: React.FC<SettingsPopoverProps> = ({
  isOpen,
  onToggle,
  onClose,
  llmProvider,
  setLlmProvider,
  llmModel,
  setLlmModel,
  llmApiKey,
  setLlmApiKey,
  llmLanguage,
  setLmLanguage,
  modelOptions,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Local draft state for settings until saved
  const [draftProvider, setDraftProvider] = useState(llmProvider);
  const [draftModel, setDraftModel] = useState(llmModel);
  const [draftApiKey, setDraftApiKey] = useState(llmApiKey);
  const [draftLanguage, setDraftLanguage] = useState(llmLanguage);
  const [showSaveToast, setShowSaveToast] = useState(false);

  // Sync draft state with props when opening
  useEffect(() => {
    if (isOpen) {
      setDraftProvider(llmProvider);
      setDraftModel(llmModel);
      setDraftApiKey(llmApiKey);
      setDraftLanguage(llmLanguage);
      setShowSaveToast(false);
    }
  }, [isOpen, llmProvider, llmModel, llmApiKey, llmLanguage]);

  // Click outside to auto-close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  const handleSave = () => {
    setLlmProvider(draftProvider);
    setLlmModel(draftModel);
    setLlmApiKey(draftApiKey);
    setLmLanguage(draftLanguage);

    localStorage.setItem('faos_provider', draftProvider);
    localStorage.setItem('faos_model', draftModel);
    localStorage.setItem('faos_api_key', draftApiKey);
    localStorage.setItem('faos_language', draftLanguage);

    setShowSaveToast(true);
    setTimeout(() => {
      setShowSaveToast(false);
      onClose();
    }, 1200);
  };

  return (
    <div ref={containerRef} className="settings-wrapper" style={{ position: 'relative', display: 'inline-block' }}>
      {/* Settings Toggle Button */}
      <button
        type="button"
        className={`settings-toggle-btn ${isOpen ? 'active' : ''}`}
        onClick={onToggle}
        title="AI LLM Settings"
        aria-label="Settings"
      >
        <Settings className={`settings-icon ${isOpen ? 'spin' : ''}`} size={18} />
      </button>

      {/* Settings Popover Dropdown */}
      {isOpen && (
        <div className="settings-popover">
          <div className="settings-header">
            <div className="settings-title">
              <Settings size={16} color="var(--accent-color)" />
              <span>Model & System Config</span>
            </div>
            <button type="button" className="settings-close-btn" onClick={onClose}>
              <X size={16} />
            </button>
          </div>

          {/* Toast Notification */}
          {showSaveToast && (
            <div className="settings-toast-success">
              <CheckCircle2 size={16} />
              <span>Settings saved successfully!</span>
            </div>
          )}

          <div className="settings-body">
            {/* Output Language Select */}
            <div className="settings-field">
              <label>
                <Globe size={14} /> Output Language / 语言
              </label>
              <select
                value={draftLanguage}
                onChange={(e) => setDraftLanguage(e.target.value)}
              >
                <option value="zh">中文 (Chinese)</option>
                <option value="en">English</option>
              </select>
            </div>

            {/* Provider Select */}
            <div className="settings-field">
              <label>
                <Server size={14} /> Provider
              </label>
              <select
                value={draftProvider}
                onChange={(e) => {
                  const val = e.target.value;
                  setDraftProvider(val);
                  setDraftModel(modelOptions[val]?.[0] || '');
                }}
              >
                <option value="mock">Mock</option>
                <option value="gemini">Gemini</option>
                <option value="deepseek">DeepSeek</option>
                <option value="openrouter">OpenRouter</option>
              </select>
            </div>

            {/* Model Select */}
            <div className="settings-field">
              <label>
                <Cpu size={14} /> Model
              </label>
              <select
                value={draftModel}
                onChange={(e) => setDraftModel(e.target.value)}
              >
                {(modelOptions[draftProvider] || []).map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>

            {/* API Key Input */}
            <div className="settings-field">
              <label>
                <Key size={14} /> API Key
              </label>
              <input
                type="password"
                value={draftApiKey}
                onChange={(e) => setDraftApiKey(e.target.value)}
                placeholder="Leave empty to use backend default"
              />
            </div>
          </div>

          {/* Footer Actions */}
          <div className="settings-footer">
            <button type="button" className="btn-secondary settings-cancel-btn" onClick={onClose}>
              Cancel
            </button>
            <button type="button" className="btn-primary settings-save-btn" onClick={handleSave}>
              <Save size={14} /> Save Config
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
