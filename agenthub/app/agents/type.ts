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