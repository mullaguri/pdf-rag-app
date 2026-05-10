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

export function useChat(isAuthenticated) {
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
    if (isAuthenticated) {
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
    }
  }, [isAuthenticated]);

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

    // Create assistant message placeholder
    const assistantId = Date.now() + 1;
    setMessages(prev => [...prev, {
      id:         assistantId,
      role:       'assistant',
      text:       '',
      sources:    [],
      evaluation: null,
      evaluate:   evaluate,
      isStreaming: true
    }]);

    try {
      let fullText = '';
      let sources = [];
      let evaluation = null;

      // Use streaming API
      const streamGenerator = api.askQuestionStream(question, evaluate, selectedModel, modelParams);
      
      for await (const event of streamGenerator) {
        if (event.type === 'chunk') {
          // Append chunk to message text
          fullText += event.content;
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantId 
                ? { ...msg, text: fullText }
                : msg
            )
          );
        } else if (event.type === 'sources') {
          sources = event.sources;
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantId 
                ? { ...msg, sources }
                : msg
            )
          );
        } else if (event.type === 'evaluation') {
          evaluation = event.evaluation;
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantId 
                ? { ...msg, evaluation, isStreaming: false }
                : msg
            )
          );
        } else if (event.type === 'error') {
          throw new Error(event.error);
        } else if (event.type === 'end') {
          // Stream ended
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantId 
                ? { ...msg, isStreaming: false }
                : msg
            )
          );
        }
      }
    } catch (err) {
      // Remove the placeholder message and add error message
      setMessages(prev => prev.filter(msg => msg.id !== assistantId));
      setMessages(prev => [...prev, {
        id:   Date.now() + 2,
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