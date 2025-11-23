import { useState, useRef, useEffect } from 'react';
import { Step } from '../types';
import { api } from '../services/api';

export function useRecording() {
    const [isRecording, setIsRecording] = useState(false);
    const [steps, setSteps] = useState<Step[]>([]);
    const eventSourceRef = useRef<EventSource | null>(null);

    const toggleRecording = async () => {
        if (isRecording) {
            try {
                await api.stopRecording();
                setIsRecording(false);
                if (eventSourceRef.current) {
                    eventSourceRef.current.close();
                    eventSourceRef.current = null;
                }
            } catch (e) {
                console.error(e);
            }
        } else {
            try {
                await api.startRecording();
                setIsRecording(true);

                eventSourceRef.current = new EventSource(`${api.url}/events`);
                eventSourceRef.current.onmessage = async (event) => {
                    const newStep: Step = JSON.parse(event.data);

                    const isGeneric =
                        newStep.description.includes("Clicar no destaque") ||
                        newStep.description.includes("Interface Visual") ||
                        newStep.element_type === "VisualElement";

                    if (isGeneric && newStep.screenshot_base64) {
                        newStep.isRefining = true;
                        setSteps((prev) => [...prev, newStep]);

                        try {
                            const refinedStep = await api.processStep(newStep);
                            setSteps((prev) =>
                                prev.map((s) => s.id === newStep.id ? refinedStep : s)
                            );
                        } catch (error) {
                            console.error('[Refinement] Error:', error);
                            setSteps((prev) =>
                                prev.map((s) => s.id === newStep.id ? { ...s, isRefining: false } : s)
                            );
                        }
                    } else {
                        setSteps((prev) => [...prev, newStep]);
                    }
                };
            } catch (e) {
                console.error(e);
            }
        }
    };

    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
        };
    }, []);

    return {
        isRecording,
        steps,
        setSteps,
        toggleRecording
    };
}
