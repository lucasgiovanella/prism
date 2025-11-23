import { useState, useEffect } from 'react';
import { SavedTutorial, Step } from '../types';
import { api } from '../services/api';

export function useTutorials() {
    const [savedTutorials, setSavedTutorials] = useState<SavedTutorial[]>([]);
    const [currentTutorialId, setCurrentTutorialId] = useState<string | null>(null);

    const loadRecentTutorials = async () => {
        try {
            const tutorials = await api.getTutorials();
            setSavedTutorials(tutorials);
        } catch (error) {
            console.error('Failed to load tutorials:', error);
        }
    };

    useEffect(() => {
        loadRecentTutorials();
    }, []);

    const saveTutorial = async (title: string, steps: Step[]) => {
        try {
            const data = {
                title,
                steps: steps.map(s => ({
                    ...s,
                    screenshot_base64: s.is_manual ? '' : s.screenshot_base64
                }))
            };

            const id = await api.saveTutorial(data, currentTutorialId || undefined);
            setCurrentTutorialId(id);
            loadRecentTutorials();
            return true;
        } catch (error) {
            console.error('Failed to save tutorial:', error);
            return false;
        }
    };

    const deleteTutorial = async (id: string) => {
        try {
            await api.deleteTutorial(id);
            loadRecentTutorials();
            if (currentTutorialId === id) {
                setCurrentTutorialId(null);
                return true; // Indicates current tutorial was deleted
            }
            return false;
        } catch (error) {
            console.error('Failed to delete tutorial:', error);
            return false;
        }
    };

    const loadTutorial = async (id: string) => {
        try {
            const tutorial = await api.getTutorial(id);
            setCurrentTutorialId(id);
            return tutorial;
        } catch (error) {
            console.error('Failed to load tutorial:', error);
            return null;
        }
    };

    return {
        savedTutorials,
        currentTutorialId,
        setCurrentTutorialId,
        loadRecentTutorials,
        saveTutorial,
        deleteTutorial,
        loadTutorial
    };
}
