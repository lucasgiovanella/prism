import React, { useState, useEffect, useRef } from 'react';
import { Play, Square, Download, Trash2, Edit3, Eye, Settings, ChevronRight, Activity, FileText, X, ZoomIn, Plus } from 'lucide-react';
import { DotLottiePlayer } from '@dotlottie/react-player';

// Define types for Step
interface Step {
  id: string;
  element_name: string;
  description: string;
  screenshot_base64: string;
  bounding_box: any;
  element_type: string;
  is_manual?: boolean;
}

interface SavedTutorial {
  id: string;
  title: string;
  date_created: string;
  date_modified: string;
}

const API_URL = 'http://localhost:8000';

function App() {
  const [steps, setSteps] = useState<Step[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
  const [title, setTitle] = useState('Meu Tutorial');
  const [isLoading, setIsLoading] = useState(true);
  const [zoomedImage, setZoomedImage] = useState<string | null>(null);
  const [savedTutorials, setSavedTutorials] = useState<SavedTutorial[]>([]);
  const [serverOnline, setServerOnline] = useState(false);
  const [currentTutorialId, setCurrentTutorialId] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // Simulate initial loading for effect
    const timer = setTimeout(() => setIsLoading(false), 2000);
    
    // Load recent tutorials
    loadRecentTutorials();
    
    // Check server health
    checkServerHealth();
    const healthInterval = setInterval(checkServerHealth, 5000);
    
    return () => {
      clearTimeout(timer);
      clearInterval(healthInterval);
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const toggleRecording = async () => {
    if (isRecording) {
      // Stop
      try {
        await fetch(`${API_URL}/stop-recording`, { method: 'POST' });
        setIsRecording(false);
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
      } catch (e) {
        console.error(e);
      }
    } else {
      // Start
      try {
        await fetch(`${API_URL}/start-recording`, { method: 'POST' });
        setIsRecording(true);
        
        // Connect SSE
        eventSourceRef.current = new EventSource(`${API_URL}/events`);
        eventSourceRef.current.onmessage = (event) => {
          const newStep = JSON.parse(event.data);
          setSteps((prev) => [...prev, newStep]);
        };
      } catch (e) {
        console.error(e);
      }
    }
  };

  const deleteStep = (id: string) => {
    setSteps((prev) => prev.filter((s) => s.id !== id));
    if (selectedStepId === id) setSelectedStepId(null);
  };

  const updateStepDescription = (id: string, newDesc: string) => {
    setSteps((prev) => prev.map((s) => (s.id === id ? { ...s, description: newDesc } : s)));
  };

  const updateStepElementName = (id: string, newName: string) => {
    setSteps((prev) => prev.map((s) => (s.id === id ? { ...s, element_name: newName } : s)));
  };

  const insertStep = (afterIndex: number) => {
    const newStep: Step = {
      id: `step-${Date.now()}`,
      element_name: 'Novo Passo',
      description: '',
      screenshot_base64: '',
      bounding_box: null,
      element_type: 'manual',
      is_manual: true
    };
    setSteps((prev) => [
      ...prev.slice(0, afterIndex + 1),
      newStep,
      ...prev.slice(afterIndex + 1)
    ]);
  };

  const checkServerHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/health`);
      if (response.ok) {
        setServerOnline(true);
      } else {
        setServerOnline(false);
      }
    } catch (error) {
      setServerOnline(false);
    }
  };

  const loadRecentTutorials = async () => {
    try {
      const response = await fetch(`${API_URL}/tutorials`);
      if (response.ok) {
        const data = await response.json();
        setSavedTutorials(data.tutorials || []);
      }
    } catch (error) {
      console.error('Failed to load tutorials:', error);
    }
  };

  const loadTutorial = async (tutorialId: string) => {
    try {
      const response = await fetch(`${API_URL}/tutorials/${tutorialId}`);
      if (response.ok) {
        const tutorial = await response.json();
        setTitle(tutorial.title);
        setSteps(tutorial.steps);
        setCurrentTutorialId(tutorialId);
      }
    } catch (error) {
      console.error('Failed to load tutorial:', error);
    }
  };

  const saveTutorial = async () => {
    try {
      const data = {
        title,
        steps: steps.map(s => ({
          ...s,
          screenshot_base64: s.is_manual ? '' : s.screenshot_base64
        }))
      };

      if (currentTutorialId) {
        // Update existing
        await fetch(`${API_URL}/tutorials/${currentTutorialId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
      } else {
        // Create new
        const response = await fetch(`${API_URL}/tutorials`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        const result = await response.json();
        setCurrentTutorialId(result.id);
      }

      loadRecentTutorials();
      alert('Tutorial salvo com sucesso!');
    } catch (error) {
      console.error('Failed to save tutorial:', error);
      alert('Erro ao salvar tutorial.');
    }
  };

  const deleteTutorialHandler = async (tutorialId: string) => {
    if (!confirm('Deseja realmente excluir este tutorial?')) return;
    
    try {
      await fetch(`${API_URL}/tutorials/${tutorialId}`, {
        method: 'DELETE'
      });
      loadRecentTutorials();
      if (currentTutorialId === tutorialId) {
        setSteps([]);
        setTitle('Meu Tutorial');
        setCurrentTutorialId(null);
      }
    } catch (error) {
      console.error('Failed to delete tutorial:', error);
    }
  };

  const newTutorial = () => {
    if (steps.length > 0 && !confirm('Deseja fechar o tutorial atual? Alterações não salvas serão perdidas.')) {
      return;
    }
    setSteps([]);
    setTitle('Meu Tutorial');
    setCurrentTutorialId(null);
    setSelectedStepId(null);
  };

  const exportTutorial = async () => {
    if (steps.length === 0) return;
    
    // Format data for Electron IPC
    const exportData = {
      title,
      steps: steps.map(s => ({
        description: s.description,
        image: s.screenshot_base64 ? `data:image/png;base64,${s.screenshot_base64}` : null
      }))
    };

    // Call Electron API
    // @ts-ignore
    if (window.electronAPI) {
      // @ts-ignore
      const result = await window.electronAPI.saveTutorial(exportData);
      if (result.success) {
        alert(`Tutorial salvo em: ${result.path}`);
      } else {
        alert(`Erro ao salvar: ${result.message}`);
      }
    } else {
      alert("Ambiente Electron não detectado (modo web).");
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center w-screen h-screen bg-black text-white">
        <div className="w-64 h-64">
          <DotLottiePlayer
            src="/src/assets/ai_generating.lottie"
            loop
            autoplay
          />
        </div>
        <p className="mt-4 text-sm font-medium tracking-widest text-zinc-500 animate-pulse uppercase">Inicializando DocGen AI...</p>
      </div>
    );
  }

  return (
    <div className="flex w-screen h-screen bg-black text-white font-sans overflow-hidden">
      {/* Sidebar */}
      <aside className="w-72 bg-black border-r border-white/10 flex flex-col z-20">
        <div className="p-8 border-b border-white/10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center shadow-sm">
              <Activity size={18} className="text-black" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              DocGen
            </h1>
          </div>
        </div>

        <nav className="flex-1 p-6 space-y-6 overflow-y-auto">
          {/* Recording Control */}
          <div className="space-y-3">
            <button
              onClick={toggleRecording}
              className={`group relative flex items-center gap-4 w-full p-3.5 rounded-xl transition-all duration-200 border ${
                isRecording 
                  ? 'bg-red-900/20 text-red-400 border-red-500/20 hover:bg-red-900/30' 
                  : 'bg-white text-black border-white hover:bg-zinc-200'
              }`}
            >
              {isRecording ? <Square size={18} className="fill-current" /> : <Play size={18} className="fill-current" />}
              <span className="font-semibold tracking-wide">{isRecording ? 'Parar Gravação' : 'Iniciar Gravação'}</span>
            </button>
          </div>

          {/* Recent Tutorials */}
          <div className="space-y-3">
            <div className="text-xs font-bold text-zinc-500 uppercase tracking-wider px-2">Últimos Manuais</div>
            <div className="space-y-2">
              {savedTutorials.length === 0 ? (
                <p className="text-xs text-zinc-600 px-2">Nenhum manual salvo</p>
              ) : (
                savedTutorials.map((tutorial) => (
                  <div
                    key={tutorial.id}
                    className="group flex items-center justify-between p-3 bg-zinc-900/50 hover:bg-zinc-800 rounded-lg border border-white/5 hover:border-white/20 transition-all cursor-pointer"
                    onClick={() => loadTutorial(tutorial.id)}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">{tutorial.title}</p>
                      <p className="text-xs text-zinc-500">{new Date(tutorial.date_modified).toLocaleDateString('pt-BR')}</p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteTutorialHandler(tutorial.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-900/20 hover:text-red-400 rounded transition-all"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </nav>
        
        {/* Server Status */}
        <div className="p-6 border-t border-white/10">
          <div className="flex items-center gap-3 text-xs text-zinc-500 bg-zinc-900/50 p-3 rounded-xl border border-white/10">
            <div className={`w-2 h-2 rounded-full ${serverOnline ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
            {serverOnline ? 'IA Ativa' : 'IA Offline'}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 bg-zinc-950 relative z-10">
        
        {/* Header */}
        <header className="h-20 border-b border-white/10 flex items-center justify-between px-8 bg-zinc-950 sticky top-0 z-10">
          <div className="flex items-center gap-4 w-full max-w-2xl">
             <FileText size={20} className="text-zinc-600" />
             <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="bg-transparent text-xl font-bold text-white focus:outline-none placeholder-zinc-700 w-full"
              placeholder={steps.length === 0 ? "Área de Trabalho" : "Digite o título do tutorial..."}
            />
          </div>
          <div className="flex items-center gap-4">
            {steps.length > 0 && (
              <>
                <button
                  onClick={newTutorial}
                  className="flex items-center gap-2 px-4 py-2 bg-zinc-900 text-white border border-white/10 hover:bg-zinc-800 rounded-lg transition-colors font-medium text-sm"
                >
                  <FileText size={16} />
                  Novo
                </button>
                <button
                  onClick={saveTutorial}
                  className="flex items-center gap-2 px-4 py-2 bg-white text-black hover:bg-zinc-200 rounded-lg transition-colors font-semibold text-sm"
                >
                  <Download size={16} />
                  Salvar
                </button>
              </>
            )}
            <button
              onClick={exportTutorial}
              disabled={steps.length === 0}
              className="flex items-center gap-2 px-4 py-2 bg-zinc-900 text-white border border-white/10 hover:bg-zinc-800 rounded-lg transition-colors font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Download size={16} />
              Exportar .md
            </button>
          </div>
        </header>

        {/* Steps List */}
        <div className="flex-1 overflow-y-auto p-8 space-y-6 scroll-smooth custom-scrollbar bg-zinc-950">
          {steps.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-zinc-600 space-y-6">
              <div className="w-24 h-24 rounded-3xl bg-zinc-900/50 border border-white/5 flex items-center justify-center">
                <Eye size={48} className="text-zinc-700" />
              </div>
              <div className="text-center space-y-2">
                <p className="text-lg font-medium text-zinc-400">Nenhuma ação registrada</p>
                <p className="text-sm text-zinc-600">Inicie a gravação para começar a capturar seu tutorial.</p>
              </div>
            </div>
          ) : (
            <>
              {steps.map((step, index) => (
                <React.Fragment key={step.id}>
                  <div
                    onClick={() => setSelectedStepId(step.id)}
                    className={`group relative bg-black border rounded-xl p-1 transition-all duration-200 hover:border-zinc-700 ${
                      selectedStepId === step.id ? 'border-white ring-1 ring-white/10' : 'border-white/10'
                    }`}
                  >
                    <div className="flex gap-6 p-5">
                      {/* Step Number */}
                      <div className="flex-shrink-0 flex flex-col items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-zinc-900 text-white flex items-center justify-center text-sm font-bold border border-white/10 group-hover:bg-white group-hover:text-black transition-colors duration-300">
                          {index + 1}
                        </div>
                        <div className="h-full w-px bg-zinc-900 group-last:hidden"></div>
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0 space-y-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <input
                                type="text"
                                value={step.element_name}
                                onChange={(e) => updateStepElementName(step.id, e.target.value)}
                                onClick={(e) => e.stopPropagation()}
                                onFocus={(e) => e.stopPropagation()}
                                onMouseDown={(e) => e.stopPropagation()}
                                className="font-bold text-lg text-white bg-transparent border-b border-transparent hover:border-zinc-700 focus:border-white focus:outline-none transition-colors flex-1 min-w-0"
                                placeholder="Nome do passo"
                              />
                              <ChevronRight size={14} className="text-zinc-600 flex-shrink-0" />
                              <span className="text-xs font-medium text-zinc-400 bg-zinc-900 px-2 py-0.5 rounded-md border border-white/10 flex-shrink-0">
                                 {step.element_type}
                              </span>
                            </div>
                          </div>
                          <button
                            onClick={(e) => { e.stopPropagation(); deleteStep(step.id); }}
                            className="opacity-0 group-hover:opacity-100 p-2 hover:bg-red-900/20 hover:text-red-400 rounded-lg transition-all duration-200 text-zinc-600"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>

                        <div className="flex gap-6">
                            {/* Image Preview - Only show for non-manual steps */}
                            {!step.is_manual && (
                              <div 
                                className="relative w-80 aspect-video rounded-lg overflow-hidden bg-zinc-900 border border-white/10 group/image cursor-pointer"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  if (step.screenshot_base64) {
                                    setZoomedImage(`data:image/png;base64,${step.screenshot_base64}`);
                                  }
                                }}
                              >
                                {step.screenshot_base64 ? (
                                  <>
                                    <img
                                      src={`data:image/png;base64,${step.screenshot_base64}`}
                                      alt={`Step ${index + 1}`}
                                      className="w-full h-full object-cover group-hover/image:scale-105 transition-transform duration-500"
                                    />
                                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover/image:opacity-100 transition-opacity flex items-center justify-center">
                                      <ZoomIn size={32} className="text-white" />
                                    </div>
                                  </>
                                ) : (
                                  <div className="w-full h-full flex items-center justify-center text-xs text-zinc-600">Sem imagem</div>
                                )}
                              </div>
                            )}

                            {/* Description Editor */}
                            <div className={`${step.is_manual ? 'flex-1' : 'flex-1'} relative`}>
                              <label className="text-xs font-bold text-zinc-600 mb-2 block uppercase tracking-wider">Descrição da Ação</label>
                              <div className="relative h-full">
                                <textarea
                                    value={step.description}
                                    onChange={(e) => updateStepDescription(step.id, e.target.value)}
                                    onClick={(e) => e.stopPropagation()}
                                    onFocus={(e) => e.stopPropagation()}
                                    onMouseDown={(e) => e.stopPropagation()}
                                    className="w-full h-[calc(100%-2rem)] bg-zinc-900 border border-white/10 rounded-lg p-4 text-sm text-zinc-300 focus:border-white focus:ring-0 focus:outline-none resize-none transition-all hover:bg-zinc-800"
                                    placeholder="Digite a descrição do passo..."
                                />
                                <Edit3 size={14} className="absolute right-4 top-4 text-zinc-600 pointer-events-none" />
                              </div>
                            </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Insert Step Button */}
                  <div className="flex items-center justify-center -my-3 relative z-10">
                    <button
                      onClick={() => insertStep(index)}
                      className="group/insert flex items-center gap-2 px-4 py-2 bg-zinc-900/50 hover:bg-zinc-800 border border-white/5 hover:border-white/20 rounded-full text-zinc-600 hover:text-white transition-all duration-200 opacity-0 hover:opacity-100 focus:opacity-100"
                      title="Inserir passo"
                    >
                      <Plus size={16} />
                      <span className="text-xs font-medium">Adicionar Passo</span>
                    </button>
                  </div>
                </React.Fragment>
              ))}
            </>
          )}
        </div>
      </main>

      {/* Image Zoom Modal */}
      {zoomedImage && (
        <div 
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-8 backdrop-blur-sm"
          onClick={() => setZoomedImage(null)}
        >
          <button
            onClick={() => setZoomedImage(null)}
            className="absolute top-4 right-4 p-3 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors"
          >
            <X size={24} />
          </button>
          <img
            src={zoomedImage}
            alt="Zoomed screenshot"
            className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  );
}

export default App;
