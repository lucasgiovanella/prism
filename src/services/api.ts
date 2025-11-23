import { Step, SavedTutorial, TutorialData } from '../types';

const API_URL = 'http://localhost:8000';

export const api = {
    url: API_URL,

    async checkHealth(): Promise<boolean> {
        try {
            const response = await fetch(`${API_URL}/health`);
            return response.ok;
        } catch {
            return false;
        }
    },

    async startRecording(): Promise<void> {
        await fetch(`${API_URL}/start-recording`, { method: 'POST' });
    },

    async stopRecording(): Promise<void> {
        await fetch(`${API_URL}/stop-recording`, { method: 'POST' });
    },

    async processStep(step: Step): Promise<Step> {
        const response = await fetch(`${API_URL}/process-step`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image_base64: step.screenshot_base64,
                bounding_box: step.bounding_box,
                context: step.description
            })
        });

        if (response.ok) {
            const result = await response.json();
            return { ...step, description: result.final_description, isRefining: false };
        }
        throw new Error('Failed to process step');
    },

    async getTutorials(): Promise<SavedTutorial[]> {
        const response = await fetch(`${API_URL}/tutorials`);
        if (response.ok) {
            const data = await response.json();
            return data.tutorials || [];
        }
        return [];
    },

    async getTutorial(id: string): Promise<TutorialData> {
        const response = await fetch(`${API_URL}/tutorials/${id}`);
        if (response.ok) {
            return await response.json();
        }
        throw new Error('Failed to load tutorial');
    },

    async saveTutorial(data: TutorialData, id?: string): Promise<string> {
        if (id) {
            await fetch(`${API_URL}/tutorials/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return id;
        } else {
            const response = await fetch(`${API_URL}/tutorials`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            return result.id;
        }
    },

    async deleteTutorial(id: string): Promise<void> {
        await fetch(`${API_URL}/tutorials/${id}`, {
            method: 'DELETE'
        });
    }
};
