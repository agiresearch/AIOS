export interface DatasetItem {
    title: string
    tableType: 'viewer' | 'preview'
    dateTime: string
    timeTitle: string
    date: string
    downloads: string
    favorites: string
}

export type DatasetsTabItem = 'Tasks' | 'Sizes' | 'Sub-tasks' | 'Languages' | 'Licenses' | 'Other'


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