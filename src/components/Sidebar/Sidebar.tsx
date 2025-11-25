import React from 'react';
import { AnimateIcon } from '../animate-ui/icons/icon';
import { Play } from "../animate-ui/icons/play"
import { SavedTutorial } from '../../types';
import { Pause } from "../animate-ui/icons/pause"
import { Trash2 } from '../animate-ui/icons/trash-2';
import { Settings } from 'lucide-react';

interface SidebarProps {
    isRecording: boolean;
    serverOnline: boolean;
    savedTutorials: SavedTutorial[];
    onToggleRecording: () => void;
    onLoadTutorial: (id: string) => void;
    onDeleteTutorial: (id: string) => void;
    onOpenSettings?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
    isRecording,
    serverOnline,
    savedTutorials,
    onToggleRecording,
    onLoadTutorial,
    onDeleteTutorial,
    onOpenSettings
}) => {
    return (
        <aside className="w-72 bg-black border-r border-white/10 flex flex-col z-20">
            <div className="p-8 border-b border-white/10 flex justify-between items-center">
                <div className="flex items-center gap-2">
                    <div className="w-16 h-16 rounded-lg flex items-center justify-center shadow-sm">
                        <img src="/src/assets/icons/icon_bg.png" alt="Icon" className="w-full h-full" />
                    </div>
                    <h1 className="text-2xl font-bold tracking-tight text-white">
                        Prism
                    </h1>
                </div>
                {onOpenSettings && (
                    <button
                        onClick={onOpenSettings}
                        className="p-2 hover:bg-white/10 rounded-lg transition-colors text-white/60 hover:text-white"
                        title="Configurações"
                    >
                        <Settings size={20} />
                    </button>
                )}
            </div>

            <nav className="flex-1 p-6 space-y-6 overflow-y-auto">
                {/* Recording Control */}
                <div className="space-y-3">
                    <AnimateIcon animateOnHover>
                        <button
                            onClick={onToggleRecording}
                            className={`group relative flex items-center gap-4 w-full p-3.5 rounded-xl transition-all duration-200 border ${isRecording
                                ? 'bg-red-900/20 text-red-400 border-red-500/20 hover:bg-red-900/30'
                                : 'bg-white text-black border-white hover:bg-zinc-200'
                                }`}
                        >
                            {isRecording ? <Pause size={18} className="fill-current" /> : <Play size={18} className="fill-current" />}
                            <span className="font-semibold tracking-wide">{isRecording ? 'Parar Gravação' : 'Iniciar Gravação'}</span>
                        </button>
                    </AnimateIcon>
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
                                    onClick={() => onLoadTutorial(tutorial.id)}
                                >
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-white truncate">{tutorial.title}</p>
                                        <p className="text-xs text-zinc-500">{new Date(tutorial.date_modified).toLocaleDateString('pt-BR')}</p>
                                    </div>
                                    <AnimateIcon animateOnHover>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onDeleteTutorial(tutorial.id);
                                            }}
                                            className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-900/20 hover:text-red-400 rounded transition-all"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </AnimateIcon>
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
    );
};
