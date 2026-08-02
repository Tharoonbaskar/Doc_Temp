import React, { createContext, useState, useMemo, useContext } from 'react';

export type SelectionType =
  | 'PAGE'
  | 'PARAGRAPH'
  | 'FIELD'
  | 'TABLE'
  | 'IMAGE'
  | 'LOGO'
  | 'HEADER'
  | 'FOOTER'
  | 'SIGNATURE'
  | 'LINE'
  | 'RECTANGLE'
  | 'BARCODE'
  | 'QR'
  | null;

interface SelectionContextProps {
  selectedId: string | null;
  setSelectedId: (id: string | null) => void;
  selectedType: SelectionType;
  setSelectedType: (type: SelectionType) => void;
  selectedPage: number | null;
  setSelectedPage: (page: number | null) => void;
  editingMode: boolean;
  setEditingMode: (mode: boolean) => void;
  selectionMode: boolean;
  setSelectionMode: (mode: boolean) => void;
}

const SelectionContext = createContext<SelectionContextProps | undefined>(undefined);

export const SelectionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<SelectionType>('PAGE');
  const [selectedPage, setSelectedPage] = useState<number | null>(1);
  const [editingMode, setEditingMode] = useState<boolean>(false);
  const [selectionMode, setSelectionMode] = useState<boolean>(false);

  const value = useMemo(() => ({
    selectedId,
    setSelectedId,
    selectedType,
    setSelectedType,
    selectedPage,
    setSelectedPage,
    editingMode,
    setEditingMode,
    selectionMode,
    setSelectionMode,
  }), [selectedId, selectedType, selectedPage, editingMode, selectionMode]);

  return (
    <SelectionContext.Provider value={value}>
      {children}
    </SelectionContext.Provider>
  );
};

export const useSelection = () => {
  const context = useContext(SelectionContext);
  if (context === undefined) {
    throw new Error('useSelection must be used within a SelectionProvider');
  }
  return context;
};
