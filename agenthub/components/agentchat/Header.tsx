import React from 'react';

import { Switch, useMantineTheme } from '@mantine/core';
import { Sun, Moon, Hash } from 'lucide-react';

export interface HeaderProps {
    darkMode: boolean;
    setDarkMode: (value: boolean) => void;
    title: string;
}

export const Header: React.FC<HeaderProps> = ({ darkMode, setDarkMode, title }) => {
    const theme = useMantineTheme();
    return (
      <div className={`flex justify-between items-center p-3 border-b ${darkMode ? 'bg-gray-900 text-white border-gray-800' : 'bg-white text-black border-gray-200'}`}>
        <div className="flex items-center space-x-2">
          <Hash size={20} className="text-gray-500" />
          <h1 className="text-lg font-medium">{title}</h1>
        </div>
        <div className="flex items-center space-x-2">
          <Sun size={16} className={darkMode ? 'text-gray-400' : 'text-yellow-500'} />
          <Switch
            checked={darkMode}
            onChange={(event) => setDarkMode(event.currentTarget.checked)}
            size="sm"
            color={theme.primaryColor}
          />
          <Moon size={16} className={darkMode ? 'text-blue-400' : 'text-gray-400'} />
        </div>
      </div>
    );
  };
