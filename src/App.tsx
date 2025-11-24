import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar/Sidebar';
import { Header } from './components/Header/Header';
import { StepList } from './components/StepList/StepList';
import { ImageZoomModal } from './components/Modals/ImageZoomModal';
import { useRecording } from './hooks/useRecording';
import { useTutorials } from './hooks/useTutorials';
import { api } from './services/api';
import { Step } from './types';

function App() {
  const { isRecording, steps, setSteps, toggleRecording } = useRecording();
  const { savedTutorials, currentTutorialId, setCurrentTutorialId, loadRecentTutorials, saveTutorial, deleteTutorial, loadTutorial } = useTutorials();

  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
  const [title, setTitle] = useState('Meu Tutorial');
  const [isLoading, setIsLoading] = useState(true);
  const [zoomedImage, setZoomedImage] = useState<string | null>(null);
  const [serverOnline, setServerOnline] = useState(false);
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showNotification = (message: string, type: 'success' | 'error' = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 2000);

    const checkServerHealth = async () => {
      const isOnline = await api.checkHealth();
      setServerOnline(isOnline);
    };

    checkServerHealth();
    const healthInterval = setInterval(checkServerHealth, 5000);

    return () => {
      clearTimeout(timer);
      clearInterval(healthInterval);
    };
  }, []);

  const handleLoadTutorial = async (id: string) => {
    const tutorial = await loadTutorial(id);
    if (tutorial) {
      setTitle(tutorial.title);
      setSteps(tutorial.steps);
    }
  };

  const handleSaveTutorial = async () => {
    const success = await saveTutorial(title, steps);
    if (success) {
      showNotification('Tutorial salvo com sucesso!');
    } else {
      showNotification('Erro ao salvar tutorial.', 'error');
    }
  };

  const handleDeleteTutorial = async (id: string) => {
    if (!confirm('Deseja realmente excluir este tutorial?')) return;

    const isCurrent = await deleteTutorial(id);
    if (isCurrent) {
      setSteps([]);
      setTitle('Meu Tutorial');
    }
  };

  const handleNewTutorial = () => {
    if (steps.length > 0 && !confirm('Deseja fechar o tutorial atual? Alterações não salvas serão perdidas.')) {
      return;
    }
    setSteps([]);
    setTitle('Meu Tutorial');
    setCurrentTutorialId(null);
    setSelectedStepId(null);
  };

  const handleExportTutorial = async () => {
    if (steps.length === 0) return;

    const exportData = {
      title,
      steps: steps.map(s => ({
        description: s.description,
        image: s.screenshot_base64 ? `data:image/png;base64,${s.screenshot_base64}` : null,
        content_type: s.content_type || 'text',
        code_language: s.code_language,
        code_content: s.code_content
      }))
    };

    // @ts-ignore
    if (window.electronAPI) {
      // @ts-ignore
      const result = await window.electronAPI.saveTutorial(exportData);
      if (result.success) {
        showNotification(`Tutorial salvo em: ${result.path}`);
      } else {
        showNotification(`Erro ao salvar: ${result.message}`, 'error');
      }
    } else {
      showNotification("Ambiente Electron não detectado (modo web).", 'error');
    }
  };

  // Step manipulation handlers
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

  const updateStepContentType = (id: string, type: 'text' | 'code') => {
    setSteps((prev) => prev.map((s) => (s.id === id ? { ...s, content_type: type } : s)));
  };

  const updateStepCodeLanguage = (id: string, lang: string) => {
    setSteps((prev) => prev.map((s) => (s.id === id ? { ...s, code_language: lang } : s)));
  };

  const updateStepCodeContent = (id: string, content: string) => {
    setSteps((prev) => prev.map((s) => (s.id === id ? { ...s, code_content: content } : s)));
  };

  const insertStep = (afterIndex: number) => {
    const newStep: Step = {
      id: `step-${Date.now()}`,
      element_name: 'Novo Passo',
      description: '',
      screenshot_base64: '',
      bounding_box: null,
      element_type: 'manual',
      is_manual: true,
      content_type: 'text'
    };
    setSteps((prev) => [
      ...prev.slice(0, afterIndex + 1),
      newStep,
      ...prev.slice(afterIndex + 1)
    ]);
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center w-screen h-screen bg-black text-white">
        <div className="relative w-24 h-24 mb-8">
          <div className="absolute inset-0 bg-blue-500/30 blur-2xl rounded-full animate-pulse"></div>
          <img
            src="/src/assets/icons/icon_bg.png"
            alt="Prism AI"
            className="relative z-10 w-full h-full object-contain drop-shadow-2xl"
          />
        </div>
        <p className="text-xs font-medium tracking-[0.2em] text-zinc-600 animate-pulse uppercase">Inicializando Prism AI</p>
      </div>
    );
  }

  return (
    <div className="flex w-screen h-screen bg-black text-white font-sans overflow-hidden min-w-[1024px]">
      <Sidebar
        isRecording={isRecording}
        serverOnline={serverOnline}
        savedTutorials={savedTutorials}
        onToggleRecording={toggleRecording}
        onLoadTutorial={handleLoadTutorial}
        onDeleteTutorial={handleDeleteTutorial}
      />

      <main className="flex-1 flex flex-col min-w-0 bg-zinc-950 relative z-10">
        <Header
          title={title}
          hasSteps={steps.length > 0}
          onTitleChange={setTitle}
          onNewTutorial={handleNewTutorial}
          onSaveTutorial={handleSaveTutorial}
          onExportTutorial={handleExportTutorial}
        />

        <StepList
          steps={steps}
          selectedStepId={selectedStepId}
          onSelectStep={setSelectedStepId}
          onDeleteStep={deleteStep}
          onUpdateStepName={updateStepElementName}
          onUpdateStepDescription={updateStepDescription}
          onUpdateStepContentType={updateStepContentType}
          onUpdateStepCodeLanguage={updateStepCodeLanguage}
          onUpdateStepCodeContent={updateStepCodeContent}
          onInsertStep={insertStep}
          onZoomImage={setZoomedImage}
        />
      </main>

      <ImageZoomModal
        imageUrl={zoomedImage}
        onClose={() => setZoomedImage(null)}
      />

      {notification && (
        <div className={`fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white font-medium z-50 transition-all ${
          notification.type === 'success' ? 'bg-green-600' : 'bg-red-600'
        }`}>
          {notification.message}
        </div>
      )}
    </div>
  );
}

export default App;
