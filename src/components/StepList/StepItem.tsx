import React from 'react';
import { ChevronRight, ZoomIn, Edit3, Plus } from 'lucide-react';
import { Step } from '../../types';
import { Trash2 } from '../animate-ui/icons/trash-2';
import { AnimateIcon } from '../animate-ui/icons/icon';
import { MessageSquareCode } from '../animate-ui/icons/message-square-code';
import { MessageSquareText } from '../animate-ui/icons/message-square-text';

interface StepItemProps {
    step: Step;
    index: number;
    isSelected: boolean;
    onSelect: () => void;
    onDelete: () => void;
    onUpdateName: (name: string) => void;
    onUpdateDescription: (desc: string) => void;
    onUpdateContentType: (type: 'text' | 'code') => void;
    onUpdateCodeLanguage: (lang: string) => void;
    onUpdateCodeContent: (content: string) => void;
    onInsertStep: () => void;
    onZoomImage: (img: string) => void;
}

export const StepItem: React.FC<StepItemProps> = ({
    step,
    index,
    isSelected,
    onSelect,
    onDelete,
    onUpdateName,
    onUpdateDescription,
    onUpdateContentType,
    onUpdateCodeLanguage,
    onUpdateCodeContent,
    onInsertStep,
    onZoomImage
}) => {
    return (
        <>
            <div
                onClick={onSelect}
                className={`group relative bg-black border rounded-xl p-1 transition-all duration-200 hover:border-zinc-700 ${isSelected ? 'border-white ring-1 ring-white/10' : 'border-white/10'
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
                                        onChange={(e) => onUpdateName(e.target.value)}
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
                                onClick={(e) => { e.stopPropagation(); onDelete(); }}
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
                                            onZoomImage(`data:image/png;base64,${step.screenshot_base64}`);
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

                            {/* Content Editor */}
                            <div className={`${step.is_manual ? 'flex-1' : 'flex-1'} relative flex flex-col gap-2`}>
                                <div className="flex items-center justify-between">
                                    <label className="text-xs font-bold text-zinc-600 uppercase tracking-wider flex items-center gap-2">
                                        Conteúdo
                                        {step.isRefining && (
                                            <span className="ml-2 text-yellow-500 animate-pulse">
                                                • Analisando com IA...
                                            </span>
                                        )}
                                    </label>

                                    {/* Toggle Type */}
                                    <div className="flex bg-zinc-900 rounded-lg p-0.5 border border-white/10">
                                        <AnimateIcon animateOnHover>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); onUpdateContentType('text'); }}
                                                className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium transition-all ${step.content_type !== 'code'
                                                    ? 'bg-zinc-800 text-white shadow-sm'
                                                    : 'text-zinc-500 hover:text-zinc-300'
                                                    }`}
                                            >
                                                <MessageSquareText size={12} />
                                                Texto
                                            </button>
                                        </AnimateIcon>
                                        <AnimateIcon animateOnHover>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); onUpdateContentType('code'); }}
                                                className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium transition-all ${step.content_type === 'code'
                                                    ? 'bg-zinc-800 text-white shadow-sm'
                                                    : 'text-zinc-500 hover:text-zinc-300'
                                                    }`}
                                            >
                                                <MessageSquareCode size={12} />
                                                Código
                                            </button>
                                        </AnimateIcon>
                                    </div>
                                </div>

                                <div className="relative h-full flex-1">
                                    {step.content_type === 'code' ? (
                                        <div className="flex flex-col gap-2 h-full">
                                            <input
                                                type="text"
                                                value={step.code_language || ''}
                                                onChange={(e) => onUpdateCodeLanguage(e.target.value)}
                                                onClick={(e) => e.stopPropagation()}
                                                className="w-full bg-zinc-900 border border-white/10 rounded-lg px-3 py-2 text-xs text-zinc-300 focus:border-white focus:outline-none placeholder-zinc-600"
                                                placeholder="Linguagem (ex: python, javascript)"
                                            />
                                            <textarea
                                                value={step.code_content || ''}
                                                onChange={(e) => onUpdateCodeContent(e.target.value)}
                                                onClick={(e) => e.stopPropagation()}
                                                onFocus={(e) => e.stopPropagation()}
                                                onMouseDown={(e) => e.stopPropagation()}
                                                className="w-full h-[calc(100%-2.5rem)] bg-zinc-950 border border-white/10 rounded-lg p-4 text-sm font-mono text-zinc-300 focus:border-white focus:ring-0 focus:outline-none resize-none transition-all"
                                                placeholder="Cole seu código aqui..."
                                                spellCheck={false}
                                            />
                                        </div>
                                    ) : (
                                        <>
                                            <textarea
                                                value={step.description}
                                                onChange={(e) => onUpdateDescription(e.target.value)}
                                                onClick={(e) => e.stopPropagation()}
                                                onFocus={(e) => e.stopPropagation()}
                                                onMouseDown={(e) => e.stopPropagation()}
                                                disabled={step.isRefining}
                                                className={`w-full h-full min-h-[100px] bg-zinc-900 border border-white/10 rounded-lg p-4 text-sm text-zinc-300 focus:border-white focus:ring-0 focus:outline-none resize-none transition-all hover:bg-zinc-800 ${step.isRefining ? 'opacity-50 cursor-wait' : ''
                                                    }`}
                                                placeholder={step.isRefining ? "Analisando imagem..." : "Digite a descrição do passo..."}
                                            />
                                            <Edit3 size={14} className="absolute right-4 top-4 text-zinc-600 pointer-events-none" />
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Insert Step Button */}
            <div className="flex items-center justify-center -my-3 relative z-10">
                <button
                    onClick={onInsertStep}
                    className="group/insert flex items-center gap-2 px-4 py-2 bg-zinc-900/50 hover:bg-zinc-800 border border-white/5 hover:border-white/20 rounded-full text-zinc-600 hover:text-white transition-all duration-200 opacity-0 hover:opacity-100 focus:opacity-100"
                    title="Inserir passo"
                >
                    <Plus size={16} />
                    <span className="text-xs font-medium">Adicionar Passo</span>
                </button>
            </div>
        </>
    );
};
