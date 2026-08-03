import React, { useState, useEffect, useRef } from 'react';
import { Settings, Save, CheckCircle2, Key, Cpu, Server, Globe, X, Users } from 'lucide-react';

// Stage 2 analyst definitions matching backend STAGE2_PERSPECTIVE
const STAGE2_ANALYSTS = [
  { id: 'value_investing_sage', label: '价值投资大师', labelEn: 'Value Investing Sage' },
  { id: 'growth_visionary', label: '成长股预见者', labelEn: 'Growth Visionary' },
  { id: 'contrarian_strategist', label: '逆向策略师', labelEn: 'Contrarian Strategist' },
  { id: 'macro_hedge_titan', label: '宏观对冲泰坦', labelEn: 'Macro Hedge Titan' },
  { id: 'soros-style_financial_philosopher', label: '索罗斯金融哲学', labelEn: 'Soros-Style Philosopher' },
  { id: 'serenity_alpha_analyst', label: 'Alpha 分析师', labelEn: 'Serenity Alpha Analyst' },
  { id: 'deep_research_specialist', label: '深度研究专家', labelEn: 'Deep Research Specialist' },
];

const ALL_STAGE2_IDS = STAGE2_ANALYSTS.map(a => a.id);

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
  analystStage2: string[];
  setAnalystStage2: (val: string[]) => void;
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
  analystStage2,
  setAnalystStage2,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Local draft state for settings until saved
  const [draftProvider, setDraftProvider] = useState(llmProvider);
  const [draftModel, setDraftModel] = useState(llmModel);
  const [draftApiKey, setDraftApiKey] = useState(llmApiKey);
  const [draftLanguage, setDraftLanguage] = useState(llmLanguage);
  const [draftAnalystStage2, setDraftAnalystStage2] = useState<string[]>(analystStage2);
  const [showSaveToast, setShowSaveToast] = useState(false);

  // Sync draft state with props when opening
  useEffect(() => {
    if (isOpen) {
      setDraftProvider(llmProvider);
      setDraftModel(llmModel);
      setDraftApiKey(llmApiKey);
      setDraftLanguage(llmLanguage);
      setDraftAnalystStage2(analystStage2);
      setShowSaveToast(false);
    }
  }, [isOpen, llmProvider, llmModel, llmApiKey, llmLanguage, analystStage2]);

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
    setAnalystStage2(draftAnalystStage2);

    localStorage.setItem('faos_provider', draftProvider);
    localStorage.setItem('faos_model', draftModel);
    localStorage.setItem('faos_api_key', draftApiKey);
    localStorage.setItem('faos_language', draftLanguage);
    localStorage.setItem('faos_analyst_stage2', JSON.stringify(draftAnalystStage2));

    setShowSaveToast(true);
    setTimeout(() => {
      setShowSaveToast(false);
      onClose();
    }, 1200);
  };

  const toggleAnalyst = (id: string) => {
    setDraftAnalystStage2(prev =>
      prev.includes(id) ? prev.filter(a => a !== id) : [...prev, id]
    );
  };

  const isZh = draftLanguage === 'zh';

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

            {/* ── Analyst Selection ── */}
            <div className="settings-field analyst-selection">
              <label>
                <Users size={14} /> {isZh ? '分析师选择 (Stage 2)' : 'Analyst Selection (Stage 2)'}
              </label>

              {/* Stage 1: Always-on core analysts */}
              <div className="analyst-group">
                <div className="analyst-group-label">
                  Stage 1 — {isZh ? '核心分析 (必选)' : 'Core Analysis (Always On)'}
                </div>
                {['fundamental_analyst', 'technical_analyst', 'sentiment_analyst'].map(id => (
                  <label key={id} className="analyst-checkbox locked">
                    <input type="checkbox" checked disabled />
                    <span className="analyst-name">
                      {id === 'fundamental_analyst' ? (isZh ? '基本面分析师' : 'Fundamental') :
                       id === 'technical_analyst' ? (isZh ? '技术面分析师' : 'Technical') :
                       (isZh ? '情绪分析师' : 'Sentiment')}
                    </span>
                    <span className="analyst-badge always-on">{isZh ? '必选' : 'Required'}</span>
                  </label>
                ))}
              </div>

              {/* Stage 2: User-selectable perspective analysts */}
              <div className="analyst-group">
                <div className="analyst-group-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Stage 2 — {isZh ? '视角扩展 (可选)' : 'Perspective (Optional)'}</span>
                  <span style={{ display: 'flex', gap: '8px' }}>
                    <button
                      type="button"
                      className="analyst-batch-btn"
                      onClick={() => setDraftAnalystStage2([...ALL_STAGE2_IDS])}
                    >
                      {isZh ? '全选' : 'All'}
                    </button>
                    <button
                      type="button"
                      className="analyst-batch-btn"
                      onClick={() => setDraftAnalystStage2([])}
                    >
                      {isZh ? '清空' : 'None'}
                    </button>
                  </span>
                </div>
                {STAGE2_ANALYSTS.map(analyst => (
                  <label key={analyst.id} className="analyst-checkbox">
                    <input
                      type="checkbox"
                      checked={draftAnalystStage2.includes(analyst.id)}
                      onChange={() => toggleAnalyst(analyst.id)}
                    />
                    <span className="analyst-name">{isZh ? analyst.label : analyst.labelEn}</span>
                  </label>
                ))}
                <div className="analyst-count">
                  {draftAnalystStage2.length}/{STAGE2_ANALYSTS.length} {isZh ? '已选择' : 'selected'}
                </div>
              </div>
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
