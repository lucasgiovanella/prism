import React from 'react';
import { FileText } from 'lucide-react';
import { AnimateIcon } from '../animate-ui/icons/icon';
import { Download } from '../animate-ui/icons/download';

interface HeaderProps {
    title: string;
    hasSteps: boolean;
    onTitleChange: (title: string) => void;
    onNewTutorial: () => void;
    onSaveTutorial: () => void;
    onExportTutorial: () => void;
}

export const Header: React.FC<HeaderProps> = ({
    title,
    hasSteps,
    onTitleChange,
    onNewTutorial,
    onSaveTutorial,
    onExportTutorial
}) => {
    return (
        <header className="h-20 border-b border-white/10 flex items-center justify-between px-8 bg-zinc-950 sticky top-0 z-10">
            <div className="flex items-center gap-4 w-full max-w-2xl">
                <FileText size={20} className="text-zinc-600" />
                <input
                    type="text"
                    value={title}
                    onChange={(e) => onTitleChange(e.target.value)}
                    className="bg-transparent text-xl font-bold text-white focus:outline-none placeholder-zinc-700 w-full"
                    placeholder={!hasSteps ? "Área de Trabalho" : "Digite o título do tutorial..."}
                />
            </div>
            <div className="flex items-center gap-4">
                {hasSteps && (
                    <>
                        <button
                            onClick={onNewTutorial}
                            className="flex items-center gap-2 px-4 py-2 bg-zinc-900 text-white border border-white/10 hover:bg-zinc-800 rounded-lg transition-colors font-medium text-sm"
                        >
                            <FileText size={16} />
                            Novo
                        </button>
                        <AnimateIcon animateOnHover>
                            <button
                                onClick={onSaveTutorial}
                                className="flex items-center gap-2 px-4 py-2 bg-white text-black hover:bg-zinc-200 rounded-lg transition-colors font-semibold text-sm"
                            >
                                <Download size={16} />
                                Salvar
                            </button>
                        </AnimateIcon>
                    </>
                )}
                <AnimateIcon animateOnHover>
                    <button
                        onClick={onExportTutorial}
                        disabled={!hasSteps}
                        className="flex items-center gap-2 px-4 py-2 bg-zinc-900 text-white border border-white/10 hover:bg-zinc-800 rounded-lg transition-colors font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Download size={16} />
                        Exportar .md
                    </button>
                </AnimateIcon>
            </div>
        </header>
    );
};
