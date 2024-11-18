export interface DatasetItem {
    title: string
    tableType: 'viewer' | 'preview'
    dateTime: string
    timeTitle: string
    date: string
    downloads: string
    favorites: string
}

export type DatasetsTabItem = 'Recommended' | 'Writing' | 'Entertainment' | 'Programming' | 'Tasks' | 'Sizes' | 'Sub-tasks' | 'Languages' | 'Licenses' | 'Other' | 'Academic' | 'Creative' | 'Lifestyle' | 'Entertainment';

export type AgentTabItem = 'Tasks' | 'Sizes' | 'Sub-tasks' | 'Languages' | 'Licenses' | 'Other' | 'Academic' | 'Creative' | 'Lifestyle' | 'Entertainment';


export interface AgentItem {
    id: string;
    author: string;
    name: string;
    version: string;
    description: string;
    createdAt: string;
    numDownloads: number;
    numFavorites: number;
}