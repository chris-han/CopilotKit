"use client";

import React, { createContext, useContext, useState, useCallback, useMemo, type ReactNode } from "react";
import type { Dashboard } from "../types/dashboard";

type DashboardContextType = {
  mode: "edit" | "view";
  activeSection: "dashboard-title" | "dashboard-preview" | "item-properties" | null;
  selectedItemId: string | null;
  dashboard: Dashboard | null;
  isDynamicDashboard: boolean;
  hasChanges: boolean;
  saving: boolean;
  setMode: (mode: "edit" | "view") => void;
  setActiveSection: (section: "dashboard-title" | "dashboard-preview" | "item-properties" | null) => void;
  setSelectedItemId: (itemId: string | null) => void;
  setDashboard: (dashboard: Dashboard | null) => void;
  setIsDynamicDashboard: (isDynamic: boolean) => void;
  setOnDashboardChange: (handler: (dashboard: Dashboard) => void) => void;
  setOnItemSelect: (handler: (itemId: string) => void) => void;
  setOnSave: (handler: () => Promise<void>) => void;
  setOnReset: (handler: () => void) => void;
  setOnNameChange: (handler: (name: string) => void) => void;
  setOnDescriptionChange: (handler: (description: string) => void) => void;
  setHasChanges: (hasChanges: boolean) => void;
  setSaving: (saving: boolean) => void;
  onDashboardChange?: (dashboard: Dashboard) => void;
  onItemSelect?: (itemId: string) => void;
  onSave?: () => Promise<void>;
  onReset?: () => void;
  onNameChange?: (name: string) => void;
  onDescriptionChange?: (description: string) => void;
};

const DashboardContext = createContext<DashboardContextType | null>(null);

type DashboardContextProviderProps = {
  children: ReactNode;
};

export function DashboardContextProvider({ children }: DashboardContextProviderProps) {
  const [mode, setMode] = useState<"edit" | "view">("view");
  const [activeSection, setActiveSection] = useState<"dashboard-title" | "dashboard-preview" | "item-properties" | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [isDynamicDashboard, setIsDynamicDashboard] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [saving, setSaving] = useState(false);
  const [onDashboardChange, setOnDashboardChangeInternal] = useState<((dashboard: Dashboard) => void) | undefined>();
  const [onItemSelect, setOnItemSelectInternal] = useState<((itemId: string) => void) | undefined>();
  const [onSave, setOnSaveInternal] = useState<(() => Promise<void>) | undefined>();
  const [onReset, setOnResetInternal] = useState<(() => void) | undefined>();
  const [onNameChange, setOnNameChangeInternal] = useState<((name: string) => void) | undefined>();
  const [onDescriptionChange, setOnDescriptionChangeInternal] = useState<((description: string) => void) | undefined>();

  const setOnDashboardChange = useCallback((handler: (dashboard: Dashboard) => void) => {
    setOnDashboardChangeInternal(() => handler);
  }, []);

  const setOnItemSelect = useCallback((handler: (itemId: string) => void) => {
    setOnItemSelectInternal(() => handler);
  }, []);

  const setOnSave = useCallback((handler: () => Promise<void>) => {
    setOnSaveInternal(() => handler);
  }, []);

  const setOnReset = useCallback((handler: () => void) => {
    setOnResetInternal(() => handler);
  }, []);

  const setOnNameChange = useCallback((handler: (name: string) => void) => {
    setOnNameChangeInternal(() => handler);
  }, []);

  const setOnDescriptionChange = useCallback((handler: (description: string) => void) => {
    setOnDescriptionChangeInternal(() => handler);
  }, []);

  const contextValue: DashboardContextType = useMemo(() => ({
    mode,
    activeSection,
    selectedItemId,
    dashboard,
    isDynamicDashboard,
    hasChanges,
    saving,
    setMode,
    setActiveSection,
    setSelectedItemId,
    setDashboard,
    setIsDynamicDashboard,
    setOnDashboardChange,
    setOnItemSelect,
    setOnSave,
    setOnReset,
    setOnNameChange,
    setOnDescriptionChange,
    setHasChanges,
    setSaving,
    onDashboardChange,
    onItemSelect,
    onSave,
    onReset,
    onNameChange,
    onDescriptionChange,
  }), [
    mode,
    activeSection,
    selectedItemId,
    dashboard,
    isDynamicDashboard,
    hasChanges,
    saving,
    setOnDashboardChange,
    setOnItemSelect,
    setOnSave,
    setOnReset,
    setOnNameChange,
    setOnDescriptionChange,
    onDashboardChange,
    onItemSelect,
    onSave,
    onReset,
    onNameChange,
    onDescriptionChange,
  ]);

  return (
    <DashboardContext.Provider value={contextValue}>
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboardContext() {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error("useDashboardContext must be used within a DashboardContextProvider");
  }
  return context;
}

// Helper function to set dashboard change handlers
export function useDashboardContextActions() {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error("useDashboardContextActions must be used within a DashboardContextProvider");
  }

  const setDashboardChangeHandler = (handler: (dashboard: Dashboard) => void) => {
    (context as any).setOnDashboardChange(() => handler);
  };

  const setItemSelectHandler = (handler: (itemId: string) => void) => {
    (context as any).setOnItemSelect(() => handler);
  };

  return {
    setDashboardChangeHandler,
    setItemSelectHandler,
  };
}