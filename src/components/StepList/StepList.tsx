import React from 'react';
import { Eye } from 'lucide-react';
import { Step } from '../../types';
import { StepItem } from './StepItem';

interface StepListProps {
    steps: Step[];
    selectedStepId: string | null;
    onSelectStep: (id: string | null) => void;
    onDeleteStep: (id: string) => void;
    onUpdateStepName: (id: string, name: string) => void;
    onUpdateStepDescription: (id: string, desc: string) => void;
    onUpdateStepContentType: (id: string, type: 'text' | 'code') => void;
    onUpdateStepCodeLanguage: (id: string, lang: string) => void;
    onUpdateStepCodeContent: (id: string, content: string) => void;
    onInsertStep: (index: number) => void;
    onZoomImage: (img: string) => void;
}

export const StepList: React.FC<StepListProps> = ({
    steps,
    selectedStepId,
    onSelectStep,
    onDeleteStep,
    onUpdateStepName,
    onUpdateStepDescription,
    onUpdateStepContentType,
    onUpdateStepCodeLanguage,
    onUpdateStepCodeContent,
    onInsertStep,
    onZoomImage
}) => {
    if (steps.length === 0) {
        return (
            <div className="h-full flex flex-col items-center justify-center text-zinc-600 space-y-6">
                <div className="w-24 h-24 rounded-3xl bg-zinc-900/50 border border-white/5 flex items-center justify-center">
                    <Eye size={48} className="text-zinc-700" />
                </div>
                <div className="text-center space-y-2">
                    <p className="text-lg font-medium text-zinc-400">Nenhuma ação registrada</p>
                    <p className="text-sm text-zinc-600">Inicie a gravação para começar a capturar seu tutorial.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 overflow-y-auto p-8 space-y-6 scroll-smooth custom-scrollbar bg-zinc-950">
            {steps.map((step, index) => (
                <StepItem
                    key={step.id}
                    step={step}
                    index={index}
                    isSelected={selectedStepId === step.id}
                    onSelect={() => onSelectStep(step.id)}
                    onDelete={() => onDeleteStep(step.id)}
                    onUpdateName={(name) => onUpdateStepName(step.id, name)}
                    onUpdateDescription={(desc) => onUpdateStepDescription(step.id, desc)}
                    onUpdateContentType={(type) => onUpdateStepContentType(step.id, type)}
                    onUpdateCodeLanguage={(lang) => onUpdateStepCodeLanguage(step.id, lang)}
                    onUpdateCodeContent={(content) => onUpdateStepCodeContent(step.id, content)}
                    onInsertStep={() => onInsertStep(index)}
                    onZoomImage={onZoomImage}
                />
            ))}
        </div>
    );
};
