import React, { useEffect, useState } from 'react';
import { X, Download, Check, Loader2, AlertCircle } from 'lucide-react';

interface Model {
  id: string;
  name: string;
  description: string;
  size: string;
  downloaded: boolean;
}

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [activeModel, setActiveModel] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchModels();
    }
  }, [isOpen]);

  // Poll progress if downloading
  useEffect(() => {
    let interval: any;
    if (downloadingId) {
      interval = setInterval(async () => {
        try {
          const res = await fetch('http://localhost:8000/settings/models/progress');
          const data = await res.json();
          if (data.status === 'downloading') {
            setProgress(data.progress);
          } else if (data.status === 'completed') {
            setDownloadingId(null);
            fetchModels(); // Refresh list
          } else if (data.status === 'error') {
            setDownloadingId(null);
            alert('Download failed: ' + data.error);
          }
        } catch (e) {
          console.error(e);
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [downloadingId]);

  const fetchModels = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/settings/models');
      const data = await res.json();
      setModels(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (modelId: string) => {
    try {
      setDownloadingId(modelId);
      setProgress(0);
      await fetch('http://localhost:8000/settings/models/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId }),
      });
    } catch (e) {
      console.error(e);
      setDownloadingId(null);
    }
  };

  const handleLoad = async (modelId: string) => {
    try {
      setLoading(true);
      await fetch('http://localhost:8000/settings/models/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId }),
      });
      setActiveModel(modelId);
      alert('Model loaded successfully!');
    } catch (e) {
      alert('Failed to load model');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-[#1e1e1e] border border-white/10 rounded-xl w-[600px] max-h-[80vh] flex flex-col shadow-2xl">
        <div className="p-6 border-b border-white/10 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-white">Configurações de IA Local</h2>
          <button onClick={onClose} className="text-white/60 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1">
          <div className="space-y-4">
            {loading && !downloadingId && (
              <div className="flex justify-center py-8">
                <Loader2 className="animate-spin text-blue-500" size={32} />
              </div>
            )}

            {!loading && models.map((model) => (
              <div key={model.id} className="bg-white/5 rounded-lg p-4 border border-white/5 hover:border-white/10 transition-colors">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="text-lg font-medium text-white">{model.name}</h3>
                    <p className="text-sm text-white/60">{model.description}</p>
                    <span className="text-xs text-white/40 mt-1 block">Tamanho: {model.size}</span>
                  </div>
                  {model.downloaded ? (
                    <div className="flex flex-col gap-2 items-end">
                      <span className="flex items-center text-green-400 text-sm bg-green-400/10 px-2 py-1 rounded">
                        <Check size={14} className="mr-1" /> Baixado
                      </span>
                      <button
                        onClick={() => handleLoad(model.id)}
                        disabled={activeModel === model.id}
                        className={`text-xs px-3 py-1.5 rounded transition-colors ${
                          activeModel === model.id
                            ? 'bg-blue-500/20 text-blue-400 cursor-default'
                            : 'bg-white/10 hover:bg-white/20 text-white'
                        }`}
                      >
                        {activeModel === model.id ? 'Ativo' : 'Carregar'}
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => handleDownload(model.id)}
                      disabled={!!downloadingId}
                      className="flex items-center bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-3 py-1.5 rounded text-sm transition-colors"
                    >
                      {downloadingId === model.id ? (
                        <Loader2 size={16} className="animate-spin mr-2" />
                      ) : (
                        <Download size={16} className="mr-2" />
                      )}
                      Baixar
                    </button>
                  )}
                </div>

                {downloadingId === model.id && (
                  <div className="mt-3">
                    <div className="flex justify-between text-xs text-white/60 mb-1">
                      <span>Baixando...</span>
                      <span>{progress > 0 ? `${progress.toFixed(1)}%` : 'Iniciando...'}</span>
                    </div>
                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-blue-500 transition-all duration-300"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
          
          <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg flex gap-3">
            <AlertCircle className="text-blue-400 shrink-0" size={20} />
            <div className="text-sm text-blue-200">
              <p className="font-medium mb-1">Nota sobre Hardware</p>
              <p className="opacity-80">
                Modelos locais rodam inteiramente no seu computador. 
                O LLaVA 7B requer cerca de 8GB de RAM. 
                O Llama 3.2 11B requer 12GB+ e uma GPU dedicada é recomendada para melhor performance.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
