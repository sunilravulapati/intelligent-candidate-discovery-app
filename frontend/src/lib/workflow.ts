"use client";

import { useState, useEffect } from "react";

export type WorkflowAction = "saved" | "shortlisted" | "rejected";

export interface WorkflowRecord {
  status: WorkflowAction;
  timestamp: number;
  history?: { action: WorkflowAction; timestamp: number }[];
}

export type CandidateWorkflowState = Record<string, WorkflowRecord>;

const CANDIDATE_WORKFLOW_KEY = "talentlens.discovery.candidateWorkflow.v2";

function getInitialState(): CandidateWorkflowState {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(CANDIDATE_WORKFLOW_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

export function useCandidateWorkflow() {
  const [workflowState, setWorkflowState] = useState<CandidateWorkflowState>(getInitialState);

  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === CANDIDATE_WORKFLOW_KEY) {
        setWorkflowState(getInitialState());
      }
    };
    const handleLocalSync = () => {
      setWorkflowState(getInitialState());
    };

    window.addEventListener("storage", handleStorageChange);
    window.addEventListener("workflow-sync", handleLocalSync);
    return () => {
      window.removeEventListener("storage", handleStorageChange);
      window.removeEventListener("workflow-sync", handleLocalSync);
    };
  }, []);

  const setWorkflowStatus = (candidateId: string, status: WorkflowAction | null) => {
    setWorkflowState((current) => {
      const next = { ...current };
      if (status === null || next[candidateId]?.status === status) {
        delete next[candidateId];
      } else {
        const now = Date.now();
        const prev = next[candidateId];
        const history = prev?.history ? [...prev.history] : prev ? [{ action: prev.status, timestamp: prev.timestamp }] : [];
        history.push({ action: status, timestamp: now });
        next[candidateId] = { status, timestamp: now, history };
      }
      if (typeof window !== "undefined") {
        window.localStorage.setItem(CANDIDATE_WORKFLOW_KEY, JSON.stringify(next));
        window.dispatchEvent(new Event("workflow-sync"));
      }
      return next;
    });
  };

  return { workflowState, setWorkflowStatus };
}
