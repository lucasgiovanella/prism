export interface Step {
    id: string;
    element_name: string;
    description: string;
    screenshot_base64: string;
    bounding_box: any;
    element_type: string;
    is_manual?: boolean;
    isRefining?: boolean;
    content_type?: 'text' | 'code';
    code_language?: string;
    code_content?: string;
}

export interface SavedTutorial {
    id: string;
    title: string;
    date_created: string;
    date_modified: string;
}

export interface TutorialData {
    title: string;
    steps: Step[];
}
