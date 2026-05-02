import { useState, useCallback, useEffect } from 'react';
import { api } from '../services/api';

// Default model parameters
const DEFAULT_MODEL_PARAMS = {
  temperature: 0.7,
  top_p: 1.0,
  top_k: 50,
  max_tokens: null,
  seed: null,
};

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [evaluate, setEvaluate] = useState(true);   // ✅ toggle state
  const [providers, setProviders] = useState([]);           // ✅ available providers
  const [modelsByProvider, setModelsByProvider] = useState({});  // ✅ models grouped by provider
  const [selectedProvider, setSelectedProvider] = useState('');  // ✅ selected provider
  const [selectedModel, setSelectedModel] = useState('');    // ✅ selected model
  const [modelParams, setModelParams] = useState(DEFAULT_MODEL_PARAMS);  // ✅ model parameters

  // ✅ Fetch available models on mount
  useEffect(() => {
    api.getModels()
      .then(data => {
        const providerList = data.providers || [];
        const modelsMap = data.models || {};
        setProviders(providerList);
        setModelsByProvider(modelsMap);
        
        // Auto-select first provider and its default model
        if (providerList.length > 0) {
          const firstProvider = providerList[0];
          setSelectedProvider(firstProvider);
          
          const providerModels = modelsMap[firstProvider] || [];
          const defaultModel = providerModels.find(m => m.is_default) || providerModels[0];
          if (defaultModel) {
            setSelectedModel(defaultModel.model);
          }
        }
      })
      .catch(err => console.warn('Failed to fetch models:', err));
  }, []);

  // ✅ Handle provider change - reset model selection
  const handleProviderChange = useCallback((provider) => {
    setSelectedProvider(provider);
    setSelectedModel('');  // Reset model when provider changes
  }, []);

  // ✅ Update a single model parameter
  const updateModelParam = useCallback((key, value) => {
    setModelParams(prev => ({
      ...prev,
      [key]: value === '' || value === null ? null : value
    }));
  }, []);

  // ✅ Reset model parameters to defaults
  const resetModelParams = useCallback(() => {
    setModelParams(DEFAULT_MODEL_PARAMS);
  }, []);

  const sendMessage = useCallback(async (question) => {
    if (!selectedModel) {
      alert('Please select a model first');
      return;
    }

    const userMsg = { id: Date.now(), role: 'user', text: question };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const data = await api.askQuestion(question, evaluate, selectedModel, modelParams);  // ✅ pass modelParams
      setMessages(prev => [...prev, {
        id:         Date.now() + 1,
        role:       'assistant',
        text:       data.answer,
        sources:    data.sources || [],
        evaluation: data.evaluation || null,          // ✅ store eval result
        evaluate:   evaluate,                          // ✅ store whether eval was enabled
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        id:   Date.now() + 1,
        role: 'error',
        text: err.message || 'Something went wrong.',
      }]);
    } finally {
      setLoading(false);
    }
  }, [evaluate, selectedModel, modelParams]);

  const clearMessages = useCallback(() => setMessages([]), []);

  // ✅ Get models for currently selected provider
  const currentModels = modelsByProvider[selectedProvider] || [];

  return { 
    messages, 
    loading, 
    sendMessage, 
    clearMessages, 
    evaluate, 
    setEvaluate, 
    providers,
    modelsByProvider,
    selectedProvider, 
    setSelectedProvider: handleProviderChange,
    selectedModel, 
    setSelectedModel,
    currentModels,
    modelParams,
    updateModelParam,
    resetModelParams,
  };
}